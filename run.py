#!/usr/bin/env python

import argparse
import hashlib
import sys
from getpass import getpass
from Cryptodome.Cipher import AES
from crankycoin import *


def client():
    helptext = '''
        Available commands:
        ===================
        balance <public key (optional)>
        send <destination> <amount>
        publickey
        privatekey
        history <public key (optional)>
        quit or exit
    '''
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
        try:
            private_key = cipher.decrypt_and_verify(ciphertext, tag)
            client = Client(private_key)
        except ValueError as ve:
            logger.warn('Invalid passphrase')
            print("\n\nInvalid passphrase\n\n")
            exit()

    while True:
        cmd = raw_input("{} ({}) wallet > ".format(config['network']['name'], config['network']['ticker_symbol']))
        cmd_split = cmd.split()
        try:
            if cmd_split[0] == "balance":
                if len(cmd_split) == 2:
                    print client.get_balance(cmd_split[1])
                else:
                    print client.get_balance()
            elif cmd_split[0] == "send":
                if len(cmd_split) == 3:
                    print client.create_transaction(cmd_split[1], float(cmd_split[2]))
                else:
                    print("\nRequires destination and amount\n")
            elif cmd_split[0] == "publickey":
                print client.get_public_key()
            elif cmd_split[0] == "privatekey":
                print client.get_private_key()
            elif cmd_split[0] == "history":
                if len(cmd_split) == 2:
                    print client.get_transaction_history(cmd_split[1])
                else:
                    print client.get_transaction_history()
            elif cmd_split[0] == "quit" or cmd_split[0] == "exit":
                exit()
            else:  # help
                print helptext
        except IndexError:
            pass


def full():
    helptext = '''
        Available commands:
        ===================
        synchronize
        addnode <host>
        getnodes
        loadblockchain <path/to/blockchain>
        getblock <index (optional)>
        getblocks <start index (optional)> <stop index (optional)>
        quit or exit
    '''
    ip = config['user']['ip']
    public_key = config['user']['public_key']
    if ip is None or public_key is None:
        print("\n\npublic key and IP must be provided.\n\n")
        exit()
    else:
        print "\n\nfull node starting...\n\n"
        fullnode = FullNode(ip, public_key)

    while True:
        cmd = raw_input("{} ({}) full node > ".format(config['network']['name'], config['network']['ticker_symbol']))
        cmd_split = cmd.split()
        try:
            if cmd_split[0] == "synchronize":
                print fullnode.synchronize()
            elif cmd_split[0] == "addnode":
                if len(cmd_split) == 2:
                    print fullnode.add_node(cmd_split[1])
                else:
                    print("\nRequires host of node to add\n")
            elif cmd_split[0] == "getnodes":
                print fullnode.full_nodes
            elif cmd_split[0] == "loadblockchain":
                if len(cmd_split) == 2:
                    print fullnode.load_blockchain(cmd_split[1])
                else:
                    print("\nRequires path/to/blockchain\n")
            elif cmd_split[0] == "getblock":
                if len(cmd_split) == 2:
                    print fullnode.blockchain.get_block_by_index(int(cmd_split[1]))
                else:
                    print fullnode.blockchain.get_latest_block()
            elif cmd_split[0] == "getblocks":
                if len(cmd_split) == 3:
                    print fullnode.blockchain.get_blocks_range(int(cmd_split[1]), int(cmd_split[2]))
                else:
                    print fullnode.blockchain.get_all_blocks()
            elif cmd_split[0] == "quit" or cmd_split[0] == "exit":
                fullnode.shutdown(True)
                exit()
            else:  # help
                print helptext
        except IndexError:
            pass


def miner():
    helptext = '''
        Available commands:
        ===================
        synchronize
        addnode <host>
        getnodes
        loadblockchain <path/to/blockchain>
        getblock <index (optional)>
        getblocks <start index (optional)> <stop index (optional)>
        quit or exit
    '''
    ip = config['user']['ip']
    public_key = config['user']['public_key']
    if ip is None or public_key is None:
        print("\n\npublic key and IP must be provided.\n\n")
        exit()
    else:
        print "\n\nmining node starting...\n\n"
        fullnode = FullNode(ip, public_key, mining=True)

    while True:
        cmd = raw_input("{} ({}) full node > ".format(config['network']['name'], config['network']['ticker_symbol']))
        cmd_split = cmd.split()
        try:
            if cmd_split[0] == "synchronize":
                print fullnode.synchronize()
            elif cmd_split[0] == "addnode":
                if len(cmd_split) == 2:
                    print fullnode.add_node(cmd_split[1])
                else:
                    print("\nRequires host of node to add\n")
            elif cmd_split[0] == "getnodes":
                print fullnode.full_nodes
            elif cmd_split[0] == "loadblockchain":
                if len(cmd_split) == 2:
                    print fullnode.load_blockchain(cmd_split[1])
                else:
                    print("\nRequires path/to/blockchain\n")
            elif cmd_split[0] == "getblock":
                if len(cmd_split) == 2:
                    print fullnode.blockchain.get_block_by_index(int(cmd_split[1]))
                else:
                    print fullnode.blockchain.get_latest_block()
            elif cmd_split[0] == "getblocks":
                if len(cmd_split) == 3:
                    print fullnode.blockchain.get_blocks_range(int(cmd_split[1]), int(cmd_split[2]))
                else:
                    print fullnode.blockchain.get_all_blocks()
            elif cmd_split[0] == "quit" or cmd_split[0] == "exit":
                fullnode.shutdown(True)
                exit()
            else:  # help
                print helptext
        except IndexError:
            pass


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
