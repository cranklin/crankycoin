# import unittest
#
# from crankycoin.models.transaction import *
# from crankycoin.repository.mempool import *
# from mock import Mock
#
#
# class TestMempool(unittest.TestCase):
#
#     def test_get_unconfirmed_transaction_returnsTransaction(self):
#         mock_transaction = Mock(Transaction)
#         tx_hash = "mock_transaction_hash"
#         mempool = Mempool()
#         mempool.unconfirmed_transactions_map[tx_hash] = mock_transaction
#         mempool.unconfirmed_transactions.append(mock_transaction)
#
#         response = mempool.get_unconfirmed_transaction(tx_hash)
#         self.assertEqual(mock_transaction, response)
#
#     def test_get_unconfirmed_transaction_whenMempoolEmpty_returnsNone(self):
#         tx_hash = "mock_transaction_hash"
#         mempool = Mempool()
#
#         response = mempool.get_unconfirmed_transaction(tx_hash)
#         self.assertEqual(None, response)
