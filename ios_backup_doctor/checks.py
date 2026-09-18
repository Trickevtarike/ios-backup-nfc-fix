"""The individual diagnostic checks, each returning a small result object."""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

from .backup import Backup, FileEntry


@dataclass
class Integrity:
    files: int = 0
    directories: int = 0
    ok: int = 0
    legitimately_empty: int = 0
    missing: int = 0
    truncated: int = 0
    expected_bytes: int = 0
    actual_bytes: int = 0
    examples: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return self.missing == 0 and self.truncated == 0

    @property
    def broken(self) -> int:
        return self.missing + self.truncated


@dataclass
class Normalisation:
    total: int = 0
    denormalised: int = 0
    collisions: int = 0
    collision_examples: list[str] = field(default_factory=list)
    by_domain: collections.Counter = field(default_factory=collections.Counter)
    examples: list[tuple[str, str]] = field(default_factory=list)

    @property
    def affected(self) -> bool:
        return self.denormalised > 0

    @property
    def repairable(self) -> bool:
        return self.affected and self.collisions == 0


def check_integrity(backup: Backup, entries: list[FileEntry]) -> Integrity:
    """Is every file the manifest promises actually on disk?"""
    result = Integrity()
    for entry in entries:
        if not entry.is_file:
            result.directories += 1
            continue
        result.files += 1
        result.expected_bytes += entry.size

        path = backup.blob_path(entry.file_id)
        if not path.exists():
            result.missing += 1
            if len(result.examples) < 5:
                result.examples.append(entry.relative_path)
            continue

        on_disk = path.stat().st_size
        result.actual_bytes += on_disk
        if entry.size > 0 and on_disk == 0:
            result.truncated += 1
            if len(result.examples) < 5:
                result.examples.append(entry.relative_path)
        elif entry.size == 0:
            # Empty files exist on iOS too -- caches, locks, placeholders.
            result.legitimately_empty += 1
        else:
            result.ok += 1
    return result


def check_normalisation(entries: list[FileEntry]) -> Normalisation:
    """How many paths are decomposed, and would normalising them collide?"""
    result = Normalisation(total=len(entries))
    after: dict[tuple[str, str], list[FileEntry]] = collections.defaultdict(list)

    for entry in entries:
        if not entry.relative_path:
            continue
        after[(entry.domain, entry.normalised())].append(entry)
        if entry.is_denormalised:
            result.denormalised += 1
            result.by_domain[entry.domain] += 1
            if len(result.examples) < 3:
                result.examples.append((entry.relative_path, entry.normalised()))

    for (domain, path), group in after.items():
        if len(group) > 1:
            result.collisions += 1
            if len(result.collision_examples) < 5:
                result.collision_examples.append(f"{domain} / {path}")
    return result


# Databases worth reporting on, as (label, path fragment).
CORE_DATABASES = [
    ("Messages", "Library/SMS/sms.db"),
    ("Message attachments", "Library/SMS/Attachments"),
    ("Contacts", "Library/AddressBook/AddressBook.sqlitedb"),
    ("Contact images", "Library/AddressBook/AddressBookImages.sqlitedb"),
    ("Call history", "Library/CallHistoryDB/CallHistory.storedata"),
    ("Notes", "NoteStore.sqlite"),
    ("Calendar", "Library/Calendar/Calendar.sqlitedb"),
    ("Photos database", "Media/PhotoData/Photos.sqlite"),
    ("Voice memos", "Recordings/"),
    ("Safari history", "Library/Safari/History.db"),
    ("WhatsApp", "ChatStorage.sqlite"),
    ("Health", "Health/healthdb.sqlite"),
]

ICLOUD_THRESHOLD = 200 * 1024


def check_databases(backup: Backup, entries: list[FileEntry]) -> list[tuple[str, int, str]]:
    """Classify each core database as present, iCloud-only or absent.

    A local backup never contains iCloud-synced data, so a database that exists
    but is nearly empty tells you the content lives in iCloud -- it is not lost,
    but it also cannot be recovered from this backup.
    """
    results = []
    for label, needle in CORE_DATABASES:
        matches = [e for e in entries if e.is_file and needle in e.relative_path]
        if not matches:
            results.append((label, 0, "absent"))
            continue
        total = sum(e.size for e in matches
                    if backup.blob_path(e.file_id).exists())
        if total == 0:
            results.append((label, 0, "icloud"))
        elif total < ICLOUD_THRESHOLD:
            results.append((label, total, "icloud"))
        else:
            results.append((label, total, "present"))
    return results
