#!/usr/bin/env python3
"""Report how many manifest paths are not NFC-normalised, and whether
normalising them would make two distinct entries collide.

Run this before fix_paths.py. Changes nothing.

Usage:  python3 check_collisions.py [BACKUP_DIR]
"""
import collections
import sqlite3
import sys
import tempfile
import unicodedata
from pathlib import Path

from ios_backup import choose_backup, decrypt_manifest, unlock

backup = choose_backup(sys.argv)
print(f"Backup: {backup.name}\n")
manifest, key = unlock(backup)

with tempfile.TemporaryDirectory() as tmp:
    db = decrypt_manifest(backup, key, Path(tmp) / "Manifest.db")
    con = sqlite3.connect(db)
    rows = con.execute("SELECT fileID, domain, relativePath, flags FROM Files").fetchall()
    con.close()

paths_before = {(d, r) for _, d, r, _ in rows if r}
after = collections.defaultdict(list)
for file_id, domain, rel, flags in rows:
    if rel:
        after[(domain, unicodedata.normalize("NFC", rel))].append((file_id, rel, flags))

collisions = {k: v for k, v in after.items() if len(v) > 1}
denormalised = sum(1 for _, _, r, _ in rows if r and not unicodedata.is_normalized("NFC", r))

print("=" * 62)
print(f"  Manifest entries:            {len(rows):>10,}")
print(f"  Not NFC-normalised:          {denormalised:>10,}")
print(f"  Distinct paths before:       {len(paths_before):>10,}")
print(f"  Distinct paths after NFC:    {len(after):>10,}")
print(f"  COLLISIONS:                  {len(collisions):>10,}")
print("=" * 62)

if collisions:
    print("\nColliding paths (examples):")
    for (domain, rel), entries in list(collisions.items())[:10]:
        print(f"\n  target: {domain} / {rel}")
        for file_id, original, flags in entries:
            form = "NFC" if unicodedata.is_normalized("NFC", original) else "NFD"
            kind = {1: "file", 2: "dir", 4: "link"}.get(flags, str(flags))
            print(f"     {file_id}  [{form}/{kind}]")
    print("\n  ==> DO NOT normalise: entries would overwrite each other.")
elif denormalised:
    print("\n  ==> Safe to normalise. Run fix_paths.py next.")
else:
    print("\n  ==> All paths already NFC. This backup is not affected.")
