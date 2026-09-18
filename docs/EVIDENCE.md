# Evidence

All logs below are real output from an affected machine, captured on
2026-09-18 during four consecutive restore attempts of the same backup.

> **Anonymisation.** Device UDID, serial number, device name and file paths have
> been replaced with placeholders. Replacement paths preserve the property that
> matters technically — non-ASCII characters stored in decomposed form — so the
> logs remain diagnostically faithful. Nothing else was altered; line structure,
> error codes and timings are verbatim.

## 1. What Finder shows

Finder reports only this, with no error code and no file name:

```
Ein Fehler ist aufgetreten und das Backup kann nicht wiederhergestellt werden.
(An error occurred and the backup could not be restored.)
```

## 2. What the system log shows

The macOS unified log is no more helpful. It records the *consequence* — the
device rebooting after the failure — which reads exactly like a cable or power
fault and sends you down the wrong path:

```
AppleMobileBackup  Restoring <private> from <private>
AMPDevicesAgent    Device detached: AMDevice {UDID = <UDID>, location ID = 0x14700000}
kernel             en9 detaching
AppleMobileBackup  _stopWithError: Error Domain=MBErrorDomain Code=200
```

`MBErrorDomain Code=200` is the generic "restore failed" bucket. Note that the
useful strings are logged as `<private>`.

## 3. What actually happened

Only `idevicebackup2` (libimobiledevice) surfaces the real error:

```
[==============                                    ]  27% Finished
ErrorCode 2: _restoreRegularFiles:size: rename error: No such file or directory (2)
  at path "/private/var/mobile/.backup.i/var/mobile/Library/SafeHarbor/<n>/Container/
           File Provider Storage/music/<Name with é in NFD>(1)/<track>.mp3"
  (MBErrorDomain/2). Underlying error: The operation couldn't be completed.
  No such file or directory (NSPOSIXErrorDomain/2).
Restore Failed (Error Code 2).
```

iOS stages incoming files under `/var/mobile/.backup.i/` and then `rename()`s
them into place. That rename fails because the target path cannot be resolved.

## 4. Reproducibility

Two independent implementations fail at the same file:

| # | Tool           | Transferred | Duration | Outcome                    |
|---|----------------|-------------|----------|----------------------------|
| 1 | Finder         | 0 GB        | ~1 s     | aborted during erase phase |
| 2 | Finder         | 0.6 GB      | 9 min    | aborted                    |
| 3 | Finder         | 35.3 GB     | 26 min   | aborted (~27 %)            |
| 4 | idevicebackup2 | ~34 GB      | 22 min   | `Restore Failed (Code 2)`  |

Attempts 3 and 4 stop at the same file. The restore is deterministic — it is not
a flaky connection.

## 5. The backup itself is intact

Verified with `check_integrity.py` before any repair:

```
  files                                 128,136
  ok                                    101,901
  directories_and_links                  41,570
  legitimately_empty                     26,235
  blob_missing                                0
  empty_but_should_have_content               0

  Expected payload:    129.7 GB
  Found on disk:       129.4 GB

  ==> BACKUP IS COMPLETE.
```

The password was independently confirmed correct (all 14 protection-class keys
unwrapped), device and backup ran the identical iOS build, and the device had
171 GB free for a 129.7 GB restore. Nothing was wrong with the backup.

## 6. Scale of the problem

```
  Manifest entries:               169,706
  Not NFC-normalised:               1,094
  Distinct paths before:          167,801
  Distinct paths after NFC:       167,801
  COLLISIONS:                           0
```

1,094 of 169,706 entries were stored decomposed. Normalising them produces no
collisions, so the repair is lossless.

Affected paths were ordinary names containing umlauts and accents, for example
(anonymised, same Unicode property):

```
File Provider Storage/photo/<word with ä>/<file>.png      77 -> 76 bytes
File Provider Storage/file/<word with ö>.apk
File Provider Storage/music/<word with é>/<track>.mp3
```

Each affected character shrinks by one byte: decomposed `a` + U+0308 (3 bytes
in UTF-8) becomes precomposed U+00E4 (2 bytes). The rendered name is identical.

## 7. Result after repair

Same backup copy, same cable, same port, same device — the only change was
normalising 1,094 manifest paths to NFC.

```
19:56  45 GB written
20:00  54 GB
20:20  95 GB
20:42  128 GB
20:52  137 GB   idevicebackup2 finished, no error
       DeviceName restored from backup (was the factory default before)
```

Attempt 5 completed in roughly one hour. It passed the 27 % mark where attempts
3 and 4 both died, and finished with device settings applied — the restored
device name is the marker that `--settings` took effect.

The final 137 GB exceeds the backup's 129.7 GB payload because the figure
includes iOS itself and caches.

This isolates Unicode normalisation as the cause: everything else was held
constant across the failing and succeeding runs.

## 8. What this rules out

During diagnosis the following were each suspected and then excluded by
measurement:

- **Corrupt backup** — integrity check: 0 missing, 0 truncated files
- **Wrong password** — all 14 class keys unwrapped offline
- **iOS version mismatch** — device and backup on the identical build
- **Insufficient space** — 171 GB free for 129.7 GB
- **Find My / activation lock** — device activated, restore started normally
- **Cable and USB port** — failure reproduced across two cables and three ports
- **Power starvation at 500 mA** — plausible, but disproved by the deterministic
  failure point; a power fault would not stop at the same file twice
- **Thermal throttling** — battery at 29.4 °C, `TimeChargingThermallyLimited = 0`

The `Device detached` log line is the strongest red herring: it is emitted
*after* the restore fails, when the device reboots.

## 9. Confirmed again via Finder

The repaired backup was restored a second time, using Finder rather than
libimobiledevice, to confirm the fix on Apple's own path:

```
21:39    7 GB   start
21:55   34 GB   <- both earlier attempts died here
22:45  137 GB
22:47   AppleMobileBackup exited

unified log, predicate process == "AppleMobileBackup",
filtered for error/stopWithError/MBErrorDomain/detach:
  (no matches)
```

68 minutes, no errors, device name restored from the backup.

One practical difference between the two paths is worth recording: after the
libimobiledevice restore, `ideviceinstaller list --user` reported **0 apps**
despite 144 GB of restored data and 50.8 GB of restored photos. App data
containers were present, the apps themselves were not. iOS backups do not
contain app binaries; Finder triggers their reinstallation from the App Store,
libimobiledevice does not. Diagnose with libimobiledevice, restore with Finder.
