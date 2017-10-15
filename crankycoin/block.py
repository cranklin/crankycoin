import time
import hashlib
import json


class Block(object):

    transactions = []

    def __init__(self, index, transactions, previous_hash, timestamp, nonce=0):
        """
        :param index: index # of block
        :type index: int
        :param transactions: list of transactions
        :type transactions: list of transaction objects
        :param previous_hash: previous block hash
        :type previous_hash: str
        :param current_hash: current block hash
        :type current_hash: str
        :param timestamp: timestamp of block mined
        :type timestamp: int
        :param nonce: nonce
        :type nonce: int
        """
        self._index = index
        self._transactions = transactions
        self._previous_hash = previous_hash
        self._nonce = nonce
        self._timestamp = timestamp if timestamp is not None else int(time.time())
        self._current_hash = self._calculate_block_hash()

    @property
    def index(self):
        return self._index

    @property
    def transactions(self):
        return self._transactions

    @property
    def previous_hash(self):
        return self._previous_hash

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def current_hash(self):
        return self._current_hash

    @property
    def nonce(self):
        return self._nonce

    @nonce.setter
    def nonce(self, value):
        self._nonce = value
        self._current_hash = self._calculate_block_hash()

    def _calculate_block_hash(self):
        """
        :return: sha256 hash
        :rtype: str
        """
        data = {
            "index": self._index,
            "previous_hash": self._previous_hash,
            "timestamp": self._timestamp,
            "transactions": self._transactions,
            "nonce": self._nonce
        }
        data_json = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def __repr__(self):
        return "<Crankycoin Block {}>".format(self._index)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other