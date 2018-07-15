import coincurve
import hashlib
import json
import time

from crankycoin.models.enums import TransactionType


class Transaction(object):

    def __init__(self, source, destination, amount, fee, prev_hash='0', tx_type=TransactionType.STANDARD.value,
                 timestamp=None, tx_hash=None, asset=None, data="", signature=None):
        """
        tx_type:
            0=genesis,
            1=coinbase,
            2=standard,
            3=asset creation,
            4=asset addendum,
            5=order,
            6=fill,
            7=registration
        """
        self._source = source
        self._destination = destination
        self._amount = amount
        self._fee = fee
        self._timestamp = timestamp
        self._signature = signature
        self._tx_hash = tx_hash
        self._tx_type = tx_type
        self._asset = asset
        self._data = data
        self._prev_hash = prev_hash
        if timestamp is None:
            self._timestamp = int(time.time())
        if asset is None:
            self._asset = '29bb7eb4fa78fc709e1b8b88362b7f8cb61d9379667ad4aedc8ec9f664e16680'
        if tx_hash is None and signature is not None:
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
    def tx_type(self):
        return self._tx_type

    @property
    def asset(self):
        return self._asset

    @property
    def data(self):
        return self._data

    @property
    def prev_hash(self):
        return self._prev_hash

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
            "tx_type": self._tx_type,
            "asset": self._asset,
            "data": self._data,
            "prev_hash": self._prev_hash,
            "signature": self._signature
        }
        data_json = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(data_json.encode('utf-8'))
        return hash_object.hexdigest()

    def sign(self, private_key):
        signature = codecs.encode(coincurve.PrivateKey.from_hex(private_key).sign(self.to_signable()), 'hex')
        self._signature = signature
        self._tx_hash = self._calculate_tx_hash()
        return signature

    def to_signable(self):
        return ":".join((
            self._source,
            self._destination,
            str(self._amount),
            str(self._fee),
            str(self._timestamp),
            str(self._tx_type),
            self._asset,
            self._data,
            self._prev_hash
        ))

    def verify(self):
        return coincurve.PublicKey(codecs.decode(self._source, 'hex')).verify(codecs.decode(self._signature, 'hex'), self.to_signable())

    def to_json(self):
        return json.dumps(self, default=lambda o: {key.lstrip('_'): value for key, value in o.__dict__.items()},
                          sort_keys=True)

    def to_dict(self):
        return {key.lstrip('_'): value for key, value in self.__dict__.items()}

    @classmethod
    def from_dict(cls, transaction_dict):
        return cls(
                transaction_dict['source'],
                transaction_dict['destination'],
                transaction_dict['amount'],
                transaction_dict['fee'],
                tx_type=transaction_dict['tx_type'],
                timestamp=transaction_dict['timestamp'],
                asset=transaction_dict['asset'],
                data=transaction_dict['data'],
                prev_hash=transaction_dict['prev_hash'],
                signature=transaction_dict['signature']
        )

    def __repr__(self):
        return "<Transaction {}>".format(self._tx_hash)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


if __name__ == "__main__":
    pass
