"""Command line interface."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from . import __version__, ui
from .backup import Backup, BackupError, describe, discover
from .checks import check_databases, check_integrity, check_normalisation
from .repair import normalise_paths


# --------------------------------------------------------------------------
# selecting and opening a backup
# --------------------------------------------------------------------------

def select_backup(arg: str | None) -> Path:
    if arg:
        path = Path(arg).expanduser()
        if not (path / "Manifest.plist").is_file():
            raise BackupError(f"Not a backup directory: {path}")
        return path

    found = discover()
    if not found:
        raise BackupError(
            "No backups found.\n\n"
            "If you know backups exist, your terminal is probably missing Full\n"
            "Disk Access. Grant it under System Settings > Privacy & Security >\n"
            "Full Disk Access, then restart the terminal."
        )
    if len(found) == 1:
        return found[0]

    print("Several backups found:\n")
    for i, path in enumerate(found, 1):
        info = describe(path)
        date = info["date"].strftime("%Y-%m-%d %H:%M") if info.get("date") else "unknown"
        print(f"  [{i}] {date}   {info.get('device') or '?'}   {path.name}")
    try:
        choice = int(input("\nWhich backup? "))
        return found[choice - 1]
    except (ValueError, IndexError, KeyboardInterrupt):
        raise BackupError("No backup selected.")


def open_backup(arg: str | None, password: str | None = None) -> Backup:
    backup = Backup(select_backup(arg))
    info = describe(backup.path)
    date = info["date"].strftime("%Y-%m-%d %H:%M") if info.get("date") else "unknown"

    ui.heading("Backup")
    ui.item(ui.INFO, "Folder", backup.path.name)
    ui.item(ui.INFO, "Created", date)
    if info.get("device"):
        ui.item(ui.INFO, "Device", f"{info['device']} · iOS {info.get('ios') or '?'}")
    ui.item(ui.OK if info.get("complete") else ui.BAD,
            "Snapshot", "finished" if info.get("complete") else "INCOMPLETE",
            "" if info.get("complete") else "this backup was never completed")

    if backup.encrypted:
        if password is None:
            password = getpass.getpass("\n  Backup password: ")
        ui.step("deriving key (a few seconds)")
        backup.unlock(password)
        ui.item(ui.OK, "Password", "correct",
                f"{len(backup.class_keys)} class keys unwrapped")
    else:
        raise BackupError("This backup is not encrypted; these tools target encrypted backups.")
    return backup


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_list(args) -> int:
    found = discover()
    if not found:
        raise BackupError("No backups found.")
    ui.heading(f"Backups in {Path.home()}/Library/.../MobileSync/Backup")
    for path in found:
        info = describe(path)
        date = info["date"].strftime("%Y-%m-%d %H:%M") if info.get("date") else "unknown"
        marks = []
        if info.get("encrypted"):
            marks.append("encrypted")
        if not info.get("complete"):
            marks.append("INCOMPLETE")
        if (path / "Manifest.db.orig").exists():
            marks.append("repaired")
        ui.item(ui.OK if info.get("complete") else ui.WARN,
                date, info.get("device") or "?", ", ".join(marks))
        print(ui.dim(f"      {path.name}"))
    print()
    return 0


def cmd_diagnose(args) -> int:
    backup = open_backup(args.backup, args.password)

    with backup.manifest_db() as con:
        ui.step("reading manifest")
        entries = backup.entries(con)

        ui.heading("Is the backup complete?")
        integrity = check_integrity(backup, entries)
        ui.item(ui.INFO, "Files", f"{integrity.files:,}")
        ui.item(ui.INFO, "Payload expected", ui.human_bytes(integrity.expected_bytes))
        ui.item(ui.INFO, "Payload on disk", ui.human_bytes(integrity.actual_bytes))
        ui.item(ui.OK if not integrity.missing else ui.BAD,
                "Missing files", f"{integrity.missing:,}")
        ui.item(ui.OK if not integrity.truncated else ui.BAD,
                "Truncated files", f"{integrity.truncated:,}")
        ui.item(ui.INFO, "Empty by design", f"{integrity.legitimately_empty:,}",
                "normal -- iOS has empty files too")

        ui.heading("Are any paths affected by the restore bug?")
        norm = check_normalisation(entries)
        ui.item(ui.INFO, "Manifest entries", f"{norm.total:,}")
        ui.item(ui.OK if not norm.affected else ui.BAD,
                "Decomposed (NFD) paths", f"{norm.denormalised:,}")
        ui.item(ui.OK if not norm.collisions else ui.BAD,
                "Collisions if normalised", f"{norm.collisions:,}")
        if norm.affected:
            for domain, count in norm.by_domain.most_common(5):
                print(ui.dim(f"      {count:>6,}  {domain}"))
            if norm.examples:
                print()
                old, new = norm.examples[0]
                print(ui.dim(f"      example: {old}"))
                print(ui.dim(f"      becomes: {new}"))
                print(ui.dim(f"      ({len(old.encode())} -> {len(new.encode())} bytes, "
                             "same readable name)"))

        if args.databases:
            ui.heading("What data does the backup hold?")
            for label, size, state in check_databases(backup, entries):
                symbol = {"present": ui.OK, "icloud": ui.WARN, "absent": ui.INFO}[state]
                note = {"present": "", "icloud": "lived in iCloud, not in this backup",
                        "absent": "not installed / nothing stored locally"}[state]
                ui.item(symbol, label,
                        ui.human_bytes(size) if size else "--", note)

    # ---- verdict -----------------------------------------------------------
    ui.heading("Verdict")
    if not integrity.complete:
        ui.verdict(ui.BAD, f"Backup is incomplete: {integrity.broken:,} broken files.",
                   "This backup cannot restore reliably. Use another copy if you have one.\n"
                   "Examples:\n  " + "\n  ".join(integrity.examples[:3]))
        return 1

    if not norm.affected:
        ui.verdict(ui.OK, "This backup is not affected by the NFC restore bug.",
                   "Every path is already normalised, and the backup is complete.\n"
                   "If your restore still fails, the cause lies elsewhere. Run the\n"
                   "restore with idevicebackup2 to see the real error message:\n\n"
                   "  idevicebackup2 -u <UDID> -i restore --system --settings \\\n"
                   '    "$HOME/Library/Application Support/MobileSync/Backup"')
        return 0

    if not norm.repairable:
        ui.verdict(ui.BAD, "Affected, but automatic repair is unsafe.",
                   f"{norm.collisions:,} paths would collide when normalised, which would\n"
                   "silently drop entries. Please open an issue with this output.\n\n"
                   "Examples:\n  " + "\n  ".join(norm.collision_examples[:3]))
        return 1

    ui.verdict(ui.WARN, f"Affected: {norm.denormalised:,} paths are stored decomposed.",
               "This is what makes the restore abort at a fixed point. Repair is safe --\n"
               "no collisions, no file is removed, no content is altered.\n\n"
               "Work on a copy, then repair it:\n\n"
               f"  cp -c -R '{backup.path}' '{backup.path}-workcopy'\n"
               f"  python3 -m ios_backup_doctor fix '{backup.path}-workcopy'\n\n"
               "Restore the repaired copy with Finder, not with idevicebackup2 --\n"
               "only Finder reinstalls your apps afterwards.")
    return 0


def cmd_fix(args) -> int:
    backup = open_backup(args.backup, args.password)

    with backup.manifest_db() as con:
        entries = backup.entries(con)
        norm = check_normalisation(entries)

    ui.heading("Repair")
    ui.item(ui.INFO, "Manifest entries", f"{norm.total:,}")
    ui.item(ui.INFO, "Paths to normalise", f"{norm.denormalised:,}")
    ui.item(ui.OK if not norm.collisions else ui.BAD,
            "Collisions", f"{norm.collisions:,}")

    if not norm.affected:
        ui.verdict(ui.OK, "Nothing to do -- this backup is not affected.")
        return 0
    if not norm.repairable:
        ui.verdict(ui.BAD, "Refusing to repair: normalising would merge distinct paths.")
        return 1

    if (backup.path / "Manifest.db.orig").exists():
        ui.item(ui.WARN, "Already repaired?", "Manifest.db.orig exists",
                "this backup was processed before")

    print()
    print(ui.yellow("  This modifies the backup in place. Work on a copy, not your only one."))
    if not args.yes:
        answer = input(f"\n  Normalise {norm.denormalised:,} paths? [y/N] ").strip().lower()
        if answer != "y":
            print("\n  Aborted, nothing changed.\n")
            return 1

    ui.step("rewriting manifest")
    result = normalise_paths(backup)

    ui.item(ui.OK, "Paths normalised", f"{result.changed:,}")
    ui.item(ui.OK if not result.remaining else ui.WARN,
            "Still decomposed", f"{result.remaining:,}")
    ui.item(ui.INFO, "Entries", f"{result.total:,}", "unchanged -- nothing was removed")
    ui.item(ui.OK, "Original saved", "Manifest.db.orig", "restore it to undo")

    ui.verdict(ui.OK, "Repaired.",
               "Now restore this backup with Finder:\n\n"
               "  1. Move any other copies out of the backup folder -- all copies share\n"
               "     one date and Finder's list cannot tell them apart\n"
               f"  2. Rename this one to the plain device UDID so Finder picks it up\n"
               "  3. Finder > device > Restore Backup...\n\n"
               "Use Finder rather than idevicebackup2: backups contain no app binaries,\n"
               "and only Finder asks the App Store to reinstall your apps.")
    return 0


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ios-backup-doctor",
        description="Diagnose and repair local iOS backups that fail to restore.",
        epilog="Start with 'diagnose'. It tells you whether this bug is your problem.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="show the backups on this Mac")
    p_list.set_defaults(func=cmd_list)

    p_diag = sub.add_parser("diagnose", help="check a backup and say what is wrong")
    p_diag.add_argument("backup", nargs="?", help="backup directory (default: ask)")
    p_diag.add_argument("--password", help="backup password (default: prompt)")
    p_diag.add_argument("--no-databases", dest="databases", action="store_false",
                        help="skip the per-database breakdown")
    p_diag.set_defaults(func=cmd_diagnose, databases=True)

    p_fix = sub.add_parser("fix", help="normalise decomposed paths (modifies the backup)")
    p_fix.add_argument("backup", nargs="?", help="backup directory (default: ask)")
    p_fix.add_argument("--password", help="backup password (default: prompt)")
    p_fix.add_argument("-y", "--yes", action="store_true", help="skip the confirmation")
    p_fix.set_defaults(func=cmd_fix)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except BackupError as exc:
        print(f"\n{ui.red('Error')}  {exc}\n", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.\n", file=sys.stderr)
        return 130
