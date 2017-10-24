import hashlib
import json
import pyelliptic
import time

from errors import *


class Transaction(object):

    def __init__(self, source, destination, amount, signature=None):
        self._source = source
        self._destination = destination
        self._amount = amount
        self._timestamp = int(time.time())
        self._signature = signature
        self._tx_hash = None
        if signature is not None:
            self._tx_hash = self._calculate_tx_hash()

    @property
    def source(self):
        return self._source

    @property
    def destination(self):
        return self._destination

    @property
    def amount(self):
        return self._amount

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def tx_hash(self):
        return self._tx_hash

    @property
    def signature(self):
        return self._signature

    @classmethod
    def from_json(cls, transaction_json):
        transaction = cls.__init__(
            transaction_json['source'],
            transaction_json['destination'],
            transaction_json['amount'],
            transaction_json.get('signature', None)
        )
        if transaction_json.get('tx_hash', None) != transaction.tx_hash:
            raise InvalidTransactionHash(transaction_json.get('tx_hash'))
        return transaction

    def _calculate_tx_hash(self):
        """
        Calculates sha-256 hash of transaction (source, destination, amount, timestamp, signature)

        :return: sha-256 hash
        :rtype: str
        """
        data = {
            "source": self._source,
            "destination": self._destination,
            "amount": self._amount,
            "timestamp": self._timestamp,
            "signature": self._signature
        }
        data_json = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def sign(self, private_key):
        signature = pyelliptic\
            .ECC(curve='secp256k1', privkey=private_key, pubkey=self._source.decode('hex'))\
            .sign(self.to_signable())\
            .encode('hex')
        self._signature = signature
        self._tx_hash = self._calculate_tx_hash()
        return signature

    def to_signable(self):
        return ":".join((
            self._source,
            self._destination,
            str(self._amount),
            str(self._timestamp)
        ))

    def verify(self):
        return pyelliptic\
            .ECC(curve='secp256k1', pubkey=self._source)\
            .verify(self._signature.decode('hex'), self.to_signable())

    def to_json(self):
        return json.dumps(self, default=lambda o: {key.lstrip('_'): value for key, value in o.__dict__.items()},
                          sort_keys=True)

    def __repr__(self):
        return "<Transaction {}>".format(self._tx_hash)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
