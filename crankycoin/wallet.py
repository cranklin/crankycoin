import sys
import coincurve
import json
import random

from crankycoin import logger
from crankycoin.node import NodeMixin
from crankycoin.models.transaction import Transaction

_PY3 = sys.version_info[0] > 2
if _PY3:
    import codecs

class Client(NodeMixin):

    __private_key__ = None
    __public_key__ = None

    def __init__(self, peers, api_client, private_key=None):
        if private_key is not None:
            self.__private_key__ = coincurve.PrivateKey.from_hex(private_key.decode())
        else:
            logger.info("No private key provided. Generating new key pair.")
            self.__private_key__ = coincurve.PrivateKey()
        self.__public_key__ = self.__private_key__.public_key
        super(Client, self).__init__(peers, api_client)
        self.check_peers()

    def get_public_key(self):
        return self.__public_key__.format(compressed=True).encode('hex') if not _PY3 else codecs.encode(self.__public_key__.format(compressed=True), 'hex')

    def get_private_key(self):
        return self.__private_key__.to_hex()

    def sign(self, message):
        return self.__private_key__.sign(message).encode('hex')

    def verify(self, signature, message, public_key=None):
        if public_key is not None:
            return coincurve.PublicKey(public_key.decode('hex')).verify(signature.decode('hex'), message)
        return self.__public_key__.verify(signature, message)

    def get_balance(self, address=None, node=None):
        if address is None:
            address = self.get_public_key()
        if node is None:
            peers = self.discover_peers()
            node = random.sample(peers, 1)[0]
        return self.api_client.get_balance(address, node)

    def get_transaction_history(self, address=None, node=None):
        if address is None:
            address = self.get_public_key()
        if node is None:
            peers = self.discover_peers()
            node = random.sample(peers, 1)[0]
        return self.api_client.get_transaction_history(address, node)

    def create_transaction(self, to, amount, fee, prev_hash):
        self.check_peers()
        transaction = Transaction(
            self.get_public_key(),
            to,
            amount,
            fee,
            prev_hash=prev_hash
        )
        transaction.sign(self.get_private_key())
        return self.api_client.broadcast_transaction(transaction)

    def check_peers(self):
        known_peers = self.discover_peers()
        self.api_client.check_peers_light(known_peers)
        return


if __name__ == "__main__":
    pass
