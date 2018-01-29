from multiprocessing import Lock
import sqlite3

from crankycoin import config
from crankycoin.models.transaction import Transaction


class Mempool(object):

    POOL_DB = config['user']['pool_db']

    def __init__(self):
        self.db_init()

    def db_init(self):
        with sqlite3.connect(self.POOL_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(unconfirmed_transactions)")
            if len(cursor.fetchall()) > 0:
                return
            sql = open('config/init_mempool.sql', 'r').read()
            cursor = conn.cursor()
            cursor.executescript(sql)
        return

    def get_all_unconfirmed_transactions_iter(self):
        sql = 'SELECT * FROM unconfirmed_transactions'
        with sqlite3.connect(self.POOL_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for transaction in cursor:
                yield Transaction(transaction[1], transaction[2], transaction[3], transaction[4], transaction[10],
                                  transaction[7], transaction[5], transaction[0], transaction[8], transaction[9],
                                  transaction[6])

    def get_unconfirmed_transactions_count(self):
        sql = 'SELECT count(*) FROM unconfirmed_transactions'
        with sqlite3.connect(self.POOL_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            count = cursor.fetchone()[0]
        return count

    def get_unconfirmed_transaction(self, tx_hash):
        sql = "SELECT * FROM unconfirmed_transactions WHERE hash='{}'".format(tx_hash)
        with sqlite3.connect(self.POOL_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            data = cursor.fetchone()
        if data is None:
            return None
        transaction = data[0]
        return Transaction(transaction[1], transaction[2], transaction[3], transaction[4], transaction[10],
                           transaction[7], transaction[5], transaction[0], transaction[8], transaction[9],
                           transaction[6])

    def get_unconfirmed_transactions_chunk(self, chunk_size=None):
        sql = 'SELECT * FROM unconfirmed_transactions ORDER BY fee DESC LIMIT {}'.format(chunk_size)
        transactions = []
        with sqlite3.connect(self.POOL_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for transaction in cursor:
                transactions.append(Transaction(transaction[1], transaction[2], transaction[3], transaction[4],
                                                transaction[10], transaction[7], transaction[5], transaction[0],
                                                transaction[8], transaction[9], transaction[6]))
        return transactions

    def push_unconfirmed_transaction(self, transaction):
        sql = "INSERT INTO unconfirmed_transactions (hash, src, dest, amount, fee, timestamp, signature, type, asset,"\
              " data, prevHash) VALUES ('{}', '{}', '{}', {}, {}, {}, '{}', {}, '{}', '{}', '{}')"\
                .format(transaction.tx_hash, transaction.source, transaction.destination, transaction.amount,
                        transaction.fee, transaction.timestamp, transaction.signature, transaction.tx_type,
                        transaction.asset, transaction.data, transaction.prev_hash)
        with sqlite3.connect(self.POOL_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.lastrowid

    def remove_unconfirmed_transaction(self, tx_hash):
        sql = "DELETE FROM unconfirmed_transactions WHERE hash='{}'".format(tx_hash)
        with sqlite3.connect(self.POOL_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.rowcount

    def remove_unconfirmed_transactions(self, transactions):
        sql = "DELETE FROM unconfirmed_transactions WHERE hash IN ({})"\
            .format(",".join(["'" + transaction.tx_hash + "'" for transaction in transactions]))
        with sqlite3.connect(self.POOL_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.rowcount


class MempoolMemory(object):

    def __init__(self):
        self.unconfirmed_transactions = []
        self.unconfirmed_transactions_map = {}
        self.unconfirmed_transactions_lock = Lock()

    def get_all_unconfirmed_transactions(self):
        return self.unconfirmed_transactions

    def get_all_unconfirmed_transactions_map(self):
        return self.unconfirmed_transactions_map

    def get_unconfirmed_transaction(self, tx_hash):
        return self.unconfirmed_transactions_map.get(tx_hash)

    def get_unconfirmed_transactions_chunk(self, chunk_size=None):
        self.unconfirmed_transactions_lock.acquire()
        try:
            if len(self.unconfirmed_transactions) != len(self.unconfirmed_transactions_map):
                self._synchronize_unconfirmed_transaction_map()
            if chunk_size is None or chunk_size > len(self.unconfirmed_transactions):
                transactions = self.get_all_unconfirmed_transactions()
            else:
                transactions = self.unconfirmed_transactions[-chunk_size:]
        finally:
            self.unconfirmed_transactions_lock.release()
        return transactions

    def push_unconfirmed_transaction(self, transaction):
        status = False
        self.unconfirmed_transactions_lock.acquire()
        try:
            if len(self.unconfirmed_transactions) != len(self.unconfirmed_transactions_map):
                self._synchronize_unconfirmed_transaction_map()
            if self.unconfirmed_transactions_map.get(transaction.tx_hash) is None:
                for t in self.unconfirmed_transactions:
                    if transaction.fee <= t.fee:
                        self.unconfirmed_transactions.insert(self.unconfirmed_transactions.index(t), transaction)
                        status = True
                        break
                if status is False:
                    self.unconfirmed_transactions.append(transaction)
                    status = True
                self.unconfirmed_transactions_map[transaction.tx_hash] = transaction
        finally:
            self.unconfirmed_transactions_lock.release()
        return status

    def remove_unconfirmed_transaction(self, transaction_hash):
        status = False
        self.unconfirmed_transactions_lock.acquire()
        try:
            if len(self.unconfirmed_transactions) != len(self.unconfirmed_transactions_map):
                self._synchronize_unconfirmed_transaction_map()
            transaction = self.unconfirmed_transactions_map.pop(transaction_hash, None)
            if transaction is not None:
                self.unconfirmed_transactions.remove(transaction)
                status = True
        finally:
            self.unconfirmed_transactions_lock.release()
        return status

    def remove_unconfirmed_transactions(self, transactions):
        self.unconfirmed_transactions_lock.acquire()
        try:
            if len(self.unconfirmed_transactions) != len(self.unconfirmed_transactions_map):
                self._synchronize_unconfirmed_transaction_map()
            for t in transactions:
                if self.unconfirmed_transactions_map.pop(t.tx_hash, None) is not None:
                    self.unconfirmed_transactions.remove(t)
        finally:
            self.unconfirmed_transactions_lock.release()
        return

    def _synchronize_unconfirmed_transaction_map(self):
        # this method does not acquire a lock.  It is assumed that the calling method will acquire the lock
        # ensure uniqueness
        self.unconfirmed_transactions = sorted(set(self.unconfirmed_transactions), key=lambda t: t.fee)
        # rebuild map
        self.unconfirmed_transactions_map = {t.tx_hash: t for t in self.unconfirmed_transactions}
        return


if __name__ == "__main__":
    pass
