"""Backup keybag parsing and key derivation.

An iOS backup keybag is a flat sequence of TLV records: a four-character ASCII
tag, a big-endian length, then the value. Records before the first CLAS tag are
keybag-wide; each CLAS starts a protection class whose WPKY holds the wrapped
class key.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, field

from cryptography.hazmat.primitives.keywrap import aes_key_unwrap


@dataclass
class Keybag:
    attrs: dict[str, bytes] = field(default_factory=dict)
    classes: list[dict] = field(default_factory=list)

    @classmethod
    def parse(cls, blob: bytes) -> "Keybag":
        kb, offset, current = cls(), 0, None
        while offset + 8 <= len(blob):
            tag = blob[offset:offset + 4].decode("ascii", "replace")
            length = struct.unpack(">I", blob[offset + 4:offset + 8])[0]
            value = blob[offset + 8:offset + 8 + length]
            offset += 8 + length
            if tag == "CLAS":
                if current:
                    kb.classes.append(current)
                current = {"CLAS": int.from_bytes(value, "big")}
            elif current is not None and tag in ("WRAP", "WPKY", "KTYP", "PBKY"):
                current[tag] = value
            else:
                kb.attrs[tag] = value
        if current:
            kb.classes.append(current)
        return kb

    def num(self, tag: str) -> int | None:
        raw = self.attrs.get(tag)
        return int.from_bytes(raw, "big") if raw else None

    def structurally_intact(self) -> bool:
        """Every class must carry a 40-byte wrapped key."""
        return bool(self.classes) and all(
            len(c.get("WPKY", b"")) == 40 for c in self.classes)

    def derive(self, password: str) -> bytes:
        """Turn the backup password into the keybag-unwrapping key.

        iOS 10 and later chain two PBKDF2 rounds: SHA-256 over DPSL/DPIC first,
        then SHA-1 over SALT/ITER. Older backups use the SHA-1 round alone.
        """
        pw = password.encode("utf-8")
        salt, iterations = self.attrs["SALT"], self.num("ITER")
        if "DPSL" in self.attrs:
            stage1 = hashlib.pbkdf2_hmac(
                "sha256", pw, self.attrs["DPSL"], self.num("DPIC"), 32)
            return hashlib.pbkdf2_hmac("sha1", stage1, salt, iterations, 32)
        return hashlib.pbkdf2_hmac("sha1", pw, salt, iterations, 32)

    def unwrap_class_keys(self, key: bytes) -> dict[int, bytes]:
        """Unwrap every protection class key. Empty result means wrong password."""
        keys = {}
        for entry in self.classes:
            try:
                keys[entry["CLAS"]] = aes_key_unwrap(key, entry["WPKY"])
            except Exception:
                pass
        return keys
