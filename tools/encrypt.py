#!/usr/bin/env python

from Cryptodome.Cipher import AES
import hashlib
from getpass import getpass

passphrase = getpass("Choose a passphrase: ")
verifypass = getpass("Re-enter passphrase: ")

if passphrase != verifypass:
    print("Passphrases do not match")
    exit()

secret = raw_input("Secret: ")
hashedpass = hashlib.sha256(passphrase).digest()
cipher = AES.new(hashedpass, AES.MODE_EAX)
ciphertext, tag = cipher.encrypt_and_digest(secret)

combined = cipher.nonce + tag + ciphertext

print("Encrypted private key: ")
print combined.encode('hex')
