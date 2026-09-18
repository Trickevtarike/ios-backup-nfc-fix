"""The repair itself: normalise decomposed manifest paths to NFC."""
from __future__ import annotations

from dataclasses import dataclass

from .backup import Backup, BackupError


@dataclass
class RepairResult:
    changed: int
    remaining: int
    total: int


def normalise_paths(backup: Backup, dry_run: bool = False) -> RepairResult:
    """Rewrite every decomposed relativePath in the manifest as NFC.

    Nothing is deleted and no file content is touched -- only the spelling of
    the paths changes, and the rendered name stays identical. Refuses to run if
    normalising would make two entries collide, which would silently drop one.
    """
    with backup.manifest_db(writable=not dry_run) as con:
        entries = backup.entries(con)
        todo = [e for e in entries if e.is_denormalised]

        seen = {(e.domain, e.normalised()) for e in entries if e.relative_path}
        if len(seen) != len({(e.domain, e.relative_path)
                             for e in entries if e.relative_path}):
            raise BackupError(
                "Normalising would merge two distinct paths. Refusing to write.\n"
                "Run 'diagnose' for details."
            )

        if not dry_run and todo:
            con.executemany(
                "UPDATE Files SET relativePath=? WHERE fileID=?",
                [(e.normalised(), e.file_id) for e in todo])
            con.commit()

        remaining = 0
        if not dry_run:
            for entry in backup.entries(con):
                if entry.is_denormalised:
                    remaining += 1

        return RepairResult(changed=len(todo), remaining=remaining,
                            total=len(entries))
