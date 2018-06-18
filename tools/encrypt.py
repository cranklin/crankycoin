#!/usr/bin/env python

from __future__ import print_function

import codecs
import hashlib
from getpass import getpass
import sys

from Cryptodome.Cipher import AES

_PY3 = sys.version_info[0] > 2
if not _PY3:
    input = raw_input

passphrase = getpass("Choose a passphrase: ")
verifypass = getpass("Re-enter passphrase: ")

if passphrase != verifypass:
    print("Passphrases do not match")
    sys.exit(1)

secret = input("Secret: ")
hashedpass = hashlib.sha256(passphrase.encode('utf-8')).digest()
cipher = AES.new(hashedpass, AES.MODE_EAX)
ciphertext, tag = cipher.encrypt_and_digest(secret.encode('utf-8'))

combined = "{}{}{}".format(cipher.nonce, tag, ciphertext)

print("Encrypted private key: ")
if not _PY3:
    print(combined.encode('hex'))
else:
    print(codecs.encode(combined.encode('utf-8'), 'hex').decode())
