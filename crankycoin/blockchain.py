import time
from math import floor
from multiprocessing import Lock, Manager
from Queue import Empty, Full

from block import *
from errors import *
from transaction import *


class Blockchain(object):

    INITIAL_COINS_PER_BLOCK = config['network']['initial_coins_per_block']
    HALVING_FREQUENCY = config['network']['halving_frequency']
    MAX_TRANSACTIONS_PER_BLOCK = config['network']['max_transactions_per_block']
    MINIMUM_HASH_DIFFICULTY = config['network']['minimum_hash_difficulty']
    TARGET_TIME_PER_BLOCK = config['network']['target_time_per_block']
    DIFFICULTY_ADJUSTMENT_SPAN = config['network']['difficulty_adjustment_span']
    SIGNIFICANT_DIGITS = config['network']['significant_digits']

    blocks = []

    def __init__(self, blocks=None):
        self.blocks_lock = Lock()
        self.unconfirmed_transactions_lock = Lock()
        self.unconfirmed_transactions = Manager().list
        if blocks is None:
            genesis_block = self.get_genesis_block()
            self.add_block(genesis_block)
        else:
            for block in blocks:
                self.add_block(block)

    def get_genesis_block(self):
        genesis_transaction_one = Transaction(
            "0",
            "03dd1e57d05d9cab1d8d9b727568ad951ac2d9ecd082bc36f69e021b8427812924",
            500000,
            0,
            ""
        )
        genesis_transaction_two = Transaction(
            "0",
            "03dd1e3defd36c8c0c7282ca1a324851efdb15f742cac0c5b258ef7b290ece9e5d",
            500000,
            0,
            ""
        )
        genesis_transactions = [genesis_transaction_one, genesis_transaction_two]
        genesis_block = Block(0, genesis_transactions, "", 0)
        return genesis_block

    def _check_genesis_block(self, block):
        if block != self.get_genesis_block():
            raise GenesisBlockMismatch(block.index, "Genesis Block Mismatch: {}".format(block))
        return

    def _check_hash_and_hash_pattern(self, block):
        hash_difficulty = self.calculate_hash_difficulty()
        if block.current_hash[:hash_difficulty].count('0') != hash_difficulty:
            raise InvalidHash(block.index, "Incompatible Block Hash: {}".format(block.current_hash))
        return

    def _check_index_and_previous_hash(self, block):
        latest_block = self.get_latest_block()
        if latest_block.index != block.index - 1:
            raise ChainContinuityError(block.index, "Incompatible block index: {}".format(block.index-1))
        if latest_block.current_hash != block.previous_hash:
            raise ChainContinuityError(block.index, "Incompatible block hash: {} and hash: {}".format(block.index-1, block.previous_hash))
        return

    def _check_transactions_and_block_reward(self, block):
        # transactions : list of transactions
        # transaction : dict(from, to, amount, timestamp, signature, hash)
        reward_amount = self.get_reward(block.index)
        payers = dict()
        for transaction in block.transactions[:-1]:
            if self.find_duplicate_transactions(transaction.tx_hash):
                raise InvalidTransactions(block.index, "Transactions not valid.  Duplicate transaction detected")
            if not transaction.verify():
                raise InvalidTransactions(block.index, "Transactions not valid.  Invalid Transaction signature")
            if transaction.source in payers:
                payers[transaction.source] += transaction.amount + transaction.fee
            else:
                payers[transaction.source] = transaction.amount + transaction.fee
            reward_amount += transaction.fee
        for key in payers:
            balance = self.get_balance(key)
            if payers[key] > balance:
                raise InvalidTransactions(block.index, "Transactions not valid.  Insufficient funds")
        # last transaction is block reward
        reward_transaction = block.transactions[-1]
        if reward_transaction.amount != reward_amount or reward_transaction.source != "0":
            raise InvalidTransactions(block.index, "Transactions not valid.  Incorrect block reward")
        return

    def validate_block(self, block):
        # verify genesis block integrity
        # TODO implement and use Merkle tree
        try:
            # if genesis block, check if block is correct
            if block.index == 0:
                self._check_genesis_block(block)
                return True
            # current hash of data is correct and hash satisfies pattern
            self._check_hash_and_hash_pattern(block)
            # block index is correct and previous hash is correct
            self._check_index_and_previous_hash(block)
            # block reward is correct based on block index and halving formula
            self._check_transactions_and_block_reward(block)
        except BlockchainException as bce:
            logger.warning("Validation Error (block id: %s): %s", bce.index, bce.message)
            return False
        return True

    def validate_transaction(self, transaction):
        if transaction in self.unconfirmed_transactions:
            logger.warn('Transaction not valid.  Duplicate transaction detected: {}'.format(transaction.tx_hash))
            return False
        if self.find_duplicate_transactions(transaction.tx_hash):
            logger.warn('Transaction not valid.  Replay transaction detected: {}'.format(transaction.tx_hash))
            return False
        if not transaction.verify():
            logger.warn('Transaction not valid.  Invalid transaction signature: {}'.format(transaction.tx_hash))
            return False
        balance = self.get_balance(transaction.source)
        if transaction.amount + transaction.fee > balance:
            logger.warn('Transaction not valid.  Insufficient funds: {}'.format(transaction.tx_hash))
            return False
        return True

    def alter_chain(self, blocks):
        #TODO enforce finality through key blocks
        fork_start = blocks[0].index
        alternate_blocks = self.blocks[0:fork_start]
        alternate_blocks.extend(blocks)
        alternate_chain = Blockchain(alternate_blocks)

        status = False
        if alternate_chain.get_size() > self.get_size():
            self.blocks_lock.acquire()
            try:
                self.blocks = alternate_blocks
                status = True
            finally:
                self.blocks_lock.release()
        return status

    def add_block(self, block):
        #TODO change this from memory to persistent
        status = False
        if self.validate_block(block):
            self.blocks_lock.acquire()
            try:
                self.blocks.append(block)
                status = True
            finally:
                self.blocks_lock.release()
        return status

    def mine_block(self, reward_address):
        #TODO add transaction fees
        transactions = []
        latest_block = self.get_latest_block()
        new_block_id = latest_block.index + 1
        previous_hash = latest_block.current_hash
        fees = 0

        for i in range(0, self.MAX_TRANSACTIONS_PER_BLOCK):
            unconfirmed_transaction = self.pop_next_unconfirmed_transaction()
            if unconfirmed_transaction is None:
                break
            if unconfirmed_transaction.tx_hash in [transaction.tx_hash for transaction in transactions]:
                continue
            if self.find_duplicate_transactions(unconfirmed_transaction.tx_hash):
                continue
            if not unconfirmed_transaction.verify():
                continue
            transactions.append(unconfirmed_transaction)
            fees += unconfirmed_transaction.fee

        if len(transactions) < 1:
            return None

        reward_transaction = Transaction(
            "0",
            reward_address,
            self.get_reward(new_block_id) + fees,
            0,
            "0"
        )

        transactions.append(reward_transaction)

        timestamp = int(time.time())

        i = 0
        block = Block(new_block_id, transactions, previous_hash, timestamp)

        while block.hash_difficulty < self.calculate_hash_difficulty():
            latest_block = self.get_latest_block()
            if latest_block.index >= new_block_id or latest_block.current_hash != previous_hash:
                # Next block in sequence was mined by another node.  Stop mining current block.
                # identify in-progress transactions that aren't included in the latest_block and place them back in
                # the unconfirmed transactions pool
                for transaction in transactions[:-1]:
                    if transaction not in latest_block.transactions:
                        self.push_unconfirmed_transaction(transaction)
                return None
            i += 1
            block.block_header.nonce = i
        return block

    def get_transaction_history(self, address):
        transactions = []
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction.source == address or transaction.destination == address:
                    transactions.append(transaction)
        return transactions

    def get_balance(self, address):
        balance = 0
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction.source == address:
                    balance -= transaction.amount + transaction.fee
                if transaction.destination == address:
                    balance += transaction.amount
        return balance

    def find_duplicate_transactions(self, transaction_hash):
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction.tx_hash == transaction_hash:
                    return block.index
        return False

    def recycle_transactions(self, block):
        for transaction in block.transactions[:-1]:
            if not self.find_duplicate_transactions(transaction.tx_hash):
                self.push_unconfirmed_transaction(transaction)
        return

    def validate_chain(self):
        try:
            for block in self.blocks:
                self.validate_block(block)
        except BlockchainException as bce:
            raise
        return True

    def calculate_hash_difficulty(self, index=None):
        if index is None:
            block = self.get_latest_block()
            index = block.index
        else:
            block = self.get_block_by_index(index)

        if block.index > self.DIFFICULTY_ADJUSTMENT_SPAN:
            block_delta = self.get_block_by_index(index - self.DIFFICULTY_ADJUSTMENT_SPAN)
            timestamp_delta = block.block_header.timestamp - block_delta.block_header.timestamp
            # blocks were mined quicker than target
            if timestamp_delta < (self.TARGET_TIME_PER_BLOCK * self.DIFFICULTY_ADJUSTMENT_SPAN):
                return block.hash_difficulty + 1
            # blocks were mined slower than target
            elif timestamp_delta > (self.TARGET_TIME_PER_BLOCK * self.DIFFICULTY_ADJUSTMENT_SPAN):
                return block.hash_difficulty - 1
            # blocks were mined within the target time window
            return block.hash_difficulty
        # not enough blocks were mined for an adjustment
        return self.MINIMUM_HASH_DIFFICULTY

    def get_reward(self, index):
        precision = pow(10, self.SIGNIFICANT_DIGITS)
        reward = self.INITIAL_COINS_PER_BLOCK
        for i in range(1, ((index / self.HALVING_FREQUENCY) + 1)):
            reward = floor((reward / 2.0) * precision) / precision
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
        '''
        Should only be called by mining nodes.  Full nodes keep unconfirmed transactions until
        a block has been broadcasted.  During the block's validation process, the transactions
        should be compared with the nodes' mempool.
        '''
        unconfirmed_transaction = None
        if len(self.unconfirmed_transactions) > 0:
            self.unconfirmed_transactions_lock.acquire()
            try:
                unconfirmed_transaction = self.unconfirmed_transactions.pop()
            finally:
                self.unconfirmed_transactions_lock.release()
        return unconfirmed_transaction

    def push_unconfirmed_transaction(self, transaction):
        status = False
        if self.validate_transaction(transaction):
            self.unconfirmed_transactions_lock.acquire()
            try:
                for t in self.unconfirmed_transactions:
                    if transaction.fee <= t.fee:
                        self.unconfirmed_transactions.insert(self.unconfirmed_transactions.index(t), transaction)
                        status = True
                        break
                if status is False:
                    self.unconfirmed_transactions.append(transaction)
                    status = True
            finally:
                self.unconfirmed_transactions_lock.release()
        return status

    def remove_unconfirmed_transaction(self, transaction_hash):
        status = False
        self.unconfirmed_transactions_lock.acquire()
        try:
            for t in self.unconfirmed_transactions:
                if t.tx_hash == transaction_hash:
                    self.unconfirmed_transactions.pop(self.unconfirmed_transactions.index(t))
                    status = True
                    break
        finally:
            self.unconfirmed_transactions_lock.release()
        return status

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


if __name__ == "__main__":
    pass
