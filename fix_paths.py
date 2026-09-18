#!/usr/bin/env python3
"""Normalise decomposed (NFD) paths in an iOS backup manifest to NFC.

This is what makes an affected backup restorable. No file is removed and no
content is altered -- only the spelling of the paths changes. 'Cafe' + combining
accent becomes the single precomposed character; the name looks identical.

Always run check_collisions.py first. Manifest.db is backed up as
Manifest.db.orig before writing, so the change can be undone.

WORK ON A COPY of your backup, not your only one.

Usage:  python3 fix_paths.py [BACKUP_DIR]
"""
import collections
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
from pathlib import Path

from ios_backup import choose_backup, decrypt_manifest, encrypt_manifest, unlock

backup = choose_backup(sys.argv)
print(f"Backup: {backup.name}\n")
manifest, key = unlock(backup)

with tempfile.TemporaryDirectory() as tmp:
    db = decrypt_manifest(backup, key, Path(tmp) / "Manifest.db")
    con = sqlite3.connect(db)
    rows = con.execute("SELECT fileID, domain, relativePath, flags FROM Files").fetchall()

    todo = [(fid, rel, unicodedata.normalize("NFC", rel), flags)
            for fid, dom, rel, flags in rows
            if rel and not unicodedata.is_normalized("NFC", rel)]

    print("=" * 62)
    print(f"  Manifest entries:      {len(rows):>10,}")
    print(f"  Paths to normalise:    {len(todo):>10,}")
    print("=" * 62)

    if not todo:
        print("\nNothing to do -- this backup is not affected.")
        con.close()
        sys.exit(0)

    kinds = collections.Counter({1: "file", 2: "dir", 4: "link"}.get(f[3], str(f[3])) for f in todo)
    print("\nBy type:")
    for kind, count in kinds.most_common():
        print(f"  {count:>6,}  {kind}")

    print("\nExamples (the readable name does not change):")
    for _, old, new, _ in todo[:3]:
        print(f"  {old}")
        print(f"    -> {new}   ({len(old.encode())} -> {len(new.encode())} bytes)")

    if input(f"\nNormalise {len(todo):,} paths? [y/N] ").strip().lower() != "y":
        print("Aborted, nothing changed.")
        con.close()
        sys.exit(0)

    con.executemany("UPDATE Files SET relativePath=? WHERE fileID=?",
                    [(new, fid) for fid, _, new, _ in todo])
    con.commit()

    remaining = sum(1 for (r,) in con.execute(
        "SELECT relativePath FROM Files WHERE relativePath IS NOT NULL")
        if not unicodedata.is_normalized("NFC", r))
    total = con.execute("SELECT COUNT(*) FROM Files").fetchone()[0]
    con.close()

    print(f"\nDone. Entries: {total:,} (unchanged), still denormalised: {remaining}")
    if remaining:
        print("  WARNING: some paths could not be normalised.")

    target = backup / "Manifest.db"
    if not (backup / "Manifest.db.orig").exists():
        shutil.copy2(target, backup / "Manifest.db.orig")
        print("Original saved as Manifest.db.orig")
    target.write_bytes(encrypt_manifest(db, key))
    print("Manifest.db rewritten.\n")

print("Now restore, e.g. with libimobiledevice:\n")
print("  idevicebackup2 -u <DEVICE_UDID> -s " + backup.name + " \\")
print("    -i restore --system --settings \\")
print('    "$HOME/Library/Application Support/MobileSync/Backup"')
