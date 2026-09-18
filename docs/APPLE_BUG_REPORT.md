# Bug report for Apple Feedback Assistant

File under **iOS → Backup and Restore**. Two separate defects; they can be filed
together or individually.

---

## Title

Local backup restore aborts entirely on a single path with decomposed Unicode
characters; Finder reports no error code or file name

## Summary

Restoring an encrypted local backup fails deterministically at the first file
whose path contains non-ASCII characters stored in decomposed (NFD) Unicode form.
The restore does not skip the file — it aborts completely, discarding all progress.
Finder surfaces only a generic message, while the underlying `mobilebackup2` API
returns both an error code and the offending path.

## Steps to reproduce

1. Have a device whose filesystem contains files or folders with umlauts or
   accents in their names (e.g. under *Files* → a third-party cloud provider's
   *File Provider Storage*), stored decomposed
2. Create an encrypted local backup via Finder
3. Erase the device
4. Restore from that backup

## Expected behaviour

The restore completes. A file that cannot be written is skipped and reported at
the end, leaving the remaining ~99 % of the restore intact.

## Actual behaviour

The restore aborts at the first affected file — in the observed case at 27 %,
after roughly 35 GB of 129.7 GB. The device reboots into an empty state. Repeating
the restore fails at the identical file.

Underlying error, obtained via a third-party `mobilebackup2` client:

```
ErrorCode 2: _restoreRegularFiles:size: rename error: No such file or directory (2)
  at path "/private/var/mobile/.backup.i/var/mobile/Library/SafeHarbor/<n>/Container/
           File Provider Storage/music/<name containing é in NFD>/<track>.mp3"
  (MBErrorDomain/2). Underlying error: NSPOSIXErrorDomain/2
Restore Failed (Error Code 2).
```

iOS stages files under `/var/mobile/.backup.i/` and then `rename()`s them into
place. The rename fails because the path is looked up in a different
normalisation form than the one recorded in the manifest.

## Defect 1 — a single unresolvable path aborts the whole restore

One file out of 128,136 makes a 129.7 GB restore fail completely. There is no
partial success and no resume: the next attempt starts from zero and fails at the
same file. Users have no way to skip it.

## Defect 2 — Finder discards the diagnostic information

Finder displays:

> An error occurred and the backup could not be restored.

No error code, no file name, no log reference. The unified log is no better: the
relevant strings are redacted as `<private>`, and the visible entries describe the
post-failure reboot:

```
AMPDevicesAgent  Device detached: AMDevice {UDID = ...}
AppleMobileBackup  _stopWithError: Error Domain=MBErrorDomain Code=200
```

`Device detached` reads as a hardware fault. In the reported case this led to
hours spent on cables, USB ports, bus power and thermals — all excluded by
measurement — before a third-party client revealed the actual cause in one line.

The information exists at the API level. Finder should surface at minimum the
error code and the path.

## Diagnosis and workaround

The backup was verified intact before any repair: 128,136 files, 0 missing,
0 truncated, 129.4 of 129.7 GB present. Password verified correct offline (all 14
protection-class keys unwrapped). Device and backup on the identical iOS build.
171 GB free for a 129.7 GB restore.

1,094 of 169,706 manifest entries were stored decomposed. Normalising those paths
to NFC produced no collisions (167,801 distinct paths before and after) and made
the restore proceed past the previous failure point.

This required decrypting and rewriting the backup manifest — not something users
can reasonably be expected to do.

## Environment

- iPhone, iOS 26.6.2 (23G90)
- macOS 15.7.9 (24G830), Intel
- Encrypted local backup, 129.7 GB, 128,136 files
- Reproduced with both Finder and libimobiledevice 1.4.0

## Suggested fixes

1. Normalise path comparison during restore, or match normalisation-insensitively
   as APFS itself does
2. Continue the restore when an individual file fails; report failures at the end
3. Surface the error code and path in Finder, and stop redacting them in the log
