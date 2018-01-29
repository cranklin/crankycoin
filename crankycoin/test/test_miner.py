import unittest
from mock import Mock, patch, PropertyMock
from crankycoin.miner import Miner
from crankycoin.models.block import Block, BlockHeader
from crankycoin.models.transaction import Transaction
from crankycoin.repository.blockchain import Blockchain
from crankycoin.repository.mempool import Mempool


class TestMiner(unittest.TestCase):

    def setUp(self):
        self.mock_blockchain = Mock(Blockchain)
        self.mock_mempool = Mock(Mempool)
        self.HOST = '123.456.789.012'
        self.REWARD_ADDRESS = 'RewardAddress'
        self.MAX_TRANSACTIONS_PER_BLOCK = 10

        self.subject = Miner(self.mock_blockchain, self.mock_mempool)
        self.subject.HOST = self.HOST
        self.subject.MAX_TRANSACTIONS_PER_BLOCK = self.MAX_TRANSACTIONS_PER_BLOCK
        self.subject.REWARD_ADDRESS = self.REWARD_ADDRESS

    def test_mine_block_When_mempool_empty_Returns_block_with_coinbase(self):
        mock_block_header = Mock(BlockHeader)
        mock_block = Mock(Block)
        mock_block.block_header = mock_block_header
        mock_hash_difficulty = PropertyMock(side_effect=[0, 0, 10])

        type(mock_block_header).hash_difficulty = mock_hash_difficulty
        mock_block_header.hash = '0000000000111111111'

        self.mock_blockchain.get_tallest_block_header.return_value = mock_block_header, 0, 125
        self.mock_blockchain.get_coinbase_hash_by_block_hash.return_value = "prevcoinbasehash"
        self.mock_blockchain.get_reward.return_value = 50
        self.mock_blockchain.calculate_hash_difficulty.return_value = 1
        self.mock_mempool.get_unconfirmed_transactions_chunk.return_value = []

        with patch('crankycoin.miner.Block', return_value=mock_block) as patched_block, \
                patch('time.time', return_value=1521946404):
            result = self.subject.mine_block()

            self.assertEqual(self.mock_blockchain.calculate_hash_difficulty.call_count, 3)
            self.assertEqual(result, mock_block)
