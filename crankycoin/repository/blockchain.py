from math import floor
from multiprocessing import Lock
import sqlite3

from crankycoin import config, logger
from crankycoin.models.block import BlockHeader
from crankycoin.models.transaction import Transaction


class Blockchain(object):

    INITIAL_COINS_PER_BLOCK = config['network']['initial_coins_per_block']
    HALVING_FREQUENCY = config['network']['halving_frequency']
    MAX_TRANSACTIONS_PER_BLOCK = config['network']['max_transactions_per_block']
    MINIMUM_HASH_DIFFICULTY = config['network']['minimum_hash_difficulty']
    TARGET_TIME_PER_BLOCK = config['network']['target_time_per_block']
    DIFFICULTY_ADJUSTMENT_SPAN = config['network']['difficulty_adjustment_span']
    SIGNIFICANT_DIGITS = config['network']['significant_digits']
    SHORT_CHAIN_TOLERANCE = config['network']['short_chain_tolerance']
    CHAIN_DB = config['user']['chain_db']

    def __init__(self):
        self.blocks_lock = Lock()
        self.db_init()

    def db_init(self):
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(blocks)")
            if len(cursor.fetchall()) > 0:
                return
            sql = open('config/init_blockchain.sql', 'r').read()
            cursor = conn.cursor()
            cursor.executescript(sql)
        return

    def add_block(self, block):
        status = False
        branch = self.get_branch_by_hash(block.block_header.previous_hash)
        max_height = self.get_height()
        if block.height > max_height:
            # we're working on the tallest branch
            if branch > 0:
                # if an alternate branch is the tallest branch, it becomes our primary branch
                self.restructure_primary_branch(branch)
                branch = 0
        else:
            # we're not on the tallest branch, so there could be a split here
            competing_branches = self.get_branches_by_prevhash(block.block_header.previous_hash)
            if competing_branches and branch in competing_branches:
                branch = self.get_new_branch_number(block.block_header.hash, block.height)

        sql_strings = list()
        sql_strings.append("INSERT INTO blocks (hash, prevhash, merkleRoot, height, nonce, timestamp, version, branch" +
                           ") VALUES ('{}', '{}', '{}', {}, {}, {}, {}, {})"
                           .format(block.block_header.hash, block.block_header.previous_hash,
                                   block.block_header.merkle_root, block.height, block.block_header.nonce,
                                   block.block_header.timestamp, block.block_header.version, branch))
        for transaction in block.transactions:
            sql_strings.append("INSERT INTO transactions (hash, src, dest, amount, fee, timestamp, signature, type," +
                               " blockHash, asset, data, branch, prevHash)" +
                               " VALUES ('{}', '{}', '{}', {}, {}, {}, '{}', {},'{}', '{}', '{}', {}, '{}')".format(
                                    transaction.tx_hash, transaction.source, transaction.destination,
                                    transaction.amount, transaction.fee, transaction.timestamp, transaction.signature,
                                    transaction.tx_type, block.block_header.hash, transaction.asset, transaction.data,
                                    branch, transaction.prev_hash))
        sql_strings.append("UPDATE branches SET currentHash = '{}', currentHeight = {} WHERE id = {}".format(
                            block.block_header.hash, block.height, branch))

        try:
            with sqlite3.connect(self.CHAIN_DB) as conn:
                cursor = conn.cursor()
                for sql in sql_strings:
                    cursor.execute(sql)
                status = True
        except sqlite3.OperationalError as err:
            logger.error("Database Error: ", err.message)
        return status

    def get_new_branch_number(self, block_hash, height):
        sql = "INSERT INTO branches (currentHash, currentHeight) VALUES ('{}', {})".format(block_hash, height)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.lastrowid

    def prune(self):
        sql = 'SELECT id FROM branches WHERE currentHeight < (SELECT MAX(height) FROM blocks) - {}'\
            .format(self.SHORT_CHAIN_TOLERANCE)
        tx_sql = 'DELETE FROM transactions WHERE branch IN ({})'
        block_sql = 'DELETE FROM transactions WHERE branch IN ({})'
        branch_sql = 'DELETE FROM branches WHERE id IN ({})'
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            branches = [branch[0] for branch in cursor.fetchall()]
            cursor.execute(tx_sql.format(",".join(branches)))
            cursor.execute(block_sql.format(",".join(branches)))
            cursor.execute(branch_sql.format(",".join(branches)))
        return

    def restructure_primary_branch(self, branch):
        block_header, block_branch, block_height = self.get_tallest_block_header(branch=branch)
        alt_branch_hashes = []
        stop_height = block_height
        start_height = block_height
        eob = False
        while not eob:
            block_header, block_branch, block_height = self.get_block_header_by_hash(block_header.previous_hash)
            if block_branch > 0:
                # Still in alternate branch.  Continue traversing
                alt_branch_hashes.append(block_header.hash)
            else:
                # End of branch has been found
                start_height = block_height
                eob = True
        primary_branch_hashes = [b[0].hash
                                 for b in self.get_block_headers_range_iter(start_height, stop_height, branch=0)]
        block_sql = 'UPDATE blocks SET branch={} WHERE hash IN ({})'
        tx_sql = 'UPDATE transactions SET branch={} WHERE blockHash IN ({})'
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(block_sql.format(0, ",".join(alt_branch_hashes)))
            cursor.execute(tx_sql.format(0, ",".join(alt_branch_hashes)))
            cursor.execute(block_sql.format(branch, ",".join(primary_branch_hashes)))
            cursor.execute(tx_sql.format(branch, ",".join(primary_branch_hashes)))
        return

    def get_transaction_history(self, address, branch=0):
        # TODO: convert this to return a generator
        transactions = []
        sql = "SELECT * FROM transactions WHERE (src='{}' OR dest='{}') AND branch={}".format(address, address, branch)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for transaction in cursor:
                transactions.append(Transaction(transaction[1], transaction[2], transaction[3], transaction[4],
                                    tx_type=transaction[7], timestamp=transaction[5], tx_hash=transaction[0],
                                    signature=transaction[6], asset=transaction[9], data=transaction[10],
                                    prev_hash=transaction[12]))
        return transactions

    def get_transactions_by_block_hash(self, block_hash):
        transactions = []
        sql = "SELECT * FROM transactions WHERE blockHash='{}' ORDER BY hash ASC".format(block_hash)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for transaction in cursor:
                transactions.append(Transaction(transaction[1], transaction[2], transaction[3], transaction[4],
                                    tx_type=transaction[7], timestamp=transaction[5], tx_hash=transaction[0],
                                    signature=transaction[6], asset=transaction[9], data=transaction[10],
                                    prev_hash=transaction[12]))
        return transactions

    def get_transaction_hashes_by_block_hash(self, block_hash):
        sql = "SELECT hash FROM transactions WHERE blockHash='{}' ORDER BY type, hash ASC".format(block_hash)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            conn.row_factory = lambda cursor, row: row[0]
            cursor = conn.cursor()
            hashes = cursor.execute(sql).fetchall()
        return hashes

    def get_coinbase_hash_by_block_hash(self, block_hash):
        sql = "SELECT hash FROM transactions WHERE blockHash='{}' AND type=2".format(block_hash)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            tx_hash = cursor.execute(sql).fetchone()
        return tx_hash[0]

    def get_transaction_by_hash(self, transaction_hash, branch=0):
        sql = "SELECT * FROM transactions WHERE hash='{}' AND branch={}".format(transaction_hash, branch)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            transaction = cursor.fetchone()
        return Transaction(transaction[1], transaction[2], transaction[3], transaction[4], tx_type=transaction[7],
                           timestamp=transaction[5], tx_hash=transaction[0], signature=transaction[6],
                           asset=transaction[8], data=transaction[9])

    def get_balance(self, address, asset=None, branch=0):
        if asset is None:
            asset = '29bb7eb4fa78fc709e1b8b88362b7f8cb61d9379667ad4aedc8ec9f664e16680'
        balance = 0
        sql = "SELECT src, dest, amount, fee FROM transactions WHERE (src='{}' OR dest='{}') AND asset='{}' AND \
               branch={}".format(address, address, asset, branch)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for transaction in cursor:
                if transaction[0] == address:
                    balance -= transaction[2] + transaction[3]
                else:
                    balance += transaction[2]
        return balance

    def find_duplicate_transactions(self, transaction_hash):
        sql = "SELECT COUNT(*) FROM transactions WHERE hash='{}'".format(transaction_hash)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            count = cursor.fetchone()[0]
            if count > 0:
                return True
        return False

    def calculate_hash_difficulty(self, height=None):
        block_height = 0
        if height is None:
            tallest_block_header = self.get_tallest_block_header()
            if tallest_block_header is not None:
                block_header, block_branch, block_height = tallest_block_header
        else:
            block_headers_at_height = self.get_block_headers_by_height(height)
            if block_headers_at_height is not None:
                block_header, block_branch, block_height = block_headers_at_height
        height = block_height

        if height > self.DIFFICULTY_ADJUSTMENT_SPAN:
            bd_header, bd_branch, bd_height = self.get_block_headers_by_height(height - self.DIFFICULTY_ADJUSTMENT_SPAN)
            timestamp_delta = block_header.timestamp - bd_header.timestamp
            # blocks were mined quicker than target
            if timestamp_delta < (self.TARGET_TIME_PER_BLOCK * self.DIFFICULTY_ADJUSTMENT_SPAN):
                return block_header.hash_difficulty + 1
            # blocks were mined slower than target
            elif timestamp_delta > (self.TARGET_TIME_PER_BLOCK * self.DIFFICULTY_ADJUSTMENT_SPAN):
                return block_header.hash_difficulty - 1
            # blocks were mined within the target time window
            return block_header.hash_difficulty
        # not enough blocks were mined for an adjustment
        return self.MINIMUM_HASH_DIFFICULTY

    def get_reward(self, height):
        precision = pow(10, self.SIGNIFICANT_DIGITS)
        reward = self.INITIAL_COINS_PER_BLOCK
        for i in range(1, ((height / self.HALVING_FREQUENCY) + 1)):
            reward = floor((reward / 2.0) * precision) / precision
        return reward

    def get_height(self):
        sql = 'SELECT MAX(height) FROM blocks'
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            height = cursor.fetchone()[0]
        return height

    def get_branch_by_hash(self, block_hash):
        sql = "SELECT branch FROM blocks WHERE hash='{}'".format(block_hash)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            branch = cursor.fetchone()
            if branch is None:
                return 0
        return branch[0]

    def get_tallest_block_header(self, branch=0):
        # returns tuple of BlockHeader, branch, height
        sql = 'SELECT * FROM blocks WHERE height = (SELECT MAX(height) FROM blocks WHERE branch={})'.format(branch)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            block = cursor.fetchone()
        if block is None:
            return None
        return BlockHeader(block[1], block[2], block[5], block[4], block[6]), block[7], block[3]

    def get_block_headers_by_height(self, height):
        # returns tuples of BlockHeader, branch, height
        block_headers = []
        sql = 'SELECT * FROM blocks WHERE height={} ORDER BY branch'.format(height)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for block in cursor:
                block_headers.append(BlockHeader(block[1], block[2], block[5], block[4], block[6])), block[7], block[3]
        return block_headers

    def get_block_header_by_hash(self, block_hash):
        # returns tuple of BlockHeader, branch, height
        sql = "SELECT * FROM blocks WHERE hash='{}'".format(block_hash)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            block = cursor.fetchone()
        if block is None:
            return None
        return BlockHeader(block[1], block[2], block[5], block[4], block[6]), block[7], block[3]

    def get_branches_by_prevhash(self, prev_hash):
        # returns list of branches
        sql = "SELECT branch FROM blocks WHERE prevHash='{}' ORDER BY branch".format(prev_hash)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            conn.row_factory = lambda cursor, row: row[0]
            cursor = conn.cursor()
            branches = cursor.execute(sql).fetchall()
        return branches

    def get_open_branches(self, tolerance):
        # returns list of tuples of branches, hash, height
        branches = []
        # sql = 'SELECT DISTINCT branch\ FROM blocks\
        #    WHERE height >= (SELECT MAX(height) FROM blocks) - {} GROUP BY branch ORDER BY branch'.format(tolerance)
        sql = 'SELECT * FROM branches WHERE currentHeight >= (SELECT MAX(height) FROM blocks) - {} ORDER BY id'\
            .format(tolerance)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for branch in cursor:
                branches.append((branch[0], branch[1], branch[2]))
        return branches

    def get_all_block_headers_iter(self, branch=0):
        # yields tuples of BlockHeader, branch, height
        sql = 'SELECT * FROM blocks WHERE branch={}'.format(branch)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for block in cursor:
                yield BlockHeader(block[1], block[2], block[5], block[4], block[6]), block[7], block[3]

    def get_block_headers_range_iter(self, start_height, stop_height, branch=0):
        # yields tuples of BlockHeader, branch, height
        sql = 'SELECT * FROM blocks WHERE height >= {} AND height <= {} AND branch={} ORDER BY height ASC'\
            .format(start_height, stop_height, branch)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for block in cursor:
                yield BlockHeader(block[1], block[2], block[5], block[4], block[6]), block[7], block[3]

    def get_hashes_range(self, start_height, stop_height, branch=0):
        sql = 'SELECT hash FROM blocks WHERE height >= {} AND height <= {} AND branch={} ORDER BY height ASC'\
            .format(start_height, stop_height, branch)
        with sqlite3.connect(self.CHAIN_DB) as conn:
            conn.row_factory = lambda cursor, row: row[0]
            cursor = conn.cursor()
            hashes = cursor.execute(sql).fetchall()
        return hashes


if __name__ == "__main__":
    pass
