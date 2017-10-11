import hashlib
import json
import pyelliptic
import time

from errors import *


class Transaction(object):

    def __init__(self, source, destination, amount, signature=None, tx_hash=None):
        self.source = source
        self.destination = destination
        self.amount = amount
        self.timestamp = int(time.time())
        self.signature = signature
        self.tx_hash = tx_hash
        if signature is not None:
            if self.tx_hash != self.calculate_tx_hash():
                raise InvalidTransactionHash(tx_hash)

    @classmethod
    def from_json(cls, transaction_json):
        transaction = cls.__init__(
            transaction_json['source'],
            transaction_json['destination'],
            transaction_json['amount'],
            transaction_json.get('signature', None),
            transaction_json.get('tx_hash', None)
        )
        return transaction

    def calculate_tx_hash(self):
        """
        Calculates sha-256 hash of transaction (source, destination, amount, timestamp, signature)

        :return: sha-256 hash
        :rtype: str
        """
        data = {
            "source": self.source,
            "destination": self.destination,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature
        }
        data_json = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def sign(self, private_key):
        signature = pyelliptic\
            .ECC(curve='secp256k1', privkey=private_key, pubkey=self.source)\
            .sign(self.to_signable())\
            .encode('hex')
        self.signature = signature
        self.tx_hash = self.calculate_tx_hash()
        return signature

    def to_signable(self):
        return ":".join((
            self.source,
            self.destination,
            str(self.amount),
            str(self.timestamp)
        ))

    def verify(self):
        return pyelliptic\
            .ECC(curve='secp256k1', pubkey=self.source)\
            .verify(self.signature.decode('hex'), self.to_signable())

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def __repr__(self):
        return "<Transaction {}>".format(self.tx_hash)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other