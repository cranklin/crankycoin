#!/usr/bin/env python

from __future__ import print_function

import hashlib
from getpass import getpass
import sys
from Cryptodome.Cipher import AES

_PY3 = sys.version_info[0] > 2
if _PY3:
    raw_input = input

passphrase = getpass("Choose a passphrase: ")
verifypass = getpass("Re-enter passphrase: ")

if passphrase != verifypass:
    print("Passphrases do not match")
    sys.exit(1)

secret = raw_input("Secret: ")
hashedpass = hashlib.sha256(passphrase).digest()
cipher = AES.new(hashedpass, AES.MODE_EAX)
ciphertext, tag = cipher.encrypt_and_digest(secret)

combined = "{}{}{}".format(cipher.nonce, tag, ciphertext)

print("Encrypted private key: ")
print(combined.encode('hex'))
