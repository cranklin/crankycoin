import codecs
import hashlib
import json
import time
import pyscrypt

from crankycoin.models.transaction import Transaction
from crankycoin.models.errors import InvalidTransactions
from crankycoin import config


class BlockHeader(object):

    def __init__(self, previous_hash, merkle_root, timestamp=None, nonce=0, version=None):
        self.version = config['network']['version'] if version is None else int(version)
        self.previous_hash = previous_hash
        self.merkle_root = merkle_root
        self.nonce = int(nonce)
        self.timestamp = int(time.time()) if timestamp is None else int(timestamp)

    def to_hashable(self):
        return "{0:0>8x}".format(self.version) + \
            self.previous_hash + \
            self.merkle_root + \
            "{0:0>8x}".format(self.timestamp) + \
            "{0:0>8x}".format(self.nonce)

    @property
    def hash(self):
        """
        :return: scrypt hash
        :rtype: str
        """
        hashable = self.to_hashable().encode('utf-8')
        hash_object = pyscrypt.hash(
            password=hashable,
            salt=hashable,
            N=1024,
            r=1,
            p=1,
            dkLen=32)
        return codecs.encode(hash_object, 'hex')

    @property
    def hash_difficulty(self):
        difficulty = 0
        for c in self.hash:
            if c != '0':
                break
            difficulty += 1
        return difficulty

    def to_json(self):
        return json.dumps(self, default=lambda o: {key.lstrip('_'): value for key, value in o.__dict__.items()},
                          sort_keys=True)

    def to_dict(self):
        return {key.lstrip('_'): value for key, value in self.__dict__.items()}

    @classmethod
    def from_dict(cls, block_header_dict):
        return cls(
            block_header_dict['previous_hash'],
            block_header_dict['merkle_root'],
            block_header_dict['timestamp'],
            block_header_dict['nonce'],
            block_header_dict['version']
        )

    def __repr__(self):
        return "<Block Header {}>".format(self.merkle_root)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class Block(object):

    transactions = []

    def __init__(self, height, transactions, previous_hash, timestamp=None, nonce=0):
        """
        :param height: height # of block
        :type height: int
        :param transactions: list of transactions
        :type transactions: list of transaction objects
        :param previous_hash: previous block hash
        :type previous_hash: str
        :param timestamp: timestamp of block mined
        :type timestamp: int
        """
        self._height = height
        self._transactions = transactions
        merkle_root = self._calculate_merkle_root()
        self.block_header = BlockHeader(previous_hash, merkle_root, timestamp, nonce)

    @property
    def height(self):
        return self._height

    @property
    def transactions(self):
        if len(self._transactions) <= 1:
            return self._transactions
        coinbase = self._transactions[0]
        sorted_transactions = sorted(self._transactions[1:], key=lambda x: x.tx_hash)
        sorted_transactions.insert(0, coinbase)
        return sorted_transactions

    def _calculate_merkle_root(self):
        if len(self._transactions) < 1:
            raise InvalidTransactions(self._height, "Zero transactions in block. Coinbase transaction required")
        merkle_base = [t.tx_hash for t in self.transactions]
        while len(merkle_base) > 1:
            temp_merkle_base = []
            for i in range(0, len(merkle_base), 2):
                if i == len(merkle_base) - 1:
                    temp_merkle_base.append(
                        hashlib.sha256(merkle_base[i]).hexdigest()
                    )
                else:
                    temp_merkle_base.append(
                        hashlib.sha256(merkle_base[i] + merkle_base[i+1]).hexdigest()
                    )
            merkle_base = temp_merkle_base
        return merkle_base[0]

    def to_json(self):
        return json.dumps(self, default=lambda o: {key.lstrip('_'): value for key, value in o.__dict__.items()},
                          sort_keys=True)

    def to_dict(self):
        d = dict()
        for key, value in self.__dict__.items():
            if isinstance(value, list):
                d[key] = [v.to_dict() for v in value]
            elif hasattr(value, "to_dict"):
                d[key] = value.to_dict()
            else:
                d[key] = value
        return d

    @classmethod
    def from_dict(cls, block_dict):
        return cls(
            block_dict['height'],
            [Transaction(
                transaction['source'],
                transaction['destination'],
                transaction['amount'],
                transaction['fee'],
                tx_type=transaction['tx_type'],
                timestamp=transaction['timestamp'],
                asset=transaction['asset'],
                data=transaction['data'],
                prev_hash=transaction['prev_hash'],
                signature=transaction['signature'])
             for transaction in block_dict['transactions']
             ],
            block_dict['previous_hash'],
            block_dict['timestamp'],
            block_dict['nonce']
        )

    def __repr__(self):
        return "<Block {}>".format(self.block_header.hash)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


if __name__ == "__main__":
    pass
