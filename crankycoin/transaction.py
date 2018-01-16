import coincurve
import hashlib
import json
import time

from errors import *


class Transaction(object):

    def __init__(self, source, destination, amount, fee, signature=None):
        self._source = source
        self._destination = destination
        self._amount = amount
        self._fee = fee
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
    def fee(self):
        return self._fee

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def tx_hash(self):
        return self._tx_hash

    @property
    def signature(self):
        return self._signature

    def _calculate_tx_hash(self):
        """
        Calculates sha256 hash of transaction (source, destination, amount, timestamp, signature)

        :return: sha256 hash
        :rtype: str
        """
        data = {
            "source": self._source,
            "destination": self._destination,
            "amount": self._amount,
            "fee": self._fee,
            "timestamp": self._timestamp,
            "signature": self._signature
        }
        data_json = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def sign(self, private_key):
        signature = coincurve.PrivateKey.from_hex(private_key).sign(self.to_signable()).encode('hex')
        self._signature = signature
        self._tx_hash = self._calculate_tx_hash()
        return signature

    def to_signable(self):
        return ":".join((
            self._source,
            self._destination,
            str(self._amount),
            str(self._fee),
            str(self._timestamp)
        ))

    def verify(self):
        return coincurve.PublicKey(self._source).verify(self._signature, self.to_signable())

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
