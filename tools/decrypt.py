#!/usr/bin/env python

from __future__ import print_function

from getpass import getpass
import hashlib
import sys
from Cryptodome.Cipher import AES

# Python 2 & 3 compatibility
_PY3 = sys.version_info[0] > 2
if _PY3:
  raw_input = input

encrypted = raw_input("Cipher: ")
passphrase = getpass("Enter passphrase: ")

encrypted = encrypted.decode('hex')
nonce = encrypted[0:16]
tag = encrypted[16:32]
ciphertext = encrypted[32:]


hashedpass = hashlib.sha256(passphrase).digest()
cipher = AES.new(hashedpass, AES.MODE_EAX, nonce)
private_key = cipher.decrypt_and_verify(ciphertext, tag)

print("Decrypted private key: ")
print(private_key)
