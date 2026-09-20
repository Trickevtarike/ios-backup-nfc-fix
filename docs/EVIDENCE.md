# Evidence

## 0. How this situation arises

Worth stating first, because it shapes the stakes: the affected user had not
chosen to erase the device. A forgotten passcode had locked it behind
escalating retry delays — 5 minutes, 15 minutes, 1 hour, 3 hours — which leaves
erasing as the only remaining option.

That is the case in which this bug does the most damage. The device *must* be
wiped, so the backup is not a safety net any more but the only copy, and the
restore has to work. It then failed four times over two days, with no
indication of why.

Had the backup been checked before the device was erased, the affected paths
would have been found and corrected in about two minutes, and the restore would
have succeeded on the first attempt. That is the single most useful conclusion
from this whole investigation, and the reason the README leads with it.

One further note on passwords: the backup password is not the device passcode.
It is a separate secret, set once when encrypted backups are enabled, and never
asked for again — so it is easily forgotten. Here it was still known, which is
the only reason 129.7 GB were recoverable at all. An encrypted backup whose
password is lost cannot be opened by anyone, Apple included.


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

## 10. What a successful restore still leaves missing

Observed after the completed restore, and worth recording because each one
initially looked like a restore failure:

- **0 installed apps** — `ideviceinstaller list --user` returned nothing while
  the device held 144 GB of restored data, 50.8 GB of it photos. App data
  containers were fully present; the binaries were not, because backups do not
  contain them. Finder reinstalls them via the App Store, libimobiledevice does
  not.
- **Messages and Contacts appeared empty** — but `sms.db` (10 MB) and
  `AddressBook.sqlitedb` (29.5 MB) were verifiably in the backup and restored.
  They surfaced once the device was signed in to its Apple Account.

  A correction to an earlier reading: Notes were first reported as iCloud-only
  because the check looked at the legacy path `Library/Notes/notes.sqlite`
  (140 KB). iOS stores them in `NoteStore.sqlite`, which held 660 KB — they
  were in the backup all along.
- **eSIM gone** — expected: eSIM profiles are bound to device and carrier and
  are never part of a backup. The physical SIM in the same device was
  unaffected and reported `kCTSIMSupportSIMStatusReady` throughout.
- **Wallpaper and lock screen not restored** — iOS 16+ keeps these with the
  iCloud lock-screen configuration.

The lesson for diagnosis: do not evaluate a restore before the device has been
signed in and given time on power and Wi-Fi. Several of these look identical to
data loss and are not.

## 11. Verifying the tool against these measurements

The restructured CLI was run against the repaired backup and reproduced every
figure measured earlier with the standalone scripts:

```
Files                    128,136      (unchanged)
Payload expected         129.67 GB    (unchanged)
Payload on disk          129.37 GB    (unchanged)
Missing files                  0
Truncated files                0
Empty by design           26,235      (unchanged)
Manifest entries         169,706      (unchanged)
Decomposed (NFD) paths         0      (was 1,094 before the repair)
Collisions                     0
```

The run also exposed two weaknesses that were then fixed:

- The "nearly empty means iCloud" heuristic was applied to path prefixes that
  match a *collection of files* rather than one database. Few voice memos look
  identical to voice memos stored elsewhere, so the tool no longer guesses
  there; the threshold now applies only to single databases and the wording is
  conditional.
- A verdict of "0 decomposed paths" conflated two different situations: a
  backup that was never affected, and one that has been repaired. The presence
  of `Manifest.db.orig` distinguishes them, and the tool now says which.

## 12. Where the decomposed paths came from

Read from the preserved original manifest (`Manifest.db.orig`) after the
repair, so the pre-repair state is still verifiable.

```
Entries in original manifest:  169,706
Of those decomposed (NFD):       1,094

By domain
     1,004   third-party Android-to-iOS file transfer app   (92 %)
        65   commercial cloud storage provider              ( 6 %)
        14   HomeDomain / Library/Mobile Documents          (iCloud Drive)
         5   Apple local file provider
         4   third-party browser
         2   third-party fitness app

By top-level path
     1,074   File Provider Storage
        14   Library
         6   Documents

By file type
       778   .mp3          49   .icloud        6   .png
       212   .m4a          24   .pdf           4   .docx
         8   .apk           2   .mp4           2   .gpx
```

An initial hypothesis — that macOS was the source, since it has traditionally
used NFD for filenames — does not survive this measurement. Only the 14 paths
in the iCloud Drive container are consistent with it. Over 90 % arrived through
one third-party file transfer app, together with Android installer packages,
which points at an import from an Android device rather than from the Mac.

### The control group

```
106 paths containing non-ASCII characters were already NFC
 of which 89 sat in the same third-party app's domain
```

This is the most informative figure in the set. The same app produced both
forms, so it does not encode incorrectly by design — it passes through whatever
normalisation the source filesystem supplied. Apple's own apps were NFC
throughout, and iOS's own data (Photos, Messages, Contacts, Calendar) contained
no decomposed paths at all.

### Decomposed characters observed

```
1,690   e + U+0301  ->  é          36   a + U+0308  ->  ä
   54   E + U+0301  ->  É          33   u + U+0308  ->  ü
   41   a + U+0300  ->  à          29   i + U+0302  ->  î
   36   C + U+0327  ->  Ç          26   o + U+0308  ->  ö
   24   c + U+0327  ->  ç          24   e + U+0300  ->  è
   19   i + U+0308  ->  ï          14   e + U+0302  ->  ê
```

Each of these costs one byte more decomposed than precomposed, which is why
affected paths shrink by exactly the number of accented characters they carry.
