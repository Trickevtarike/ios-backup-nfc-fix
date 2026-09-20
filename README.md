# iOS Backup Doctor

**Your iPhone backup restore fails at the same percentage every time, and Finder
only says "An error occurred"?** This finds out why, and fixes the most common
cause.

```bash
pip3 install cryptography
python3 -m ios_backup_doctor diagnose
```

That is it. One command, one password prompt, one clear answer.

---

## The problem this solves

Restoring a local (Finder/iTunes) backup aborts partway through — always at the
same point — and Finder gives you nothing to work with:

> An error occurred and the backup could not be restored.

No error code. No file name. The system log is worse than useless: it shows the
device rebooting *after* the failure, which reads like a broken cable and sends
you hunting through USB ports and power supplies for hours.

The actual cause is usually this: paths in the backup that contain **umlauts or
accents** are stored in *decomposed* Unicode (`a` + combining diaeresis), while
iOS looks them up *precomposed* (`ä`). It cannot resolve the path, the `rename`
into place fails — and the entire restore is discarded over one file.

**The fix** is to normalise those paths. Nothing is deleted, no content changes,
and the readable name stays exactly the same.

## Usage

```bash
# What backups are on this Mac?
python3 -m ios_backup_doctor list

# Check one -- this is where you start
python3 -m ios_backup_doctor diagnose

# Repair a copy (see below)
python3 -m ios_backup_doctor fix ~/path/to/backup-copy
```

`diagnose` verifies the password, checks that the backup is complete, counts
affected paths, confirms the repair would be collision-free, and shows which
core databases the backup holds. It ends with a verdict that tells you whether
this bug is your problem — and if it is not, where to look instead.

### Requirements

Python 3.9+ and `cryptography`. macOS protects the backup folder, so grant your
terminal **Full Disk Access** (System Settings → Privacy & Security → Full Disk
Access) and restart it. Without that the folder appears empty rather than
raising a permission error.

### Work on a copy

On APFS a copy is instant and costs no extra disk space:

```bash
cd ~/Library/Application\ Support/MobileSync/Backup
cp -c -R <UDID> <UDID>-workcopy
python3 -m ios_backup_doctor fix <UDID>-workcopy
```

`fix` also keeps the untouched `Manifest.db` as `Manifest.db.orig`, so the
change is reversible either way.

## Restore with Finder, not with libimobiledevice

Use `idevicebackup2` to *diagnose* — it is the only way to see the real error
message. But restore the repaired backup with **Finder**.

iOS backups contain app *data*, never app binaries. Finder hands your app list
to the App Store and the apps come back on their own; `idevicebackup2` does not.
Restoring through it leaves you with full data containers and **zero installed
apps** — confirmed here: `ideviceinstaller list --user` reported 0 apps against
144 GB of restored data.

Finder picks a backup by folder name, and every copy of one backup shares the
same date, so its list cannot tell them apart. Leave exactly one in place:

```bash
cd ~/Library/Application\ Support/MobileSync/Backup
mkdir -p ~/backup-copies-aside
mv <other folders> ~/backup-copies-aside/   # keep them, just out of the way
mv <UDID>-workcopy <UDID>                   # the repaired copy becomes active
```

Then: Finder → device → **Restore Backup…**

## What a backup does not restore

A successful restore still leaves gaps, and they are easy to mistake for a
failed restore. None of the following are defects:

| Missing afterwards | Why | What to do |
|---|---|---|
| **eSIM / mobile plan** | eSIM profiles are cryptographically bound to device and carrier and are deliberately never included in a backup — otherwise a mobile identity could be cloned by restoring a backup onto another device | Settings → Cellular → Add eSIM sometimes offers the previous plan. Otherwise ask the carrier for a new profile; the number stays the same. Keep your EID ready (Settings → General → About → EID) |
| **Apps** | Backups hold app *data*, never app binaries | Sign in with your Apple Account; Finder-restored devices reinstall them automatically. After an `idevicebackup2` restore, fetch them from App Store → Account → Purchased |
| **iCloud-synced data** | Notes, and Messages or Contacts when iCloud sync is on, live in iCloud and are not part of a local backup | Returns on its own after signing in. `diagnose` shows which databases were actually in the backup |
| **Wallpaper and lock screen** | Since iOS 16 these hang off the iCloud lock-screen configuration | Set again manually |
| **Device passcode, Face ID** | Never restored, by design | Set up again |
| **Apple Account sign-in** | Credentials are never in a backup | Sign in manually |

The practical consequence: judge a restore only **after** signing in with your
Apple Account and letting the device sit on power and Wi-Fi for a while. A
freshly restored device looks alarmingly empty before that — no apps, a bare
home screen, an empty Messages app — while the data is already on disk.

## Is this actually my problem?

Likely, if all of these hold:

- the restore fails at **the same percentage every time** — deterministic, not flaky
- the backup passes the integrity check
- the password is correct and the device's iOS is not older than the backup's
- there is enough free space on the device
- your files or folders contain **umlauts or accents** in their names

If the failure point moves around between attempts, this is *not* your problem —
that pattern points at cable, port or power. `diagnose` says so explicitly.

### Seeing the real error yourself

```bash
brew install libimobiledevice
idevicebackup2 -u <DEVICE_UDID> -i restore --system --settings \
  "$HOME/Library/Application Support/MobileSync/Backup"
```

An affected backup produces the line Finder withholds:

```
[==============                                    ]  27% Finished
ErrorCode 2: _restoreRegularFiles:size: rename error: No such file or directory (2)
  at path ".../File Provider Storage/music/<name with é>/<track>.mp3"
Restore Failed (Error Code 2).
```

## Safety and privacy

- The password is read interactively, never stored, never transmitted
- Only **metadata** is decrypted — the manifest, i.e. the file index. File
  contents are never decrypted, copied or inspected
- `fix` is the only command that writes, it asks before doing so, and it keeps
  the original manifest
- `fix` refuses to run if normalising would merge two distinct paths
- Nothing contacts the network

The decrypted manifest holds every file path on the device. It lives in a
temporary directory and is deleted when the command exits.

## Status

Confirmed on one affected device.

| | |
|---|---|
| Device | iPhone 15 Pro Max, iOS 26.6.2 (23G90) |
| Host | macOS 15.7.9, Intel |
| Backup | encrypted, 129.7 GB, 128,136 files |
| Affected paths | 1,094 of 169,706 manifest entries |
| Collisions from normalising | 0 |

**Before:** two independent restore attempts, Finder and libimobiledevice, both
aborted at 34–35 GB on the same file.

**After:** the restore ran to completion twice — first with libimobiledevice,
then with Finder (68 minutes, 137 GB, no errors in the unified log). Same backup
copy, same cable, same USB port, same device. That isolates Unicode
normalisation as the cause.

[docs/EVIDENCE.md](docs/EVIDENCE.md) has the full measurement trail, including
every hypothesis that was tested and excluded along the way.

Reports from other configurations are welcome — please open an issue with the
output of `diagnose`, which prints counts and domains but no personal paths.

## Reporting this to Apple

[docs/APPLE_BUG_REPORT.md](docs/APPLE_BUG_REPORT.md) is a prepared report for
[Feedback Assistant](https://feedbackassistant.apple.com), filed under
**iOS → Backup and Restore**. Two independent defects are worth reporting:

1. A restore aborts completely over one unresolvable path instead of skipping
   the file and reporting it at the end
2. Finder surfaces no error code and no file name, while the underlying API
   provides both

## Licence

MIT — see [LICENSE](LICENSE).
