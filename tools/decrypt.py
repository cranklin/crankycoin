#!/usr/bin/env python

from __future__ import print_function

import codecs
from getpass import getpass
import hashlib
import sys
from Cryptodome.Cipher import AES

# Python 2 & 3 compatibility
_PY3 = sys.version_info[0] > 2
if _PY3:
  input = raw_input

encrypted = input("Cipher: ")
passphrase = getpass("Enter passphrase: ")

encrypted = codecs.decode(encrypted, 'hex')
nonce = encrypted[0:16]
tag = encrypted[16:32]
ciphertext = encrypted[32:]


hashedpass = hashlib.sha256(passphrase.encode('utf-8')).digest()
cipher = AES.new(hashedpass, AES.MODE_EAX, nonce)
private_key = cipher.decrypt_and_verify(ciphertext, tag)

print("Decrypted private key: ")
print(private_key)
