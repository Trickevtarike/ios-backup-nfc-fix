#!/usr/bin/env python3
"""Check whether a password matches an encrypted iOS backup -- offline.

No device required. Useful to rule out the password before blaming anything else:
Finder reports a wrong password and a corrupt keybag with the same generic error.

Usage:  python3 verify_password.py [BACKUP_DIR]
"""
import sys
from ios_backup import choose_backup, unlock

backup = choose_backup(sys.argv)
print(f"Backup: {backup.name}\n")
unlock(backup)
print("\n  ==> PASSWORD IS CORRECT. Encryption is not your problem.")
