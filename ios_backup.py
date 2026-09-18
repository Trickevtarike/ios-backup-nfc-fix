"""
Shared helpers for reading encrypted iOS backups (Finder / iTunes local backups).

Only metadata is touched: the keybag is parsed, the Manifest.db is decrypted so
that file paths can be inspected. No file contents are ever decrypted or copied.

The backup password never leaves the machine and is never written to disk.
"""
from __future__ import annotations

import getpass
import hashlib
import os
import plistlib
import struct
import sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.keywrap import aes_key_unwrap
except ImportError:
    sys.exit("Missing dependency. Install it with:  pip3 install cryptography")

BACKUP_ROOT = Path.home() / "Library/Application Support/MobileSync/Backup"


def find_backups(root: Path = BACKUP_ROOT) -> list[Path]:
    """Return every directory under *root* that looks like a device backup."""
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / "Manifest.plist").is_file())


def choose_backup(argv: list[str]) -> Path:
    """Resolve a backup directory from argv[1], or ask the user to pick one.

    Exits with a readable message when the folder cannot be used -- most often
    because Terminal lacks Full Disk Access, which makes the backup folder look
    empty instead of raising a permission error.
    """
    if len(argv) > 1:
        path = Path(argv[1]).expanduser()
        if not (path / "Manifest.plist").is_file():
            sys.exit(f"Not a backup directory (no Manifest.plist): {path}")
        return path

    backups = find_backups()
    if not backups:
        sys.exit(
            f"No backups found in {BACKUP_ROOT}\n\n"
            "If you know backups exist there, your terminal is probably missing\n"
            "Full Disk Access. Grant it under System Settings > Privacy & Security >\n"
            "Full Disk Access, then restart the terminal and try again."
        )
    if len(backups) == 1:
        return backups[0]

    print("Multiple backups found:\n")
    for i, b in enumerate(backups, 1):
        date = "?"
        try:
            status = plistlib.loads((b / "Status.plist").read_bytes())
            date = str(status.get("Date", "?"))
        except Exception:
            pass
        print(f"  [{i}] {b.name}   {date}")
    try:
        pick = int(input("\nSelect backup: "))
        return backups[pick - 1]
    except (ValueError, IndexError):
        sys.exit("Invalid selection.")


def parse_keybag(blob: bytes) -> tuple[dict, list[dict]]:
    """Split a BackupKeyBag into its top-level TLV fields and per-class entries."""
    offset, top, classes, current = 0, {}, [], None
    while offset + 8 <= len(blob):
        tag = blob[offset:offset + 4].decode("ascii", "replace")
        length = struct.unpack(">I", blob[offset + 4:offset + 8])[0]
        value = blob[offset + 8:offset + 8 + length]
        offset += 8 + length
        if tag == "CLAS":
            if current:
                classes.append(current)
            current = {"CLAS": int.from_bytes(value, "big")}
        elif current is not None and tag in ("WRAP", "WPKY"):
            current[tag] = value
        else:
            top[tag] = value
    if current:
        classes.append(current)
    return top, classes


def unlock(backup: Path, password: str | None = None) -> tuple[dict, bytes]:
    """Derive the class keys for *backup* and return (manifest_plist, manifest_key).

    Raises SystemExit when the password does not match the keybag.
    """
    manifest = plistlib.loads((backup / "Manifest.plist").read_bytes())
    if not manifest.get("IsEncrypted"):
        sys.exit("This backup is not encrypted; these tools target encrypted backups.")

    top, classes = parse_keybag(manifest["BackupKeyBag"])
    if password is None:
        password = getpass.getpass("Backup password: ")
    pw = password.encode("utf-8")

    # iOS 10 and later: PBKDF2-SHA256 first, then PBKDF2-SHA1 over the result.
    print("Deriving key (this takes a few seconds) ...", flush=True)
    if "DPSL" in top:
        stage1 = hashlib.pbkdf2_hmac("sha256", pw, top["DPSL"],
                                     int.from_bytes(top["DPIC"], "big"), 32)
        key = hashlib.pbkdf2_hmac("sha1", stage1, top["SALT"],
                                  int.from_bytes(top["ITER"], "big"), 32)
    else:
        key = hashlib.pbkdf2_hmac("sha1", pw, top["SALT"],
                                  int.from_bytes(top["ITER"], "big"), 32)

    class_keys = {}
    for entry in classes:
        try:
            class_keys[entry["CLAS"]] = aes_key_unwrap(key, entry["WPKY"])
        except Exception:
            pass
    if not class_keys:
        sys.exit("Wrong password: no class key could be unwrapped.")

    wrapped = manifest["ManifestKey"]
    protection_class = struct.unpack("<L", wrapped[:4])[0] & 0xFFFF
    if protection_class not in class_keys:
        sys.exit("Manifest key references a protection class that could not be unwrapped.")
    manifest_key = aes_key_unwrap(class_keys[protection_class], wrapped[4:])
    print(f"Unlocked ({len(class_keys)} class keys).")
    return manifest, manifest_key


def decrypt_manifest(backup: Path, manifest_key: bytes, dest: Path) -> Path:
    """Decrypt Manifest.db into *dest* and verify it is valid SQLite."""
    data = (backup / "Manifest.db").read_bytes()
    decryptor = Cipher(algorithms.AES(manifest_key), modes.CBC(b"\x00" * 16)).decryptor()
    plain = decryptor.update(data) + decryptor.finalize()
    if plain[:15] != b"SQLite format 3":
        sys.exit("Decryption produced invalid SQLite data -- wrong key?")
    dest.write_bytes(plain)
    return dest


def encrypt_manifest(plain_path: Path, manifest_key: bytes) -> bytes:
    """Encrypt a plaintext Manifest.db back into backup format."""
    data = plain_path.read_bytes()
    if len(data) % 16:
        data += b"\x00" * (16 - len(data) % 16)
    encryptor = Cipher(algorithms.AES(manifest_key), modes.CBC(b"\x00" * 16)).encryptor()
    return encryptor.update(data) + encryptor.finalize()
