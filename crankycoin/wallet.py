import coincurve
import random
import requests

from config import *
from node import NodeMixin
from transaction import *


class Client(NodeMixin):

    __private_key__ = None
    __public_key__ = None

    def __init__(self, private_key=None):
        if private_key is not None:
            self.__private_key__ = coincurve.PrivateKey.from_hex(private_key)
        else:
            logger.info("No private key provided. Generating new key pair.")
            self.__private_key__ = coincurve.PrivateKey()
        self.__public_key__ = self.__private_key__.public_key

    def get_public_key(self):
        return self.__public_key__.format(compressed=True).encode('hex')

    def get_private_key(self):
        return self.__private_key__.to_hex()

    def sign(self, message):
        return self.__private_key__.sign(message).encode('hex')

    def verify(self, signature, message, public_key=None):
        if public_key is not None:
            return coincurve.PublicKey(public_key).verify(signature, message)
        return self.__public_key__.verify(signature, message)

    def get_balance(self, address=None, node=None):
        if address is None:
            address = self.get_public_key()
        if node is None:
            node = random.sample(self.full_nodes, 1)[0]
        url = self.BALANCE_URL.format(node, self.FULL_NODE_PORT, address)
        try:
            response = requests.get(url)
            return response.json()
        except requests.exceptions.RequestException as re:
            pass
        return None

    def get_transaction_history(self, address=None, node=None):
        if address is None:
            address = self.get_public_key()
        if node is None:
            node = random.sample(self.full_nodes, 1)[0]
        url = self.TRANSACTION_HISTORY_URL.format(node, self.FULL_NODE_PORT, address)
        try:
            response = requests.get(url)
            return response.json()
        except requests.exceptions.RequestException as re:
            pass
        return None

    def create_transaction(self, to, amount, fee):
        transaction = Transaction(
            self.get_public_key(),
            to,
            amount,
            fee
        )
        transaction.sign(self.get_private_key())
        return self.broadcast_transaction(transaction)


if __name__ == "__main__":
    pass
