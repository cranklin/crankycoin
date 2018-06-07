#!/usr/bin/env python

from __future__ import print_function

import hashlib
from getpass import getpass
import sys
from Cryptodome.Cipher import AES

_PY3 = sys.version_info[0] > 2
if _PY3:
    raw_input = input
    import codecs

passphrase = getpass("Choose a passphrase: ").encode('utf-8')
verifypass = getpass("Re-enter passphrase: ").encode('utf-8')

if passphrase != verifypass:
    print("Passphrases do not match")
    sys.exit(1)

secret = raw_input("Secret: ")
hashedpass = hashlib.sha256(passphrase).digest()
cipher = AES.new(hashedpass, AES.MODE_EAX)
ciphertext, tag = cipher.encrypt_and_digest(secret.encode('utf-8'))

combined = "{}{}{}".format(cipher.nonce, tag, ciphertext)

print("Encrypted private key: ")
if not _PY3:
    print(combined.encode('hex')
else:
    codecs.encode(combined.encode('utf-8'), 'hex'))
