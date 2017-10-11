import hashlib
import json
import pyelliptic
import random
import requests

from node import NodeMixin, BALANCE_URL, FULL_NODE_PORT, TRANSACTION_HISTORY_URL
from transaction import *


class Client(NodeMixin):

    __private_key__ = None
    __public_key__ = None

    def __init__(self, private_key=None, public_key=None):
        if private_key is not None and public_key is not None:
            self.__private_key__ = private_key.decode('hex')
            self.__public_key__ = public_key.decode('hex')
        self.ecc = self.generate_ecc_instance()

    def generate_ecc_instance(self):
        if self.__private_key__ is None or self.__public_key__ is None:
            print "ECC keys not provided.  Generating ECC keys"
            ecc = pyelliptic.ECC(curve='secp256k1')
            self.__private_key__ = ecc.get_privkey()
            self.__public_key__ = ecc.get_pubkey()
        else:
            ecc = pyelliptic.ECC(curve='secp256k1', privkey=self.__private_key__, pubkey=self.__public_key__)
        return ecc

    def get_pubkey(self, hex=True):
        return self.ecc.get_pubkey().encode('hex') if hex else self.ecc.get_pubkey()

    def get_privkey(self, hex=True):
        return self.ecc.get_privkey().encode('hex') if hex else self.ecc.get_privkey()

    def sign(self, message):
        return self.ecc.sign(message).encode('hex')

    def verify(self, signature, message, public_key=None):
        if public_key is not None:
            return pyelliptic.ECC(curve='secp256k1', pubkey=public_key.decode('hex')).verify(signature.decode('hex'), message)
        return self.ecc.verify(signature, message)

    def get_balance(self, address=None, node=None):
        if address is None:
            address = self.get_pubkey()
        if node is None:
            node = random.sample(self.full_nodes, 1)[0]
        url = BALANCE_URL.format(node, FULL_NODE_PORT, address)
        try:
            response = requests.get(url)
            return response.json()
        except requests.exceptions.RequestException as re:
            pass
        return None

    def get_transaction_history(self, address=None, node=None):
        if address is None:
            address = self.get_pubkey()
        if node is None:
            node = random.sample(self.full_nodes, 1)[0]
        url = TRANSACTION_HISTORY_URL.format(node, FULL_NODE_PORT, address)
        try:
            response = requests.get(url)
            return response.json()
        except requests.exceptions.RequestException as re:
            pass
        return None

    def create_transaction(self, to, amount):
        transaction = Transaction(
            self.get_pubkey(),
            to,
            amount
        )
        transaction.sign(self.get_privkey())
        return self.broadcast_transaction(transaction)

    def calculate_transaction_hash(self, transaction):
        """
        Calculates sha-256 hash of transaction

        :param transaction: transaction
        :type transaction: dict(from, to, amount, timestamp, signature, (hash))

        :return: sha256 hash
        :rtype: str
        """
        # pop hash so method can calculate transactions pre or post hash
        data = transaction.copy()
        data.pop("hash", None)
        data_json = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def generate_signable_transaction(self, from_address, to_address, amount, timestamp):
        return ":".join((from_address, to_address, str(amount), str(timestamp)))


if __name__ == "__main__":
    pass
