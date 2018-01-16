import hashlib
import time
import json
import pyscrypt

from config import *
from errors import *


class BlockHeader(object):

    def __init__(self, previous_hash, merkle_root, timestamp=None, nonce=0):
        self.version = config['network']['version']
        self.previous_hash = previous_hash
        self.merkle_root = merkle_root
        self.nonce = nonce
        self.timestamp = timestamp if timestamp is not None else int(time.time())

    def to_hashable(self):
        return "{0:0>8}".format(self.version, 'x') + \
            self.previous_hash + \
            self.merkle_root + \
            format(self.timestamp, 'x') + \
            "{0:0>8}".format(self.nonce, 'x')

    def to_json(self):
        return json.dumps(self, default=lambda o: {key.lstrip('_'): value for key, value in o.__dict__.items()},
                          sort_keys=True)

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

    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0):
        """
        :param index: index # of block
        :type index: int
        :param transactions: list of transactions
        :type transactions: list of transaction objects
        :param previous_hash: previous block hash
        :type previous_hash: str
        :param timestamp: timestamp of block mined
        :type timestamp: int
        """
        self._index = index
        self._transactions = transactions
        merkle_root = self._calculate_merkle_root()
        self.block_header = BlockHeader(previous_hash, merkle_root, timestamp, nonce)
        self._current_hash = self._calculate_block_hash()

    @property
    def index(self):
        return self._index

    @property
    def transactions(self):
        return self._transactions

    @property
    def current_hash(self):
        return self._calculate_block_hash()

    @property
    def hash_difficulty(self):
        difficulty = 0
        for c in self.current_hash:
            if c != '0':
                break
            difficulty += 1
        return difficulty

    def _calculate_block_hash(self):
        """
        :return: scrypt hash
        :rtype: str
        """
        header = self.block_header.to_hashable()
        hash_object = pyscrypt.hash(
            password=header,
            salt=header,
            N=1024,
            r=1,
            p=1,
            dkLen=32)
        return hash_object.encode('hex')

    def _calculate_merkle_root(self):
        if len(self._transactions) < 1:
            raise InvalidTransactions(self._index, "Zero transactions in block. Coinbase transaction required")
        merkle_base = [t.tx_hash for t in self._transactions]
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

    def __repr__(self):
        return "<Block {}>".format(self._index)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other