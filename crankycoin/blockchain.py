import hashlib
import pyelliptic
import json
import datetime
from errors import *


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

    def __repr__(self):
        return "<Crankycoin Block {}>".format(self.index)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


class Blockchain(object):

    INITIAL_COINS_PER_BLOCK = 50
    HALVING_FREQUENCY = 1000
    MAX_TRANSACTIONS_PER_BLOCK = 10

    unconfirmed_transactions = []
    blocks = []

    def __init__(self, blocks=None):
        if blocks is None:
            genesis_block = self.get_genesis_block()
            self.add_block(genesis_block)
        else:
            for block in blocks:
                self.add_block(block)

    def get_genesis_block(self):
        genesis_transaction = {
                "from": "0",
                "to": "0442c0fe0050d53426395a046e3c4e6216189666544005567b0b3ed3dcf0151a1ac5b926bdfe93f15ecea3230951ed4151dadab28f2906d0052febea1b7453ce6f",
                "amount": 50,
                "signature": "0",
                "timestamp": 0,
                "hash": 0
        }
        genesis_transactions = [genesis_transaction]
        current_hash = self.calculate_block_hash(0, 0, 0, genesis_transactions, 0)
        genesis_block = Block(0, genesis_transactions, 0, current_hash, 0, 0);
        return genesis_block

    def calculate_transaction_hash(self, transaction):
        """
        Calculates sha-256 hash of transaction

        :param transaction: transaction
        :type transaction: dict(from, to, amount, timestamp, signature, (hash))

        :return: sha256 hash
        :rtype: str
        """
        # pop hash so method can calculate transactions pre or post hash
        data = transaction.copy()
        data.pop("hash", None)
        data_json = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def calculate_block_hash(self, index, previous_hash, timestamp, transactions, nonce=0):
        """
        Calculates sha-256 hash of block based on index, previous_hash, timestamp, transactions, and nonce

        :param index: index of block to hash
        :type index: int
        :param previous_hash: previous block hash
        :type previous_hash: str
        :param timestamp: timestamp of block mined
        :type timestamp: int
        :param transactions: list of transactions
        :type transactions: list of transaction dicts
        :param nonce: nonce
        :type nonce: int

        :return: sha256 hash
        :rtype: str
        """
        data = {
            "index": index,
            "previous_hash": previous_hash,
            "timestamp": timestamp,
            "transactions": transactions,
            "nonce": nonce
        }
        data_json = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def _check_hash_and_hash_pattern(self, block):
        block_hash = self.calculate_block_hash(block.index, block.previous_hash, block.timestamp, block.transactions, block.nonce)
        if block_hash != block.current_hash or block_hash[:4] != "0000":
            return False
        return True

    def _check_index_and_previous_hash(self, block):
        latest_block = self.get_latest_block()
        if latest_block.index != block.index - 1 or latest_block.current_hash != block.previous_hash:
            return False
        return True

    def _check_transactions_and_block_reward(self, block):
        # transactions : list of transactions
        # transaction : dict(from, to, amount, timestamp, signature, hash)
        payers = dict()
        for transaction in block.transactions[:-1]:
            if transaction["hash"] != self.calculate_transaction_hash(transaction):
                return False
            else:
                if self.find_duplicate_transactions(transaction["hash"]):
                    return False
            if not self.verify_signature(
                    transaction["signature"],
                    ":".join((
                        transaction["from"],
                        transaction["to"],
                        str(transaction["amount"]),
                        str(transaction["timestamp"]))),
                    transaction["from"]):
                return False
            if transaction["from"] in payers:
                payers[transaction["from"]] += transaction["amount"]
            else:
                payers[transaction["from"]] = transaction["amount"]
        for key in payers:
            balance = self.get_balance(key)
            if payers[key] > balance:
                return False
        # last transaction is block reward
        reward_transaction = block.transactions[-1]
        reward_amount = self.get_reward(block.index)
        if reward_transaction["amount"] != reward_amount or reward_transaction["from"] != 0:
            return False
        return True

    def validate_block(self, block):
        # verify genesis block integrity
        # TODO implement and use Merkle tree
        if block.index == 0:
            if block != self.get_genesis_block():
                raise GenesisBlockMismatch(block.index, "Genesis Block Mismatch: {}".format(block))
            return True
        # current hash of data is correct and hash satisfies pattern
        if not self._check_hash_and_hash_pattern(block):
            raise InvalidHash(block.index, "Invalid Hash: {}".format(block.current_hash))
        # block index is correct and previous hash is correct
        if not self._check_index_and_previous_hash(block):
            raise ChainContinuityError(block.index, "Block not compatible with previous block id: {} and hash: {}".format(block.index-1, block.previous_hash))
        # block reward is correct based on block index and halving formula
        if not self._check_transactions_and_block_reward(block):
            raise InvalidTransactions(block.index, "Transactions not valid.  Insufficient funds and/or incorrect block reward")
        return True

    def alter_chain(self, blocks):
        #TODO enforce finality through key blocks
        fork_start = blocks[0].index
        alternate_blocks = self.blocks[0:fork_start]
        alternate_blocks.extend(blocks)
        alternate_chain = Blockchain(alternate_blocks)
        if alternate_chain.get_size() > self.get_size():
            self.blocks = alternate_blocks
            return True
        return False

    def add_block(self, block):
        if self.validate_block(block):
            self.blocks.append(block)
            return True
        return False

    def mine_block(self, reward_address):
        #TODO add transaction fees
        transactions = []
        for i in range(0, self.MAX_TRANSACTIONS_PER_BLOCK):
            unconfirmed_transaction = self.pop_next_unconfirmed_transaction()
            if unconfirmed_transaction is None:
                break
            if unconfirmed_transaction["hash"] != self.calculate_transaction_hash(unconfirmed_transaction):
                continue
            if unconfirmed_transaction["hash"] in [transaction["hash"] for transaction in transactions]:
                continue
            if self.find_duplicate_transactions(unconfirmed_transaction["hash"]):
                continue
            if not self.verify_signature(
                    unconfirmed_transaction["signature"],
                    ":".join((
                        unconfirmed_transaction["from"],
                        unconfirmed_transaction["to"],
                        str(unconfirmed_transaction["amount"]),
                        str(unconfirmed_transaction["timestamp"]))),
                    unconfirmed_transaction["from"]):
                continue

            transactions.append(unconfirmed_transaction)

        if len(transactions) < 1:
            return None

        latest_block = self.get_latest_block()
        reward_transaction = {
            "from": "0",
            "to": reward_address,
            "amount": self.get_reward(latest_block.index + 1),
            "signature": "0",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        reward_transaction["hash"] = self.calculate_transaction_hash(reward_transaction)
        transactions.append(reward_transaction)

        timestamp = datetime.datetime.utcnow().isoformat()

        def new_hash(nonce):
            return self.calculate_block_hash(latest_block.index + 1, latest_block.current_hash, timestamp, transactions, nonce)

        i = 0
        while new_hash(i)[:4] != "0000":
            i += 1

        block = Block(latest_block.index + 1, transactions, latest_block.current_hash, new_hash(i), timestamp, i)
        return block

    def get_transaction_history(self, address):
        transactions = []
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction["from"] == address or transaction["to"] == address:
                    transactions.append(transaction)
        return transactions

    def get_balance(self, address):
        balance = 0
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction["from"] == address:
                    balance -= transaction["amount"]
                if transaction["to"] == address:
                    balance += transaction["amount"]
        return balance

    def find_duplicate_transactions(self, transaction_hash):
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction["hash"] == transaction_hash:
                    return block.index
        return False

    def validate_chain(self):
        try:
            for block in self.blocks:
                self.validate_block(block)
        except BlockchainException as bce:
            raise
        return True

    def get_reward(self, index):
        # 50 coins per block.  Halves every 1000 blocks
        reward = self.INITIAL_COINS_PER_BLOCK
        for i in range(1, ((index / self.HALVING_FREQUENCY) + 1)):
            reward = reward / 2
        return reward

    def get_size(self):
        return len(self.blocks)

    def get_latest_block(self):
        try:
            return self.blocks[-1]
        except IndexError:
            return None

    def get_block_by_index(self, index):
        try:
            return self.blocks[index]
        except IndexError:
            return None

    def get_all_blocks(self):
        return self.blocks

    def get_blocks_range(self, start_index, stop_index):
        return self.blocks[start_index:stop_index+1]

    def get_all_unconfirmed_transactions(self):
        return self.unconfirmed_transactions

    def pop_next_unconfirmed_transaction(self):
        try:
            return self.unconfirmed_transactions.pop(0)
        except IndexError:
            return None

    def push_unconfirmed_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)
        return True

    def verify_signature(self, signature, message, public_key):
        return pyelliptic.ECC(curve='secp256k1', pubkey=public_key.decode('hex')).verify(signature.decode('hex'), message)

    def generate_signable_transaction(self, from_address, to_address, amount, timestamp):
        return ":".join((from_address, to_address, amount, timestamp))

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


if __name__ == "__main__":
    pass
