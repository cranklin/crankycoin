import json


class Block(object):

    def __init__(self, index, transactions, previous_hash, current_hash, timestamp, nonce):
        """
        :param index: index # of block
        :type index: int
        :param transactions: list of transactions
        :type transactions: list of transaction dicts
        :param previous_hash: previous block hash
        :type previous_hash: str
        :param current_hash: current block hash
        :type current_hash: str
        :param timestamp: timestamp of block mined
        :type timestamp: int
        :param nonce: nonce
        :type nonce: int

        transaction
        :type transaction: dict(from, to, amount, timestamp, signature, hash)
        :type from: string
        :type to: string
        :type amount: float
        :type timestamp: int
        :type signature: string
        :type hash: string
        """
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.current_hash = current_hash
        self.timestamp = timestamp
        self.nonce = nonce

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __repr__(self):
        return "<Crankycoin Block {}>".format(self.index)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other