#!/usr/bin/env python3
"""Verify that every file the manifest lists is actually present on disk.

Answers the question "is my backup complete?" without restoring it. Note that a
sizeable number of zero-byte entries is normal -- empty files exist on iOS too --
so the meaningful signal is 'expected content but found empty', not 'is empty'.

Usage:  python3 check_integrity.py [BACKUP_DIR]
"""
import collections
import plistlib
import sqlite3
import sys
import tempfile
from pathlib import Path

from ios_backup import choose_backup, decrypt_manifest, unlock

backup = choose_backup(sys.argv)
print(f"Backup: {backup.name}\n")
manifest, key = unlock(backup)

with tempfile.TemporaryDirectory() as tmp:
    db = decrypt_manifest(backup, key, Path(tmp) / "Manifest.db")
    con = sqlite3.connect(db)
    rows = con.execute("SELECT fileID, domain, relativePath, flags, file FROM Files").fetchall()
    con.close()

    stat = collections.Counter()
    missing, truncated = [], []
    expected_bytes = actual_bytes = 0

    for file_id, domain, rel, flags, blob in rows:
        if flags != 1:                      # 2 = directory, 4 = symlink
            stat["directories_and_links"] += 1
            continue
        stat["files"] += 1

        size = 0
        try:
            for obj in plistlib.loads(blob).get("$objects", []):
                if isinstance(obj, dict) and "Size" in obj:
                    size = obj["Size"]
                    break
        except Exception:
            stat["unreadable_metadata"] += 1
        expected_bytes += size

        blob_path = backup / file_id[:2] / file_id
        if not blob_path.exists():
            stat["blob_missing"] += 1
            if len(missing) < 5:
                missing.append(rel)
            continue

        on_disk = blob_path.stat().st_size
        actual_bytes += on_disk
        if size > 0 and on_disk == 0:
            stat["empty_but_should_have_content"] += 1
            if len(truncated) < 5:
                truncated.append(rel)
        elif size == 0:
            stat["legitimately_empty"] += 1
        else:
            stat["ok"] += 1

print("=" * 62)
for name, count in stat.most_common():
    print(f"  {name:<34} {count:>10,}")
print("=" * 62)
print(f"  Expected payload:  {expected_bytes / 2**30:>8.1f} GB")
print(f"  Found on disk:     {actual_bytes / 2**30:>8.1f} GB")
print("=" * 62)

for label, items in (("MISSING", missing), ("TRUNCATED", truncated)):
    if items:
        print(f"\n{label} (examples):")
        for rel in items:
            print(f"  {rel}")

broken = stat["blob_missing"] + stat["empty_but_should_have_content"]
print(f"\n  ==> {'BACKUP IS COMPLETE.' if not broken else f'INCOMPLETE: {broken:,} broken files.'}")
