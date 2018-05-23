from unittest import TestCase
from mock import patch, Mock

from crankycoin.models.enums import TransactionType
from crankycoin.repository.blockchain import Blockchain
from crankycoin.repository.mempool import Mempool
from crankycoin.services.validator import Validator
from crankycoin.models.block import Block, BlockHeader
from crankycoin.models.transaction import Transaction


class TestValidator(TestCase):

    def setUp(self):
        self.mock_blockchain = Mock(Blockchain)
        with patch.object(Blockchain, "__init__", return_value=None) as patched_blockchain, \
            patch.object(Mempool, "__init__", return_value=None) as patched_mempool:
            self.subject = Validator()
        self.subject.blockchain = self.mock_blockchain

    def test_check_hash_and_hash_pattern_When_valid_Returns(self):
        self.mock_blockchain.calculate_hash_difficulty.return_value = 4
        mock_block = Mock(Block)
        mock_block_header = Mock(BlockHeader)
        mock_block_header.hash = "0000FFFFFFF999999999999"
        mock_block.block_header = mock_block_header

        response = self.subject.check_hash_and_hash_pattern(mock_block)

    def test_check_height_and_previous_hash_When_valid_Returns(self):
        mock_previous_block_header = Mock(BlockHeader)
        self.mock_blockchain.get_block_header_by_hash.return_value = (mock_previous_block_header, 0, 15)
        mock_block_header = Mock(BlockHeader)
        mock_block_header.previous_hash = "0000FFFFFFF999999999999"
        mock_block = Mock(Block)
        mock_block.height = 16
        mock_block.block_header = mock_block_header

        response = self.subject.check_height_and_previous_hash(mock_block)

    def test_check_block_reward(self):
        mock_transaction = Mock(Transaction)
        mock_transaction.tx_type = TransactionType.STANDARD
        mock_transaction.fee = .05
        mock_coinbase_transaction = Mock(Transaction)
        mock_coinbase_transaction.tx_type = TransactionType.COINBASE
        mock_coinbase_transaction.amount = 50.05
        mock_coinbase_transaction.source = "0"
        mock_block = Mock(Block)
        mock_block.height = 16
        mock_block.transactions = [mock_coinbase_transaction, mock_transaction]
        self.mock_blockchain.get_reward.return_value = 50

        response = self.subject.check_block_reward(mock_block)
        self.assertTrue(response)
