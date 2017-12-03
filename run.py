#!/usr/bin/env python

import argparse
import hashlib
import sys
from getpass import getpass
from Cryptodome.Cipher import AES
from crankycoin import *


def main(argv):
    parser = argparse.ArgumentParser(description='Starts a ' + config['network']['name'] + ' node')
    parser.add_argument('mode', metavar='type', nargs='?', default=None, help='client | full | miner')
    args = parser.parse_args()
    if args.mode == "client":
        encrypted = config['user']['encrypted_private_key']
        if encrypted is None:
            print("\n\nNo private key provided. A new wallet will be generated for you...\n\n")
            client = Client()
        else:
            passphrase = getpass("Enter passphrase: ")
            encrypted = encrypted.decode('hex')
            nonce = encrypted[0:16]
            tag = encrypted[16:32]
            ciphertext = encrypted[32:]
            hashedpass = hashlib.sha256(passphrase).digest()
            cipher = AES.new(hashedpass, AES.MODE_EAX, nonce)
            private_key = cipher.decrypt_and_verify(ciphertext, tag)
            client = Client(private_key)
    elif args.mode == "full":
        ip = config['user']['ip']
        public_key = config['user']['public_key']
        if ip is None or public_key is None:
            print("\n\npublic key and IP must be provided.\n\n")
        else:
            print "\n\nfull node server starting...\n\n"
            fullnode = FullNode(ip, public_key)
    elif args.mode == "miner":
        ip = config['user']['ip']
        public_key = config['user']['public_key']
        if ip is None or public_key is None:
            print("\n\npublic key and IP must be provided.\n\n")
        else:
            print "\n\nfull node server started...\n\n"
            fullnode = FullNode(ip, public_key)
    else:
        print("Node operation mode not specified")


if __name__ == "__main__":
    main(sys.argv[1:])
