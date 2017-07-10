import unittest
from mock import patch, Mock, MagicMock, call
from crankycoin.blockchain import *

class TestBlockchain(unittest.TestCase):

    def test_Blockchain_whenConstructedWithNoBlocks_thenCreatesGenesisBlock(self):
        mock_genesis_block = Mock(Block)

        with patch.object(Blockchain, 'get_genesis_block', return_value=mock_genesis_block) as patched_get_genesis_block, \
                patch.object(Blockchain, 'add_block', return_value=True) as patched_add_block:

            resp = Blockchain()

            patched_get_genesis_block.assert_called_once()
            patched_add_block.assert_called_once_with(mock_genesis_block)

    def test_Blockchain_whenConstructedWithBlocks_thenAddsBlocksWithoutGenesisBlock(self):
        mock_block_one = Mock(Block)
        mock_block_two = Mock(Block)

        with patch.object(Blockchain, 'get_genesis_block') as patched_get_genesis_block, \
                patch.object(Blockchain, 'add_block', return_value=True) as patched_add_block:

            resp = Blockchain([mock_block_one, mock_block_two])

            patched_get_genesis_block.assert_not_called()
            patched_add_block.assert_has_calls([call(mock_block_one), call(mock_block_two)])

    def test_get_genesis_block_whenCalled_thenCreatesAndReturnsBlockWithGenesisTransactions(self):
        genesis_transactions = [{
            'from': '0',
            'timestamp': 0,
            'to': '0442c0fe0050d53426395a046e3c4e6216189666544005567b0b3ed3dcf0151a1ac5b926bdfe93f15ecea3230951ed4151dadab28f2906d0052febea1b7453ce6f',
            'amount': 50,
            'signature': '0',
            'hash': 0
        }]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_block_hash', return_value="mock_block_hash") as patched_calculate_block_hash, \
                patch('crankycoin.blockchain.Block') as patched_Block:
            subject = Blockchain()
            genesis_block = subject.get_genesis_block()

            patched_calculate_block_hash.assert_called_once_with(0, 0, 0, genesis_transactions, 0)
            patched_Block.assert_called_once_with(0, genesis_transactions, 0, 'mock_block_hash', 0, 0)

    def test_calculate_transaction_hash_whenCalledWithSameTransactions_thenReturnsConsistentSha256Hash(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature'
        }
        transaction_three = {
            'to': 'to',
            'timestamp': 0,
            'from': 'from',
            'signature': 'signature',
            'amount': 50,
            'hash': 0
        }

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            transaction_hash_one = subject.calculate_transaction_hash(transaction_one)
            transaction_hash_two = subject.calculate_transaction_hash(transaction_two)
            transaction_hash_three = subject.calculate_transaction_hash(transaction_three)

            self.assertEqual(transaction_hash_one, transaction_hash_two)
            self.assertEqual(transaction_hash_one, transaction_hash_three)
            self.assertEquals(1, len(set([transaction_hash_one, transaction_hash_two, transaction_hash_three])))

    def test_calculate_transaction_hash_whenCalledWithDifferentTransactions_thenReturnsDifferentSha256Hash(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }
        transaction_two = {
            'from': 'different_from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }
        transaction_three = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'different_signature',
            'hash': 0
        }
        transaction_four = {
            'from': 'from',
            'timestamp': 0,
            'to': 'different_to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            transaction_hash_one = subject.calculate_transaction_hash(transaction_one)
            transaction_hash_two = subject.calculate_transaction_hash(transaction_two)
            transaction_hash_three = subject.calculate_transaction_hash(transaction_three)
            transaction_hash_four = subject.calculate_transaction_hash(transaction_four)

            self.assertNotEqual(transaction_hash_one, transaction_hash_two)
            self.assertNotEqual(transaction_hash_one, transaction_hash_three)
            self.assertNotEqual(transaction_one, transaction_hash_four)
            self.assertEquals(4, len(set([transaction_hash_one, transaction_hash_two, transaction_hash_three, transaction_hash_four])))

    def test_calculate_block_hash_whenCalledWithSameBlockData_thenReturnsConsistentSha256Hash(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }
        transaction_two = {
            'from': 'different_from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            block_hash_one = subject.calculate_block_hash(1, "previous_hash", 0, [transaction_one, transaction_two], "1234")
            block_hash_two = subject.calculate_block_hash(1, "previous_hash", 0, [transaction_one, transaction_two], "1234")

            self.assertEqual(block_hash_one, block_hash_two)

    def test_calculate_block_hash_whenCalledWithDifferentBlockData_thenReturnsDifferentSha256Hash(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }
        transaction_two = {
            'from': 'different_from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }
        transaction_three = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'different_signature',
            'hash': 0
        }
        transaction_four = {
            'from': 'from',
            'timestamp': 0,
            'to': 'different_to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            block_hash_one = subject.calculate_block_hash(1, "previous_hash", 0, [transaction_one, transaction_two], "1234")
            block_hash_two = subject.calculate_block_hash(2, "previous_hash", 0, [transaction_one, transaction_two], "1234")
            block_hash_three = subject.calculate_block_hash(1, "different_previous_hash", 0, [transaction_one, transaction_two], "1234")
            block_hash_four = subject.calculate_block_hash(1, "previous_hash", 1, [transaction_one, transaction_two], "1234")
            block_hash_five = subject.calculate_block_hash(1, "previous_hash", 0, [transaction_three, transaction_four], "1234")
            block_hash_six = subject.calculate_block_hash(1, "previous_hash", 0, [transaction_one, transaction_two], "5678")

            self.assertNotEqual(block_hash_one, block_hash_two)
            self.assertNotEqual(block_hash_one, block_hash_three)
            self.assertNotEqual(block_hash_one, block_hash_four)
            self.assertNotEqual(block_hash_one, block_hash_five)
            self.assertNotEqual(block_hash_one, block_hash_six)
            self.assertEquals(6, len(set([block_hash_one, block_hash_two, block_hash_three, block_hash_four, block_hash_five, block_hash_six])))

    def test_check_hash_and_hash_pattern_whenBlockHasValidHashAndPattern_thenReturnsTrue(self):
        mock_block = Mock(Block)
        transaction = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_block_hash', return_value="0000_valid_block_hash") as patched_calculate_block_hash:
            mock_block.current_hash = "0000_valid_block_hash"
            mock_block.index = 35
            mock_block.previous_hash = "0000_valid_previous_hash"
            mock_block.transactions = [transaction]
            mock_block.nonce = 37
            mock_block.timestamp = 12341234
            subject = Blockchain()

            resp = subject._check_hash_and_hash_pattern(mock_block)

            self.assertTrue(resp)

    def test_check_hash_and_hash_pattern_whenBlockHasInvalidHash_thenReturnsFalse(self):
        mock_block = Mock(Block)
        transaction = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_block_hash', return_value="0000_wrong_block_hash") as patched_calculate_block_hash:
            mock_block.current_hash = "0000_valid_block_hash"
            mock_block.index = 35
            mock_block.previous_hash = "0000_valid_previous_hash"
            mock_block.transactions = [transaction]
            mock_block.nonce = 37
            mock_block.timestamp = 12341234
            subject = Blockchain()

            resp = subject._check_hash_and_hash_pattern(mock_block)

            self.assertFalse(resp)

    def test_check_hash_and_hash_pattern_whenBlockHasInvalidPattern_thenReturnsFalse(self):
        mock_block = Mock(Block)
        transaction = {
            'from': 'from',
            'timestamp': 0,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_block_hash', return_value="invalid_block_hash") as patched_calculate_block_hash:
            mock_block.current_hash = "invalid_block_hash"
            mock_block.index = 35
            mock_block.previous_hash = "0000_valid_previous_hash"
            mock_block.transactions = [transaction]
            mock_block.nonce = 37
            mock_block.timestamp = 12341234
            subject = Blockchain()

            resp = subject._check_hash_and_hash_pattern(mock_block)

            self.assertFalse(resp)

    def test_check_index_and_previous_hash_whenBlockHasValidIndexAndPreviousHash_thenReturnsTrue(self):
        mock_block = Mock(Block)
        mock_block.index = 35
        mock_block.previous_hash = "0000_hash_of_block_34"
        mock_latest_block = Mock(Block)
        mock_latest_block.index = 34
        mock_latest_block.current_hash = "0000_hash_of_block_34"

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_latest_block', return_value=mock_latest_block) as patched_get_latest_block:
            subject = Blockchain()
            resp = subject._check_index_and_previous_hash(mock_block)

            self.assertTrue(resp)

    def test_check_index_and_previous_hash_whenBlockHasInValidIndex_thenReturnsFalse(self):
        mock_block = Mock(Block)
        mock_block.index = 35
        mock_block.previous_hash = "0000_hash_of_block_34"
        mock_latest_block = Mock(Block)
        mock_latest_block.index = 33
        mock_latest_block.current_hash = "0000_hash_of_block_34"

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_latest_block', return_value=mock_latest_block) as patched_get_latest_block:
            subject = Blockchain()
            resp = subject._check_index_and_previous_hash(mock_block)

            self.assertFalse(resp)

    def test_check_index_and_previous_hash_whenBlockHasInValidPreviousHash_thenReturnsFalse(self):
        mock_block = Mock(Block)
        mock_block.index = 35
        mock_block.previous_hash = "0000_wrong_hash_of_block_34"
        mock_latest_block = Mock(Block)
        mock_latest_block.index = 34
        mock_latest_block.current_hash = "0000_hash_of_block_34"

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_latest_block', return_value=mock_latest_block) as patched_get_latest_block:
            subject = Blockchain()

            resp = subject._check_index_and_previous_hash(mock_block)

            self.assertFalse(resp)

    def test_check_transactions_and_block_reward_whenValid_thenReturnsTrue(self):
        mock_block = Mock(Block)
        transaction = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': "transaction_hash_one"
        }
        reward_transaction = {
            'from': 0,
            'timestamp': 1498933800,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }
        mock_block.index = 5
        mock_block.transactions = [transaction, reward_transaction]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_transaction_hash', return_value="transaction_hash_one") as patched_calculate_transaction_hash, \
                patch.object(Blockchain, 'find_duplicate_transactions', return_value=False) as patched_find_duplicate_transactions, \
                patch.object(Blockchain, 'verify_signature', return_value=True) as patched_verify_signature, \
                patch.object(Blockchain, 'get_balance', return_value=50) as patched_get_balance, \
                patch.object(Blockchain, 'get_reward', return_value=50) as patched_get_reward:
            subject = Blockchain()

            resp = subject._check_transactions_and_block_reward(mock_block)

            self.assertTrue(resp)

    def test_check_transactions_and_block_reward_whenValidMultipleTransactionsFromSamePayer_thenReturnsTrue(self):
        mock_block = Mock(Block)
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        reward_transaction = {
            'from': 0,
            'timestamp': 1498933800,
            'to': 'to',
            'amount': 50,
            'signature': '0',
            'hash': 0
        }
        mock_block.index = 5
        mock_block.transactions = [transaction_one, transaction_two, reward_transaction]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_transaction_hash', side_effect=["transaction_hash_one", "transaction_hash_two"]) as patched_calculate_transaction_hash, \
                patch.object(Blockchain, 'find_duplicate_transactions', return_value=False) as patched_find_duplicate_transactions, \
                patch.object(Blockchain, 'verify_signature', return_value=True) as patched_verify_signature, \
                patch.object(Blockchain, 'get_balance', return_value=50) as patched_get_balance, \
                patch.object(Blockchain, 'get_reward', return_value=50) as patched_get_reward:
            subject = Blockchain()

            resp = subject._check_transactions_and_block_reward(mock_block)

            self.assertTrue(resp)

    def test_check_transactions_and_block_reward_whenInvalidHash_thenReturnsFalse(self):
        mock_block = Mock(Block)
        transaction = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': "invalid_transaction_hash_one"
        }
        reward_transaction = {
            'from': 0,
            'timestamp': 1498933800,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }
        mock_block.index = 2
        mock_block.transactions = [transaction, reward_transaction]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_transaction_hash', return_value="transaction_hash_one") as patched_calculate_transaction_hash, \
                patch.object(Blockchain, 'find_duplicate_transactions', return_value=False) as patched_find_duplicate_transactions, \
                patch.object(Blockchain, 'get_balance', return_value=50) as patched_get_balance, \
                patch.object(Blockchain, 'get_reward', return_value=50) as patched_get_reward:
            subject = Blockchain()

            resp = subject._check_transactions_and_block_reward(mock_block)

            self.assertFalse(resp)

    def test_check_transactions_and_block_reward_whenDuplicateTransaction_thenReturnsFalse(self):
        mock_block = Mock(Block)
        transaction = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': "transaction_hash_one"
        }
        reward_transaction = {
            'from': 0,
            'timestamp': 1498933800,
            'to': 'to',
            'amount': 50,
            'signature': 'signature',
            'hash': 0
        }
        mock_block.index = 2
        mock_block.transactions = [transaction, reward_transaction]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_transaction_hash', return_value="transaction_hash_one") as patched_calculate_transaction_hash, \
                patch.object(Blockchain, 'find_duplicate_transactions', return_value=True) as patched_find_duplicate_transactions, \
                patch.object(Blockchain, 'get_balance', return_value=50) as patched_get_balance, \
                patch.object(Blockchain, 'get_reward', return_value=50) as patched_get_reward:
            subject = Blockchain()

            resp = subject._check_transactions_and_block_reward(mock_block)

            self.assertFalse(resp)

    def test_check_transactions_and_block_reward_whenInsufficientBalanceFromPayer_thenReturnsFalse(self):
        mock_block = Mock(Block)
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        reward_transaction = {
            'from': 0,
            'timestamp': 1498933800,
            'to': 'to',
            'amount': 50,
            'signature': '0',
            'hash': 0
        }
        mock_block.index = 5
        mock_block.transactions = [transaction_one, transaction_two, reward_transaction]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_transaction_hash', side_effect=["transaction_hash_one", "transaction_hash_two"]) as patched_calculate_transaction_hash, \
                patch.object(Blockchain, 'find_duplicate_transactions', return_value=False) as patched_find_duplicate_transactions, \
                patch.object(Blockchain, 'verify_signature', return_value=True) as patched_verify_signature, \
                patch.object(Blockchain, 'get_balance', return_value=49) as patched_get_balance, \
                patch.object(Blockchain, 'get_reward', return_value=50) as patched_get_reward:
            subject = Blockchain()

            resp = subject._check_transactions_and_block_reward(mock_block)

            self.assertFalse(resp)

    def test_check_transactions_and_block_reward_whenInvalidBlockReward_thenReturnsFalse(self):
        mock_block = Mock(Block)
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        reward_transaction = {
            'from': 0,
            'timestamp': 1498933800,
            'to': 'to',
            'amount': 51,
            'signature': '0',
            'hash': 0
        }
        mock_block.index = 5
        mock_block.transactions = [transaction_one, transaction_two, reward_transaction]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_transaction_hash', side_effect=["transaction_hash_one", "transaction_hash_two"]) as patched_calculate_transaction_hash, \
                patch.object(Blockchain, 'find_duplicate_transactions', return_value=False) as patched_find_duplicate_transactions, \
                patch.object(Blockchain, 'verify_signature', return_value=True) as patched_verify_signature, \
                patch.object(Blockchain, 'get_balance', return_value=50) as patched_get_balance, \
                patch.object(Blockchain, 'get_reward', return_value=50) as patched_get_reward:
            subject = Blockchain()

            resp = subject._check_transactions_and_block_reward(mock_block)

            self.assertFalse(resp)

    def test_check_transactions_and_block_reward_whenInvalidBlockRewardSource_thenReturnsFalse(self):
        mock_block = Mock(Block)
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        reward_transaction = {
            'from': 'a different source',
            'timestamp': 1498933800,
            'to': 'to',
            'amount': 50,
            'signature': '0',
            'hash': 0
        }
        mock_block.index = 5
        mock_block.transactions = [transaction_one, transaction_two, reward_transaction]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'calculate_transaction_hash', side_effect=["transaction_hash_one", "transaction_hash_two"]) as patched_calculate_transaction_hash, \
                patch.object(Blockchain, 'find_duplicate_transactions', return_value=False) as patched_find_duplicate_transactions, \
                patch.object(Blockchain, 'verify_signature', return_value=True) as patched_verify_signature, \
                patch.object(Blockchain, 'get_balance', return_value=50) as patched_get_balance, \
                patch.object(Blockchain, 'get_reward', return_value=50) as patched_get_reward:
            subject = Blockchain()

            resp = subject._check_transactions_and_block_reward(mock_block)

            self.assertFalse(resp)

    def test_validate_block_whenValid_returnsTrue(self):
        mock_block = Mock(Block)
        mock_block.index = 51000
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, '_check_hash_and_hash_pattern', return_value=True) as patched_check_hash_and_hash_pattern, \
                patch.object(Blockchain, '_check_index_and_previous_hash', return_value=True) as patched_check_index_and_previous_hash, \
                patch.object(Blockchain, '_check_transactions_and_block_reward', return_value=True) as patched_check_transactions_and_block_reward:
            subject = Blockchain()

            resp = subject.validate_block(mock_block)

            self.assertTrue(resp)

    def test_validate_block_whenValidGenesisBlock_returnsTrue(self):
        genesis_block = Mock(Block)
        genesis_block.index = 0
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_genesis_block', return_value=genesis_block) as patched_get_genesis_block:
            subject = Blockchain()

            resp = subject.validate_block(genesis_block)

            self.assertTrue(resp)

    def test_validate_block_whenInvalidGenesisBlock_raisesGenesisBlockMismatchException(self):
        invalid_genesis_block = Mock(Block)
        invalid_genesis_block.index = 0
        genesis_block = Mock(Block)
        genesis_block.index = 0
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_genesis_block', return_value=genesis_block) as patched_get_genesis_block:
            subject = Blockchain()

            with self.assertRaises(GenesisBlockMismatch):
                subject.validate_block(invalid_genesis_block)

    def test_validate_block_whenInvalidHash_raisesInvalidHashException(self):
        mock_block = Mock(Block)
        mock_block.index = 51000
        mock_block.current_hash = "invalid_hash"
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, '_check_hash_and_hash_pattern', return_value=False) as patched_check_hash_and_hash_pattern:
            subject = Blockchain()

            with self.assertRaises(InvalidHash):
                subject.validate_block(mock_block)

    def test_validate_block_whenInvalidIncompatibleBlock_raisesChainContinuityErrorException(self):
        mock_block = Mock(Block)
        mock_block.index = 51000
        mock_block.current_hash = "0000_current_hash"
        mock_block.previous_hash = "0000_previous_hash"
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, '_check_hash_and_hash_pattern', return_value=True) as patched_check_hash_and_hash_pattern, \
                patch.object(Blockchain, '_check_index_and_previous_hash', return_value=False) as patched_check_index_and_previous_hash:
            subject = Blockchain()

            with self.assertRaises(ChainContinuityError):
                subject.validate_block(mock_block)

    def test_validate_block_whenInvalidTransactions_raisesInvalidTransactionsException(self):
        mock_block = Mock(Block)
        mock_block.index = 51000
        mock_block.current_hash = "0000_current_hash"
        mock_block.previous_hash = "0000_previous_hash"
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, '_check_hash_and_hash_pattern', return_value=True) as patched_check_hash_and_hash_pattern, \
                patch.object(Blockchain, '_check_index_and_previous_hash', return_value=True) as patched_check_index_and_previous_hash, \
                patch.object(Blockchain, '_check_transactions_and_block_reward', return_value=False) as patched__check_transactions_and_block_reward:
            subject = Blockchain()

            with self.assertRaises(InvalidTransactions):
                subject.validate_block(mock_block)

    def test_alter_chain_whenNewChainIsLonger_thenReplacesChainAndReturnsTrue(self):
        # difficult to unit test; Likely code smell
        mock_block_one = Mock(Block, name="mock_block_one")
        mock_block_one.index = 0
        mock_block_two = Mock(Block, name="mock_block_two")
        mock_block_two.index = 1
        mock_block_three = Mock(Block, name="mock_block_three")
        mock_block_three.index = 2
        mock_block_four = Mock(Block, name="mock_block_four")
        mock_block_four.index = 3
        mock_block_five = Mock(Block, name="mock_block_five")
        mock_block_five.index = 4

        mock_forked_block_four = Mock(Block, name="mock_forked_block_four")
        mock_forked_block_four.index = 3
        mock_forked_block_five = Mock(Block, name="mock_forked_block_five")
        mock_forked_block_five.index = 4
        mock_forked_block_six = Mock(Block, name="mock_forked_block_six")
        mock_forked_block_six.index = 5

        mock_blocks = [
            mock_block_one,
            mock_block_two,
            mock_block_three,
            mock_block_four,
            mock_block_five
        ]
        mock_forked_blocks = [
            mock_forked_block_four,
            mock_forked_block_five,
            mock_forked_block_six
        ]
        mock_altered_blocks = [
            mock_block_one,
            mock_block_two,
            mock_block_three,
            mock_forked_block_four,
            mock_forked_block_five,
            mock_forked_block_six
        ]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_size', side_effect=[6, 5]) as patched_get_size:
            subject = Blockchain()
            subject.blocks = mock_blocks
            subject.blocks_lock = threading.Lock()

            resp = subject.alter_chain(mock_forked_blocks)

            self.assertTrue(resp)
            self.assertEqual(subject.blocks, mock_altered_blocks)

    def test_alter_chain_whenNewChainIsNotLonger_thenDoesNotAlterChainAndReturnsFalse(self):
        # difficult to unit test; Likely code smell
        mock_block_one = Mock(Block, name="mock_block_one")
        mock_block_one.index = 0
        mock_block_two = Mock(Block, name="mock_block_two")
        mock_block_two.index = 1
        mock_block_three = Mock(Block, name="mock_block_three")
        mock_block_three.index = 2
        mock_block_four = Mock(Block, name="mock_block_four")
        mock_block_four.index = 3
        mock_block_five = Mock(Block, name="mock_block_five")
        mock_block_five.index = 4

        mock_forked_block_four = Mock(Block, name="mock_forked_block_four")
        mock_forked_block_four.index = 3
        mock_forked_block_five = Mock(Block, name="mock_forked_block_five")
        mock_forked_block_five.index = 4

        mock_blocks = [
            mock_block_one,
            mock_block_two,
            mock_block_three,
            mock_block_four,
            mock_block_five
        ]
        mock_forked_blocks = [
            mock_forked_block_four,
            mock_forked_block_five
        ]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_size', return_value=5) as patched_get_size:
            subject = Blockchain()
            subject.blocks = mock_blocks

            resp = subject.alter_chain(mock_forked_blocks)

            self.assertFalse(resp)
            self.assertEqual(subject.blocks, mock_blocks)

    def test_add_block_whenValidBlock_thenAddsBlockAndReturnsTrue(self):
        mock_block = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'validate_block', return_value=True) as patched_validate_block:
            subject = Blockchain()
            mock_blocks = Mock()
            subject.blocks = mock_blocks
            subject.blocks_lock = threading.Lock()

            resp = subject.add_block(mock_block)

            self.assertTrue(resp)
            mock_blocks.append.assert_called_once_with(mock_block)

    def test_add_block_whenInvalidBlock_thenDoesNotAddBlockAndReturnsFalse(self):
        mock_block = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'validate_block', return_value=False) as patched_validate_block:
            subject = Blockchain()
            mock_blocks = Mock()
            subject.blocks = mock_blocks

            resp = subject.add_block(mock_block)

            self.assertFalse(resp)
            mock_blocks.append.assert_not_called()

    def test_mine_block_whenNoUnconfirmedTransactions_thenReturnsNone(self):
        latest_block = Mock(Block)
        latest_block.index = 35
        latest_block.current_hash = "latest_block_hash"
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_latest_block', return_value=latest_block) as patched_get_latest_block, \
                patch.object(Blockchain, 'pop_next_unconfirmed_transaction', return_value=None) as patched_pop_next_unconfirmed_transaction:
            subject = Blockchain()

            resp = subject.mine_block("reward_address")

            self.assertIsNone(resp)
            patched_pop_next_unconfirmed_transaction.assert_called_once()

    def test_mine_block_whenOneTransaction_andIncorrectTransactionHash_thenReturnsNone(self):
        transaction = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature',
            'hash': 'incorrect_transaction_hash'
        }
        latest_block = Mock(Block)
        latest_block.index = 35
        latest_block.current_hash = "latest_block_hash"
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_latest_block', return_value=latest_block) as patched_get_latest_block, \
 \
                patch.object(Blockchain, 'pop_next_unconfirmed_transaction', side_effect=[transaction, None]) as patched_pop_next_unconfirmed_transaction, \
                patch.object(Blockchain, 'calculate_transaction_hash', return_value="transaction_hash") as patched_calculate_transaction_hash:
            subject = Blockchain()

            resp = subject.mine_block("reward_address")

            self.assertIsNone(resp)
            self.assertEqual(patched_pop_next_unconfirmed_transaction.call_count, 2)
            patched_calculate_transaction_hash.assert_called_once_with(transaction)

    def test_mine_block_whenOneDuplicateTransaction_thenReturnsNone(self):
        transaction = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature',
            'hash': 'transaction_hash'
        }
        block_id_with_same_transaction = 38
        latest_block = Mock(Block)
        latest_block.index = 35
        latest_block.current_hash = "latest_block_hash"
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'get_latest_block', return_value=latest_block) as patched_get_latest_block, \
 \
                patch.object(Blockchain, 'pop_next_unconfirmed_transaction', side_effect=[transaction, None]) as patched_pop_next_unconfirmed_transaction, \
                patch.object(Blockchain, 'calculate_transaction_hash', return_value="transaction_hash") as patched_calculate_transaction_hash, \
                patch.object(Blockchain, 'find_duplicate_transactions', return_value=block_id_with_same_transaction) as patched_find_duplicate_transactions:
            subject = Blockchain()

            resp = subject.mine_block("reward_address")

            self.assertIsNone(resp)
            self.assertEqual(patched_pop_next_unconfirmed_transaction.call_count, 2)
            patched_calculate_transaction_hash.assert_called_once_with(transaction)
            patched_find_duplicate_transactions.asssert_called_once_with("transaction_hash")

    def test_mine_block_whenDuplicateTransactionsInUnconfirmedPool_thenMinesOneOfThemAndReturnsBlock(self):
        # this is difficult to test; likely code smell
        transaction = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature',
            'hash': 'transaction_hash'
        }
        duplicate_transaction = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 25,
            'signature': 'signature',
            'hash': 'transaction_hash'
        }
        latest_block = Mock(Block)
        latest_block.index = 31
        latest_block.current_hash = "latest_block_current_hash"

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'pop_next_unconfirmed_transaction', side_effect=[transaction, duplicate_transaction, None]) as patched_pop_next_unconfirmed_transaction, \
                patch.object(Blockchain, 'calculate_transaction_hash', side_effect=["transaction_hash", "transaction_hash", "reward_transaction_hash"]) as patched_calculate_transaction_hash, \
                patch.object(Blockchain, 'find_duplicate_transactions', return_value=False) as patched_find_duplicate_transactions, \
                patch.object(Blockchain, 'verify_signature', return_value=True) as patched_verify_signature, \
                patch.object(Blockchain, 'get_latest_block', return_value=latest_block) as patched_get_latest_block, \
                patch.object(Blockchain, 'get_reward', return_value=50) as patched_get_reward, \
                patch.object(Blockchain, 'calculate_block_hash', side_effect=["bad_hash", "bad_hash", "0000_good_hash", "0000_good_hash"]) as patched_calculate_block_hash, \
                patch("crankycoin.datetime.datetime") as patched_datetime:
            subject = Blockchain()
            mock_utcnow = Mock()
            mock_utcnow.isoformat.return_value = 5555555555
            patched_datetime.utcnow.return_value = mock_utcnow

            resp = subject.mine_block("reward_address")

            self.assertIsInstance(resp, Block)
            self.assertEqual(len(resp.transactions), 2)
            self.assertEqual(patched_pop_next_unconfirmed_transaction.call_count, 3)
            self.assertEqual(patched_calculate_transaction_hash.call_count, 3)
            patched_find_duplicate_transactions.assert_called_once_with("transaction_hash")
            patched_verify_signature.assert_called_once_with("signature", "from:to:25:1498923800", "from")
            self.assertEqual(patched_calculate_block_hash.call_count, 4)

    def test_get_transaction_history_whenAddressHasTransactions_returnHistory(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'address',
            'amount': 1,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'address',
            'amount': 3,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        transaction_three = {
            'from': 'from',
            'timestamp': 1498925800,
            'to': 'to',
            'amount': 5,
            'signature': 'signature_three',
            'hash': "transaction_hash_three"
        }
        transaction_four = {
            'from': 'from',
            'timestamp': 1498926800,
            'to': 'address',
            'amount': 7,
            'signature': 'signature_four',
            'hash': "transaction_hash_four"
        }
        transaction_five = {
            'from': 'address',
            'timestamp': 1498927800,
            'to': 'to',
            'amount': 11,
            'signature': 'signature_five',
            'hash': "transaction_hash_five"
        }
        transaction_six = {
            'from': 'from',
            'timestamp': 1498928800,
            'to': 'to',
            'amount': 13,
            'signature': 'signature_six',
            'hash': "transaction_hash_six"
        }
        block_one = Mock(Block)
        block_one.transactions = [transaction_one, transaction_two]
        block_two = Mock(Block)
        block_two.transactions = [transaction_three, transaction_four]
        block_three = Mock(Block)
        block_three.transactions = [transaction_five, transaction_six]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [block_one, block_two, block_three]

            transaction_history = subject.get_transaction_history('address')

            self.assertEqual(len(transaction_history), 4)
            self.assertEqual(transaction_history, [transaction_one, transaction_two, transaction_four, transaction_five])

    def test_get_transaction_history_whenAddressHasNoTransactions_returnEmptyList(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 1,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'to',
            'amount': 3,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        transaction_three = {
            'from': 'from',
            'timestamp': 1498925800,
            'to': 'to',
            'amount': 5,
            'signature': 'signature_three',
            'hash': "transaction_hash_three"
        }
        transaction_four = {
            'from': 'from',
            'timestamp': 1498926800,
            'to': 'to',
            'amount': 7,
            'signature': 'signature_four',
            'hash': "transaction_hash_four"
        }
        transaction_five = {
            'from': 'from',
            'timestamp': 1498927800,
            'to': 'to',
            'amount': 11,
            'signature': 'signature_five',
            'hash': "transaction_hash_five"
        }
        transaction_six = {
            'from': 'from',
            'timestamp': 1498928800,
            'to': 'to',
            'amount': 13,
            'signature': 'signature_six',
            'hash': "transaction_hash_six"
        }
        block_one = Mock(Block)
        block_one.transactions = [transaction_one, transaction_two]
        block_two = Mock(Block)
        block_two.transactions = [transaction_three, transaction_four]
        block_three = Mock(Block)
        block_three.transactions = [transaction_five, transaction_six]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [block_one, block_two, block_three]

            transaction_history = subject.get_transaction_history('address')

            self.assertEqual(len(transaction_history), 0)

    def test_get_balance_whenAddressHasTransactions_returnBalance(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'address',
            'amount': 1,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'address',
            'amount': 3,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        transaction_three = {
            'from': 'from',
            'timestamp': 1498925800,
            'to': 'to',
            'amount': 5,
            'signature': 'signature_three',
            'hash': "transaction_hash_three"
        }
        transaction_four = {
            'from': 'from',
            'timestamp': 1498926800,
            'to': 'address',
            'amount': 7,
            'signature': 'signature_four',
            'hash': "transaction_hash_four"
        }
        transaction_five = {
            'from': 'address',
            'timestamp': 1498927800,
            'to': 'to',
            'amount': .11,
            'signature': 'signature_fave',
            'hash': "transaction_hash_five"
        }
        transaction_six = {
            'from': 'address',
            'timestamp': 1498928800,
            'to': 'to',
            'amount': .13,
            'signature': 'signature_six',
            'hash': "transaction_hash_six"
        }
        block_one = Mock(Block)
        block_one.transactions = [transaction_one, transaction_two]
        block_two = Mock(Block)
        block_two.transactions = [transaction_three, transaction_four]
        block_three = Mock(Block)
        block_three.transactions = [transaction_five, transaction_six]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [block_one, block_two, block_three]

            balance = subject.get_balance('address')

            self.assertEqual(balance, 10.76)

    def test_get_balance_whenAddressHasNoTransactions_returnZeroBalance(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 1,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'to',
            'amount': 3,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        transaction_three = {
            'from': 'from',
            'timestamp': 1498925800,
            'to': 'to',
            'amount': 5,
            'signature': 'signature_three',
            'hash': "transaction_hash_three"
        }
        block_one = Mock(Block)
        block_one.transactions = [transaction_one]
        block_two = Mock(Block)
        block_two.transactions = [transaction_two]
        block_three = Mock(Block)
        block_three.transactions = [transaction_three]

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [block_one, block_two, block_three]

            balance = subject.get_balance('address')

            self.assertEqual(balance, 0)

    def test_find_duplicate_transactions_WhenHashExists_thenReturnBlockIndex(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 1,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'to',
            'amount': 3,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        transaction_three = {
            'from': 'from',
            'timestamp': 1498925800,
            'to': 'to',
            'amount': 5,
            'signature': 'signature_three',
            'hash': "transaction_hash_three"
        }
        transaction_four = {
            'from': 'from',
            'timestamp': 1498926800,
            'to': 'address',
            'amount': 7,
            'signature': 'signature_four',
            'hash': "transaction_hash_four"
        }
        block_one = Mock(Block)
        block_one.transactions = [transaction_one]
        block_one.index = 0
        block_two = Mock(Block)
        block_two.transactions = [transaction_two]
        block_two.index = 1
        block_three = Mock(Block)
        block_three.transactions = [transaction_three, transaction_four]
        block_three.index = 2

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [block_one, block_two, block_three]

            resp = subject.find_duplicate_transactions("transaction_hash_four")

            self.assertEqual(resp, block_three.index)

    def test_find_duplicate_transactions_WhenHashNotFound_thenReturnFalse(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 1,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'to',
            'amount': 3,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        transaction_three = {
            'from': 'from',
            'timestamp': 1498925800,
            'to': 'to',
            'amount': 5,
            'signature': 'signature_three',
            'hash': "transaction_hash_three"
        }
        transaction_four = {
            'from': 'from',
            'timestamp': 1498926800,
            'to': 'address',
            'amount': 7,
            'signature': 'signature_four',
            'hash': "transaction_hash_four"
        }
        block_one = Mock(Block)
        block_one.transactions = [transaction_one]
        block_one.index = 0
        block_two = Mock(Block)
        block_two.transactions = [transaction_two]
        block_two.index = 1
        block_three = Mock(Block)
        block_three.transactions = [transaction_three, transaction_four]
        block_three.index = 2

        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [block_one, block_two, block_three]

            resp = subject.find_duplicate_transactions("transaction_hash_five")

            self.assertFalse(resp)

    def test_validate_chain_whenAllBlocksValid_thenReturnTrue(self):
        mock_block = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'validate_block', return_value=True) as patched_validate_block:
            subject = Blockchain()
            subject.blocks = [mock_block, mock_block, mock_block]

            resp = subject.validate_chain()

            self.assertTrue(resp)

    def test_validate_chain_whenInvalidBlockPresent_thenRaiseException(self):
        mock_block = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init, \
                patch.object(Blockchain, 'validate_block', side_effect=InvalidHash(2, "Invalid Hash")) as patched_validate_block:
            subject = Blockchain()
            subject.blocks = [mock_block, mock_block, mock_block]

            with self.assertRaises(InvalidHash):
                subject.validate_chain()

    def test_get_reward_whenGivenIndex_thenReturnsProperReward(self):
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()

            reward_one = subject.get_reward(0)
            reward_two = subject.get_reward(999)
            reward_three = subject.get_reward(1000)
            reward_four = subject.get_reward(1999)
            reward_five = subject.get_reward(2000)
            reward_six = subject.get_reward(3000)
            reward_seven = subject.get_reward(4000)
            reward_eight = subject.get_reward(5000)
            reward_nine = subject.get_reward(5999)
            reward_ten = subject.get_reward(6000)

            self.assertEqual(reward_one, 50)
            self.assertEqual(reward_two, 50)
            self.assertEqual(reward_three, 25)
            self.assertEqual(reward_four, 25)
            self.assertEqual(reward_five, 12)
            self.assertEqual(reward_six, 6)
            self.assertEqual(reward_seven, 3)
            self.assertEqual(reward_eight, 1)
            self.assertEqual(reward_nine, 1)
            self.assertEqual(reward_ten, 0)

    def test_get_size_whenBlocksExist_thenReturnsProperLength(self):
        mock_block = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [mock_block, mock_block, mock_block]

            size = subject.get_size()

            self.assertEqual(3, size)

    def test_get_size_whenNoBlocksExist_thenReturnsZero(self):
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()

            size = subject.get_size()

            self.assertEqual(0, size)

    def test_get_latest_block_whenBlocksExist_thenReturnLatestBlock(self):
        mock_block = Mock(Block)
        latest_block = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [mock_block, mock_block, mock_block, latest_block]

            block = subject.get_latest_block()

            self.assertEqual(block, latest_block)

    def test_get_latest_block_whenNoBlocksExist_thenReturnNone(self):
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()

            block = subject.get_latest_block()

            self.assertIsNone(block)

    def test_get_block_by_index_whenBlockExists_thenReturnCorrectBlock(self):
        mock_block_one = Mock(Block)
        mock_block_two = Mock(Block)
        mock_block_three = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [mock_block_one, mock_block_two, mock_block_three]

            block = subject.get_block_by_index(1)

            self.assertEqual(block, mock_block_two)

    def test_get_block_by_index_whenBlockDoesNotExist_thenReturnNone(self):
        mock_block_one = Mock(Block)
        mock_block_two = Mock(Block)
        mock_block_three = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [mock_block_one, mock_block_two, mock_block_three]

            block = subject.get_block_by_index(3)

            self.assertIsNone(block)

    def test_get_blocks_range_whenBlocksExists_thenReturnCorrectBlocks(self):
        mock_block_one = Mock(Block)
        mock_block_two = Mock(Block)
        mock_block_three = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [mock_block_one, mock_block_two, mock_block_three]

            blocks = subject.get_blocks_range(0, 2)

            self.assertEqual(blocks, subject.blocks)

            blocks = subject.get_blocks_range(0, 1)

            self.assertEqual(blocks, [mock_block_one, mock_block_two])

    def test_get_blocks_range_whenBlocksOutOfRange_thenReturnsListOfBlocksWithinRange(self):
        mock_block_one = Mock(Block)
        mock_block_two = Mock(Block)
        mock_block_three = Mock(Block)
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.blocks = [mock_block_one, mock_block_two, mock_block_three]

            blocks = subject.get_blocks_range(4, 6)

            self.assertEqual(blocks, [])

            blocks = subject.get_blocks_range(1, 5)

            self.assertEqual(blocks, [mock_block_two, mock_block_three])

    def test_pop_next_unconfirmed_transaction_whenTransactionsExist_thenPopsAndReturnsFirstTransaction(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 1,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        transaction_two = {
            'from': 'from',
            'timestamp': 1498924800,
            'to': 'to',
            'amount': 3,
            'signature': 'signature_two',
            'hash': "transaction_hash_two"
        }
        transaction_three = {
            'from': 'from',
            'timestamp': 1498925800,
            'to': 'to',
            'amount': 5,
            'signature': 'signature_three',
            'hash': "transaction_hash_three"
        }
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.unconfirmed_transactions_lock = threading.Lock()
            subject.unconfirmed_transactions = [transaction_one, transaction_two, transaction_three]

            transaction = subject.pop_next_unconfirmed_transaction()

            self.assertEqual(transaction, transaction_one)
            self.assertEqual(len(subject.unconfirmed_transactions), 2)
            self.assertTrue(transaction_one not in subject.unconfirmed_transactions)

    def test_pop_next_unconfirmed_transaction_whenNoTransactionsExist_thenReturnsNone(self):
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.unconfirmed_transactions_lock = threading.Lock()

            transaction = subject.pop_next_unconfirmed_transaction()

            self.assertIsNone(transaction)

    def test_push_unconfirmed_transaction_thenPushesTransactionAndReturnsNone(self):
        transaction_one = {
            'from': 'from',
            'timestamp': 1498923800,
            'to': 'to',
            'amount': 1,
            'signature': 'signature_one',
            'hash': "transaction_hash_one"
        }
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()
            subject.unconfirmed_transactions_lock = threading.Lock()

            resp = subject.push_unconfirmed_transaction(transaction_one)

            self.assertTrue(resp)
            self.assertEqual(len(subject.unconfirmed_transactions), 1)
            self.assertTrue(transaction_one in subject.unconfirmed_transactions)

    def test_verify_signature_whenSignatureAndMessageAndPublicKeyMatch_thenReturnsTrue(self):
        signature = '304502202d009c9b97385189d23600ae480435ea5b68786dbdba184c80e0fb6e58d8c5520221009c25f5cdf659f33ce04f683e14f355b3db5524a289feb9efa4c6879342a81648'
        message = 'hello world'
        public_key = '04496ee863ef587f55b911987c0b0e88b73e840440b834c50ff774677dde49468dafe07868452635e986c35b62244b4739a8db5e27750ff172a9e52ea7278e93c6'
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()

            resp = subject.verify_signature(
                signature,
                message,
                public_key
            )

            self.assertTrue(resp)

    def test_verify_signature_whenSignatureAndMessageAndPublicKeyMisMatch_thenReturnsFalse(self):
        signature = '304502202d009c9b97385189d23600ae480435ea5b68786dbdba184c80e0fb6e58d8c5520221009c25f5cdf659f33ce04f683e14f355b3db5524a289feb9efa4c6879342a81648'
        message = 'invalid message'
        public_key = '04496ee863ef587f55b911987c0b0e88b73e840440b834c50ff774677dde49468dafe07868452635e986c35b62244b4739a8db5e27750ff172a9e52ea7278e93c6'
        with patch.object(Blockchain, '__init__', return_value=None) as patched_init:
            subject = Blockchain()

            resp = subject.verify_signature(
                signature,
                message,
                public_key
            )

            self.assertFalse(resp)
