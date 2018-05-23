import hashlib

from crankycoin import logger, config
from crankycoin.models.enums import TransactionType
from crankycoin.repository.blockchain import Blockchain
from crankycoin.repository.mempool import Mempool
from crankycoin.models.errors import InvalidHash, ChainContinuityError, InvalidTransactions, BlockchainException


class Validator(object):

    def __init__(self):
        self.blockchain = Blockchain()
        self.mempool = Mempool()

    def check_hash_and_hash_pattern(self, block):
        hash_difficulty = self.blockchain.calculate_hash_difficulty(block.height)
        if block.block_header.hash[:hash_difficulty].count('0') != hash_difficulty:
            raise InvalidHash(block.height, "Incompatible Block Hash: {}".format(block.block_header.hash))
        return

    def check_height_and_previous_hash(self, block):
        previous_block = self.blockchain.get_block_header_by_hash(
            block.block_header.previous_hash)
        if previous_block is None:
            raise ChainContinuityError(block.height, "Incompatible block hash: {} and hash: {}"
                                       .format(block.height-1, block.block_header.previous_hash))
        previous_block_header, previous_block_branch, previous_block_height = previous_block
        if previous_block_height != block.height - 1:
            raise ChainContinuityError(block.height, "Incompatible block height: {}".format(block.height-1))
        return

    def check_block_reward(self, block):
        reward_amount = self.blockchain.get_reward(block.height)
        for transaction in block.transactions[1:]:
            if TransactionType(transaction.tx_type) == TransactionType.COINBASE:
                logger.warn("Block not valid.  Multiple coinbases detected")
                return False
            reward_amount += transaction.fee
        # first transaction is coinbase
        reward_transaction = block.transactions[0]
        if TransactionType(reward_transaction.tx_type) != TransactionType.COINBASE:
            logger.warn("Block not valid.  Missing coinbase")
            return False
        if reward_transaction.amount != reward_amount:
            logger.warn("Invalid block reward {} should be {}".format(reward_transaction.amount, reward_amount))
            return False
        if reward_transaction.source != "0":
            logger.warn("Invalid Coinbase source")
            return False
        return True

    def validate_block_header(self, block_header, transactions_inv):
        if self.blockchain.get_block_header_by_hash(block_header.hash):
            logger.warn('Block Header already exists')
            return False
        if block_header.version != config['network']['version']:
            logger.warn('Incompatible version')
            return False
        if block_header.merkle_root != self.calculate_merkle_root(transactions_inv):
            logger.warn('Invalid merkle root')
            return False
        previous_block = self.blockchain.get_block_header_by_hash(block_header.previous_hash)
        if previous_block is None:
            return None
        previous_block_header, previous_block_branch, previous_block_height = previous_block
        if self.blockchain.calculate_hash_difficulty(previous_block_height + 1) > block_header.hash_difficulty:
            logger.warn('Invalid hash difficulty')
            return False
        return previous_block_height + 1

    def validate_block(self, block, merkle_root):
        if block.block_header.merkle_root != merkle_root:
            logger.warn("invalid merkle root")
            return False
        if not self.check_block_reward(block):
            logger.warn("Invalid block reward")
            return False
        return True

    def validate_block_transactions_inv(self, transactions_inv):
        """
        Checks a list of transaction hashes, checks for double-spends and/or entries in the mempool
        Returns a list of unknown transaction hashes

        :param transactions_inv:
        :return: block_transactions, missing_transactions_inv
        :rtype: tuple(list, list)
        """
        missing_transactions_inv = []
        block_transactions = []
        for tx_hash in transactions_inv:
            if self.blockchain.find_duplicate_transactions(tx_hash):
                logger.warn('Transaction not valid.  Double-spend prevented: {}'.format(tx_hash))
                return False
            transaction = self.mempool.get_unconfirmed_transaction(tx_hash)
            if transaction is None:
                missing_transactions_inv.append(tx_hash)
            else:
                block_transactions.append(transaction)
        return block_transactions, missing_transactions_inv

    def validate_transaction(self, transaction):
        """
        Validate a single transaction.  Check for double-spend, invalid signature, and insufficient funds

        :param transaction:
        :return: boolean
        :rtype: boolean
        """
        if self.blockchain.find_duplicate_transactions(transaction.tx_hash):
            logger.warn('Transaction not valid.  Double-spend prevented: {}'.format(transaction.tx_hash))
            return False
        if not transaction.verify():
            logger.warn('Transaction not valid.  Invalid transaction signature: {}'.format(transaction.tx_hash))
            return False
        balance = self.blockchain.get_balance(transaction.source)
        if transaction.amount + transaction.fee > balance:
            logger.warn('Transaction not valid.  Insufficient funds: {}'.format(transaction.tx_hash))
            return False
        return True

    @staticmethod
    def calculate_merkle_root(tx_hashes):
        coinbase_hash = tx_hashes[0]
        merkle_base = sorted(tx_hashes[1:])
        merkle_base.insert(0, coinbase_hash)
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


if __name__ == "__main__":
    pass
