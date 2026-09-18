"""Locating, unlocking and reading local iOS backups."""
from __future__ import annotations

import plistlib
import shutil
import sqlite3
import struct
import tempfile
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.keywrap import aes_key_unwrap

from .keybag import Keybag

BACKUP_ROOT = Path.home() / "Library/Application Support/MobileSync/Backup"


class BackupError(Exception):
    """Anything that stops us from reading a backup, phrased for the user."""


@dataclass
class FileEntry:
    file_id: str
    domain: str
    relative_path: str
    flags: int          # 1 file, 2 directory, 4 symlink
    size: int

    @property
    def is_file(self) -> bool:
        return self.flags == 1

    @property
    def is_denormalised(self) -> bool:
        return bool(self.relative_path) and not unicodedata.is_normalized(
            "NFC", self.relative_path)

    def normalised(self) -> str:
        return unicodedata.normalize("NFC", self.relative_path)


def discover(root: Path = BACKUP_ROOT) -> list[Path]:
    """Every directory under *root* that carries a Manifest.plist."""
    if not root.is_dir():
        return []
    try:
        return sorted(p for p in root.iterdir()
                      if p.is_dir() and (p / "Manifest.plist").is_file())
    except PermissionError:
        raise BackupError(
            f"macOS denied access to {root}\n\n"
            "Grant your terminal Full Disk Access under System Settings >\n"
            "Privacy & Security > Full Disk Access, then restart it."
        )


def describe(path: Path) -> dict:
    """Cheap summary for listings: date, device, encryption, completeness."""
    info: dict = {"name": path.name, "path": path}
    try:
        status = plistlib.loads((path / "Status.plist").read_bytes())
        info["date"] = status.get("Date")
        info["complete"] = status.get("SnapshotState") == "finished"
    except Exception:
        info["date"], info["complete"] = None, False
    try:
        meta = plistlib.loads((path / "Info.plist").read_bytes())
        info["device"] = meta.get("Product Name") or meta.get("Device Name")
        info["ios"] = meta.get("Product Version")
    except Exception:
        info["device"] = info["ios"] = None
    try:
        manifest = plistlib.loads((path / "Manifest.plist").read_bytes())
        info["encrypted"] = bool(manifest.get("IsEncrypted"))
    except Exception:
        info["encrypted"] = None
    return info


class Backup:
    """An encrypted local backup, unlocked with its password."""

    def __init__(self, path: Path):
        self.path = path
        try:
            self.manifest = plistlib.loads((path / "Manifest.plist").read_bytes())
        except FileNotFoundError:
            raise BackupError(f"Not a backup directory: {path}")
        self.keybag = Keybag.parse(self.manifest["BackupKeyBag"])
        self._manifest_key: bytes | None = None

    @property
    def encrypted(self) -> bool:
        return bool(self.manifest.get("IsEncrypted"))

    def unlock(self, password: str) -> None:
        """Derive the manifest key. Raises BackupError on a wrong password."""
        if not self.encrypted:
            raise BackupError("This backup is not encrypted; nothing to unlock.")
        class_keys = self.keybag.unwrap_class_keys(self.keybag.derive(password))
        if not class_keys:
            raise BackupError("Wrong password: no protection class key could be unwrapped.")
        self.class_keys = class_keys
        wrapped = self.manifest["ManifestKey"]
        protection_class = struct.unpack("<L", wrapped[:4])[0] & 0xFFFF
        if protection_class not in class_keys:
            raise BackupError("Manifest key belongs to an unavailable protection class.")
        self._manifest_key = aes_key_unwrap(class_keys[protection_class], wrapped[4:])

    @property
    def manifest_key(self) -> bytes:
        if self._manifest_key is None:
            raise BackupError("Backup is still locked -- call unlock() first.")
        return self._manifest_key

    def _decrypt_manifest(self, dest: Path) -> Path:
        data = (self.path / "Manifest.db").read_bytes()
        decryptor = Cipher(algorithms.AES(self.manifest_key),
                           modes.CBC(b"\x00" * 16)).decryptor()
        plain = decryptor.update(data) + decryptor.finalize()
        if plain[:15] != b"SQLite format 3":
            raise BackupError("Decrypted manifest is not valid SQLite -- wrong key?")
        dest.write_bytes(plain)
        return dest

    @contextmanager
    def manifest_db(self, writable: bool = False):
        """Yield a connection to the decrypted manifest.

        The plaintext copy lives in a temporary directory and is deleted on
        exit. With writable=True, changes are re-encrypted back into the backup
        and the untouched Manifest.db is preserved as Manifest.db.orig.
        """
        with tempfile.TemporaryDirectory(prefix="ios-backup-doctor-") as tmp:
            db_path = self._decrypt_manifest(Path(tmp) / "Manifest.db")
            con = sqlite3.connect(db_path)
            try:
                yield con
                if writable:
                    con.commit()
            finally:
                con.close()
            if writable:
                target = self.path / "Manifest.db"
                backup_copy = self.path / "Manifest.db.orig"
                if not backup_copy.exists():
                    shutil.copy2(target, backup_copy)
                data = db_path.read_bytes()
                if len(data) % 16:
                    data += b"\x00" * (16 - len(data) % 16)
                encryptor = Cipher(algorithms.AES(self.manifest_key),
                                   modes.CBC(b"\x00" * 16)).encryptor()
                target.write_bytes(encryptor.update(data) + encryptor.finalize())

    def entries(self, con: sqlite3.Connection) -> list[FileEntry]:
        rows = con.execute(
            "SELECT fileID, domain, relativePath, flags, file FROM Files").fetchall()
        return [FileEntry(fid, dom, rel or "", flags, _size_of(blob))
                for fid, dom, rel, flags, blob in rows]

    def blob_path(self, file_id: str) -> Path:
        return self.path / file_id[:2] / file_id


def _size_of(blob) -> int:
    """Read the Size field out of a manifest file record."""
    try:
        for obj in plistlib.loads(blob).get("$objects", []):
            if isinstance(obj, dict) and "Size" in obj:
                return obj["Size"]
    except Exception:
        pass
    return 0
