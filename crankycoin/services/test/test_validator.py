from unittest import TestCase, skip
from mock import patch, Mock, MagicMock

from crankycoin import config
from crankycoin.models.enums import TransactionType
from crankycoin.repository.blockchain import Blockchain
from crankycoin.repository.mempool import Mempool
from crankycoin.services.validator import Validator
from crankycoin.models.block import Block, BlockHeader
from crankycoin.models.transaction import Transaction


class TestValidator(TestCase):

    def setUp(self):
        self.mock_blockchain = Mock(Blockchain)
        self.mock_mempool = Mock(Mempool)
        with patch.object(Blockchain, "__init__", return_value=None) as patched_blockchain, \
            patch.object(Mempool, "__init__", return_value=None) as patched_mempool:
            self.subject = Validator()
        self.subject.blockchain = self.mock_blockchain
        self.subject.mempool = self.mock_mempool

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

    def test_validate_block_header(self):
        self.mock_blockchain.get_block_header_by_hash.side_effect = [None, (Mock(), 0, 15)]
        self.mock_blockchain.calculate_hash_difficulty.return_value = 4
        mock_block_header = Mock(BlockHeader)
        mock_block_header.version = config['network']['version']
        mock_block_header.merkle_root = "0123456789ABCDEF"
        mock_block_header.hash_difficulty = 4
        mock_block_header.previous_hash = "0000123412341234"

        with patch('crankycoin.services.validator.Validator.calculate_merkle_root', return_value="0123456789ABCDEF") as patched_calculate_merkle_root:
            response = self.subject.validate_block_header(mock_block_header, [])

        self.assertTrue(response)

    def test_validate_block(self):
        mock_block_header = Mock(BlockHeader)
        mock_block_header.merkle_root = "0123456789ABCDEF"
        mock_block = Mock(Block)
        mock_block.block_header = mock_block_header

        with patch('crankycoin.services.validator.Validator.check_block_reward', return_value=True) as patched_check_block_reward:
            response = self.subject.validate_block(mock_block, "0123456789ABCDEF")

        self.assertTrue(response)

    def test_validate_block_transactions_inv(self):
        mock_transaction = Mock(Transaction)
        self.mock_blockchain.find_duplicate_transactions.return_value = False
        self.mock_mempool.get_unconfirmed_transaction.side_effect = [None, mock_transaction]

        response = self.subject.validate_block_transactions_inv(['tx_hash_one', 'tx_hash_two'])

        self.assertIn('tx_hash_one', response[1])
        self.assertIn(mock_transaction, response[0])

    def test_validate_transaction(self):
        self.mock_blockchain.find_duplicate_transactions.return_value = False
        self.mock_blockchain.get_balance.return_value = 100
        mock_transaction = Mock(Transaction)
        mock_transaction.tx_hash = "0123456789ABCDEF"
        mock_transaction.verify.return_value = True
        mock_transaction.source = "03dd1e00000000000000000"
        mock_transaction.amount = 95
        mock_transaction.fee = 5

        response = self.subject.validate_transaction(mock_transaction)

        self.assertTrue(response)

    @skip
    def test_calculate_merkle_root(self):
        raise NotImplementedError

