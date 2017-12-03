#!/usr/bin/env python

from Cryptodome.Cipher import AES
import hashlib
from getpass import getpass

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
print private_key
