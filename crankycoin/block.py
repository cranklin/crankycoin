import time
import hashlib
import json


class Block(object):

    transactions = []

    def __init__(self, index, transactions, previous_hash, current_hash, timestamp, nonce):
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
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.timestamp = timestamp if timestamp is not None else int(time.time())
        self.current_hash = current_hash if current_hash is not None else self.calculate_block_hash()

    def calculate_block_hash(self):
        """
        :return: sha256 hash
        :rtype: str
        """
        data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "nonce": self.nonce
        }
        data_json = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def __repr__(self):
        return "<Crankycoin Block {}>".format(self.index)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other