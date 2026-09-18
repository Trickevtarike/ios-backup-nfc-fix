# iOS backup restore fails at a fixed point — Unicode normalisation

**Symptom:** Restoring a local (Finder/iTunes) iPhone backup fails partway through,
always at the same point, with no useful error message. Finder says only:

> An error occurred and the backup could not be restored.

**Cause:** Paths in the backup manifest that contain non-ASCII characters
(umlauts, accents) are stored in **decomposed** Unicode form (NFD: `a` + combining
diaeresis). iOS resolves them in **precomposed** form (NFC: `ä`), fails to find the
staging path, and aborts the entire restore at the first such file.

**Fix:** Normalise the affected paths in the manifest to NFC. No file is removed,
no content is altered, and the readable name does not change.

---

## Is this your problem?

Likely, if all of the following hold:

- the restore fails at **the same percentage every time** (deterministic, not flaky)
- your backup passes an integrity check
- the password is correct and the iOS version is not older than the backup's
- the device has enough free space
- your data contains files or folders with **umlauts or accents** in their names

If the failure point moves around between attempts, this is *not* your problem —
that pattern points at cable, port or power.

## Getting the real error message

Finder hides the error. `libimobiledevice` shows it:

```bash
brew install libimobiledevice

idevicebackup2 -u <DEVICE_UDID> -i restore --system --settings \
  "$HOME/Library/Application Support/MobileSync/Backup"
```

An affected backup produces:

```
[==============                                    ]  27% Finished
ErrorCode 2: _restoreRegularFiles:size: rename error: No such file or directory (2)
  at path ".../File Provider Storage/music/<name with é>/<track>.mp3"
Restore Failed (Error Code 2).
```

The path in that message will contain a non-ASCII character.

## Usage

Requires Python 3.9+ and `cryptography`:

```bash
pip3 install cryptography
```

macOS protects the backup folder. Grant your terminal **Full Disk Access**
(System Settings → Privacy & Security → Full Disk Access), then restart it —
otherwise the folder appears empty rather than raising a permission error.

```bash
# 1. Rule out the password (offline, no device needed)
python3 verify_password.py

# 2. Confirm the backup is actually complete
python3 check_integrity.py

# 3. Check how many paths are affected and whether repair is safe
python3 check_collisions.py

# 4. Repair — RUN THIS ON A COPY
python3 fix_paths.py /path/to/your/backup-copy
```

Each script takes an optional backup directory; without one it discovers backups
under `~/Library/Application Support/MobileSync/Backup` and asks which to use.

### Make a copy first

Backups live in `~/Library/Application Support/MobileSync/Backup/<UDID>`. On APFS
a copy is cheap and instant:

```bash
cd ~/Library/Application\ Support/MobileSync/Backup
cp -c -R <UDID> <UDID>-workcopy      # -c = APFS clone, no extra disk space
```

`fix_paths.py` additionally saves the untouched `Manifest.db` as
`Manifest.db.orig` inside the directory it modifies, so the change is reversible.

## Restore with Finder, not with libimobiledevice

Use `idevicebackup2` to *diagnose* — it is the only way to see the real error.
But restore the repaired backup with **Finder**.

`idevicebackup2 restore` writes the app *data* but does not reliably trigger
reinstallation of the apps themselves from the App Store. iOS backups never
contain app binaries. A restore via libimobiledevice therefore leaves you with
full data containers and zero installed apps — verified here with
`ideviceinstaller list --user` reporting 0 apps against 144 GB of restored data.
Finder hands the app list to the App Store and the apps come back on their own
once you sign in.

Finder picks the backup by folder name, so make the repaired copy the active one:

```bash
cd ~/Library/Application\ Support/MobileSync/Backup
mkdir -p ~/backup-copies-aside
mv <other UDID folders> ~/backup-copies-aside/   # keep them, just out of the way
mv <UDID>-workcopy <UDID>                        # repaired copy becomes active
```

All copies of the same backup share one date, so Finder's list cannot tell them
apart — leaving exactly one in place removes the guesswork.

Then: Finder → device → **Restore Backup…**

## Safety and privacy

- The backup password is read interactively, never stored, never transmitted
- Only **metadata** is decrypted (the manifest, i.e. the file index) — file
  contents are never decrypted, copied or inspected
- `fix_paths.py` is the only script that writes; the others are read-only
- Nothing contacts the network

The decrypted manifest contains every file path on the device. The scripts keep
it in a temporary directory and delete it on exit. If you produce one yourself
for debugging, delete it afterwards.

## Why this is hard to diagnose

The macOS log records the device **rebooting after** the failure:

```
AMPDevicesAgent  Device detached: AMDevice {UDID = ...}
kernel           en9 detaching
```

which looks exactly like a failing cable or insufficient bus power. That symptom
is a consequence, not the cause. See [docs/EVIDENCE.md](docs/EVIDENCE.md) for the
full measurement trail, including every hypothesis that was tested and excluded.

## Reporting this to Apple

See [docs/APPLE_BUG_REPORT.md](docs/APPLE_BUG_REPORT.md) for a prepared report.
File it via [Feedback Assistant](https://feedbackassistant.apple.com) under
**iOS → Backup and Restore**.

The two defects worth reporting are independent:

1. A restore aborts completely because of one unresolvable path, instead of
   skipping the file and reporting it at the end
2. Finder surfaces no error code and no file name, while the underlying API
   provides both

## Status

Confirmed on one affected device.

| | |
|---|---|
| Device | iPhone, iOS 26.6.2 (23G90) |
| Host | macOS 15.7.9, Intel |
| Backup | encrypted, 129.7 GB, 128,136 files |
| Affected paths | 1,094 of 169,706 manifest entries |
| Collisions from normalising | 0 |

**Before the fix:** two independent restore attempts (Finder and libimobiledevice)
aborted at 34–35 GB, both at the same file.

**After normalising the paths to NFC:** the restore ran to completion, twice —
first with libimobiledevice, then with Finder (68 minutes, 137 GB, no errors in
the unified log). Nothing else was changed: same backup copy, same cable, same
USB port, same device. That isolates Unicode normalisation as the cause.

Reports from other configurations are welcome — please open an issue with the
output of `check_collisions.py` (it prints counts only, no personal paths).

## Licence

MIT — see [LICENSE](LICENSE).
