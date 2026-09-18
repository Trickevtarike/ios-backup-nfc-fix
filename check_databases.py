#!/usr/bin/env python3
"""Report which core databases a backup contains, and how large they are.

Answers a question that comes up after every restore that looks incomplete:
were my messages and contacts in this backup at all, or did they live in iCloud?
Data synced through iCloud is not part of a local backup and only returns once
you sign in on the device -- an empty or near-empty database here is the giveaway.

Only sizes are read. No database is opened, no content is decrypted.

Usage:  python3 check_databases.py [BACKUP_DIR]
"""
import plistlib
import sqlite3
import sys
import tempfile
from pathlib import Path

from ios_backup import choose_backup, decrypt_manifest, unlock

# (label, substring matched against relativePath)
TARGETS = [
    ("Messages (SMS/iMessage)", "Library/SMS/sms.db"),
    ("Message attachments",     "Library/SMS/Attachments"),
    ("Contacts",                "Library/AddressBook/AddressBook.sqlitedb"),
    ("Contact images",          "Library/AddressBook/AddressBookImages.sqlitedb"),
    ("Call history",            "Library/CallHistoryDB/CallHistory.storedata"),
    ("Notes",                   "Library/Notes/notes.sqlite"),
    ("Notes (modern)",          "NoteStore.sqlite"),
    ("Calendar",                "Library/Calendar/Calendar.sqlitedb"),
    ("Photos database",         "Media/PhotoData/Photos.sqlite"),
    ("Voice memos",             "Recordings/"),
    ("Safari history",          "Library/Safari/History.db"),
    ("WhatsApp",                "ChatStorage.sqlite"),
    ("Health",                  "Health/healthdb.sqlite"),
]

ICLOUD_THRESHOLD = 200 * 1024  # below this, a database is effectively empty


def entry_size(blob) -> int:
    """Pull the Size field out of a manifest file record."""
    try:
        for obj in plistlib.loads(blob).get("$objects", []):
            if isinstance(obj, dict) and "Size" in obj:
                return obj["Size"]
    except Exception:
        pass
    return 0


def human(n: int) -> str:
    if n >= 2**30:
        return f"{n / 2**30:.2f} GB"
    if n >= 2**20:
        return f"{n / 2**20:.1f} MB"
    return f"{n / 1024:.0f} KB"


backup = choose_backup(sys.argv)
print(f"Backup: {backup.name}\n")
manifest, key = unlock(backup)

with tempfile.TemporaryDirectory() as tmp:
    db = decrypt_manifest(backup, key, Path(tmp) / "Manifest.db")
    con = sqlite3.connect(db)

    print("\n" + "=" * 72)
    print(f"  {'DATABASE':<26} {'SIZE':>12}   STATUS")
    print("=" * 72)

    for label, needle in TARGETS:
        rows = con.execute(
            "SELECT fileID, file FROM Files WHERE relativePath LIKE ? AND flags=1",
            (f"%{needle}%",)).fetchall()

        total = present = 0
        for file_id, blob in rows:
            path = backup / file_id[:2] / file_id
            if path.exists() and path.stat().st_size > 0:
                total += entry_size(blob)
                present += 1

        if not rows:
            print(f"  {label:<26} {'--':>12}   NOT IN BACKUP")
        elif total == 0:
            print(f"  {label:<26} {'0 B':>12}   EMPTY -> was in iCloud")
        elif total < ICLOUD_THRESHOLD:
            print(f"  {label:<26} {human(total):>12}   NEARLY EMPTY -> likely iCloud")
        else:
            print(f"  {label:<26} {human(total):>12}   PRESENT ({present} file(s))")

    print("=" * 72)
    con.close()

print("""
How to read this:
  PRESENT       The data was in the backup and should be on the device after a
                restore. If it is missing there, the restore is the problem.
  EMPTY / NEARLY EMPTY
                The data lived in iCloud, not in this backup. It returns once
                you sign in with your Apple Account on the device -- nothing
                was lost and nothing can be recovered from the backup.
  NOT IN BACKUP The app was not installed, or it stores nothing locally.

Remember that app *data* is restored but apps themselves are not: iOS backups
contain no app binaries. WhatsApp chats stay invisible until WhatsApp is
reinstalled from the App Store.""")
