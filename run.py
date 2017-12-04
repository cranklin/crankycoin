#!/usr/bin/env python

import argparse
import hashlib
import sys
from getpass import getpass
from Cryptodome.Cipher import AES
from crankycoin import *


def client():
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
    while True:
        cmd = raw_input("{} ({}) wallet > ".format(config['network']['name'], config['network']['ticker_symbol']))
        cmd_split = cmd.split()
        try:
            if cmd_split[0] == "balance":
                pass
            elif cmd_split[0] == "send":
                pass
            elif cmd_split[0] == "publickey":
                pass
            elif cmd_split[0] == "privatekey":
                pass
            elif cmd_split[0] == "history":
                pass
            elif cmd_split[0] == "quit" or cmd_split[0] == "exit":
                exit()
            else:  # help
                pass
        except IndexError:
            pass

def full():
    ip = config['user']['ip']
    public_key = config['user']['public_key']
    if ip is None or public_key is None:
        print("\n\npublic key and IP must be provided.\n\n")
    else:
        print "\n\nfull node server starting...\n\n"
        fullnode = FullNode(ip, public_key)


def miner():
    ip = config['user']['ip']
    public_key = config['user']['public_key']
    if ip is None or public_key is None:
        print("\n\npublic key and IP must be provided.\n\n")
    else:
        print "\n\nfull node server started...\n\n"
        fullnode = FullNode(ip, public_key)


def main(argv):
    parser = argparse.ArgumentParser(description='Starts a ' + config['network']['name'] + ' node')
    parser.add_argument('mode', metavar='type', nargs='?', default=None, help='client | full | miner')
    args = parser.parse_args()
    if args.mode == "client":
        client()
    elif args.mode == "full":
        full()
    elif args.mode == "miner":
        miner()
    else:
        print("Node operation mode not specified")


if __name__ == "__main__":
    main(sys.argv[1:])
