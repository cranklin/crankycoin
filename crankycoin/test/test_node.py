import unittest
from mock import patch, Mock, MagicMock, call, PropertyMock
from crankycoin.node import *


class TestNode(unittest.TestCase):

    def test_request_nodes_whenValidNode_thenRequestsNodes(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"full_nodes": ["127.0.0.2", "127.0.0.1", "127.0.0.3"]}
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch("crankycoin.requests.get", return_value=mock_response) as patched_requests:
            node = FullNode("127.0.0.1", "reward_address")

            nodes = node.request_nodes("127.0.0.2", "30013")

            self.assertIsNotNone(nodes)
            self.assertEqual(nodes, {"full_nodes": ["127.0.0.2", "127.0.0.1", "127.0.0.3"]})
            patched_requests.assert_called_once_with('http://127.0.0.2:30013/nodes')

    def test_request_nodes_whenNon200Status_thenReturnsNone(self):
        mock_response = Mock()
        mock_response.status_code = 404
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch("crankycoin.requests.get", return_value=mock_response) as patched_requests:
            node = FullNode("127.0.0.1", "reward_address")

            nodes = node.request_nodes("127.0.0.2", "30013")

            self.assertIsNone(nodes)
            patched_requests.assert_called_once_with('http://127.0.0.2:30013/nodes')

    def test_request_nodes_whenRequestError_thenReturnsNone(self):
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch("crankycoin.requests.get", side_effect=requests.exceptions.RequestException()) as patched_requests:
            node = FullNode("127.0.0.1", "reward_address")

            nodes = node.request_nodes("127.0.0.2", "30013")

            self.assertIsNone(nodes)
            patched_requests.assert_called_once_with('http://127.0.0.2:30013/nodes')

    def test_request_nodes_from_all_SetsFullNodesPropertyOnClass(self):
        nodes_one = {"full_nodes": ["127.0.0.2", "127.0.0.1", "127.0.0.4"]}
        nodes_two = {"full_nodes": ["127.0.0.2", "127.0.0.3", "127.0.0.5"]}
        nodes_three = {"full_nodes": ["127.0.0.1", "127.0.0.3", "127.0.0.4"]}
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch.object(FullNode, 'request_nodes', side_effect=[nodes_one, nodes_two, nodes_three]) as patched_request_nodes:
            node = FullNode("127.0.0.1", "reward_address")
            node.full_nodes = {"127.0.0.1", "127.0.1.1", "127.0.1.2"}

            node.request_nodes_from_all()

            self.assertEqual(node.full_nodes, {"127.0.0.2", "127.0.0.1", "127.0.0.3", "127.0.0.4", "127.0.0.5", "127.0.1.1", "127.0.1.2"})

    def test_broadcast_transaction_thenBroadcastsToAllNodes(self):
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch.object(FullNode, 'request_nodes_from_all') as patched_request_nodes_from_all, \
                patch("crankycoin.time.time", return_value="1508823223") as patched_time_time, \
                patch("crankycoin.requests.post") as patched_requests:

            transaction = Transaction("source", "destination", 0, 0)
            node = FullNode("127.0.0.1", "reward_address")
            node.full_nodes = {"127.0.0.1", "127.0.0.2", "127.0.0.3"}

            node.broadcast_transaction(transaction)

            patched_request_nodes_from_all.assert_called_once()
            patched_requests.assert_has_calls([
                call("http://127.0.0.1:30013/transactions", json={'transaction': '{"amount": 0, "destination": "destination", "fee": 0, "signature": null, "source": "source", "timestamp": 1508823223, "tx_hash": null}'}),
                call("http://127.0.0.2:30013/transactions", json={'transaction': '{"amount": 0, "destination": "destination", "fee": 0, "signature": null, "source": "source", "timestamp": 1508823223, "tx_hash": null}'}),
                call("http://127.0.0.3:30013/transactions", json={'transaction': '{"amount": 0, "destination": "destination", "fee": 0, "signature": null, "source": "source", "timestamp": 1508823223, "tx_hash": null}'})
            ], True)

    def test_broadcast_transaction_whenRequestException_thenFailsGracefully(self):
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch.object(FullNode, 'request_nodes_from_all') as patched_request_nodes_from_all, \
                patch("crankycoin.time.time", return_value="1508823223") as patched_time_time, \
                patch("crankycoin.requests.post", side_effect=requests.exceptions.RequestException()) as patched_requests:

            transaction = Transaction("source", "destination", 0, 0)
            node = FullNode("127.0.0.1", "reward_address")
            node.full_nodes = {"127.0.0.1", "127.0.0.2", "127.0.0.3"}

            node.broadcast_transaction(transaction)

            patched_request_nodes_from_all.assert_called_once()
            patched_requests.assert_has_calls([
                call("http://127.0.0.1:30013/transactions", json={'transaction': '{"amount": 0, "destination": "destination", "fee": 0, "signature": null, "source": "source", "timestamp": 1508823223, "tx_hash": null}'}),
                call("http://127.0.0.2:30013/transactions", json={'transaction': '{"amount": 0, "destination": "destination", "fee": 0, "signature": null, "source": "source", "timestamp": 1508823223, "tx_hash": null}'}),
                call("http://127.0.0.3:30013/transactions", json={'transaction': '{"amount": 0, "destination": "destination", "fee": 0, "signature": null, "source": "source", "timestamp": 1508823223, "tx_hash": null}'})
            ], True)

    def test_request_block_whenIndexIsLatest_thenRequestsLatestBlockFromNode(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = '{"nonce": 12345, "index": 35, "transactions": [], "timestamp": 1234567890, "current_hash": "current_hash", "previous_hash": "previous_hash"}'

        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch("crankycoin.node.Block.current_hash", new_callable=PropertyMock) as patched_block_current_hash, \
                patch("crankycoin.requests.get", return_value=mock_response) as patched_requests:
            patched_block_current_hash.return_value = "current_hash"
            node = FullNode("127.0.0.1", "reward_address")

            block = node.request_block("127.0.0.2", "30013", "latest")

            self.assertIsNotNone(block)
            self.assertEqual(block.index, 35)
            self.assertEqual(block.transactions, [])
            self.assertEqual(block.previous_hash, "previous_hash")
            self.assertEqual(block.current_hash, "current_hash")
            self.assertEqual(block.timestamp, 1234567890)
            self.assertEqual(block.nonce, 12345)
            patched_requests.assert_called_once_with('http://127.0.0.2:30013/block/latest')

    def test_request_block_whenIndexIsNumeric_thenRequestsCorrectBlockFromNode(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = '{"nonce": 12345, "index": 29, "transactions": [], "timestamp": 1234567890, "current_hash": "current_hash", "previous_hash": "previous_hash"}'

        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch("crankycoin.node.Block.current_hash", new_callable=PropertyMock) as patched_block_current_hash, \
                patch("crankycoin.requests.get", return_value=mock_response) as patched_requests:
            patched_block_current_hash.return_value = "current_hash"
            node = FullNode("127.0.0.1", "reward_address")

            block = node.request_block("127.0.0.2", "30013", 29)

            self.assertIsNotNone(block)
            self.assertEqual(block.index, 29)
            self.assertEqual(block.transactions, [])
            self.assertEqual(block.previous_hash, "previous_hash")
            self.assertEqual(block.current_hash, "current_hash")
            self.assertEqual(block.timestamp, 1234567890)
            self.assertEqual(block.nonce, 12345)
            patched_requests.assert_called_once_with('http://127.0.0.2:30013/block/29')

    def test_request_block_whenRequestException_thenReturnsNone(self):
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch("crankycoin.requests.get", side_effect=requests.exceptions.RequestException()) as patched_requests:
            node = FullNode("127.0.0.1", "reward_address")

            block = node.request_block("127.0.0.2", "30013", "latest")

            self.assertIsNone(block)
            patched_requests.assert_called_once_with('http://127.0.0.2:30013/block/latest')

    def test_request_block_from_all_whenIndexIsLatest_thenReturnsLatestBlockFromAll(self):
        block = Mock(Block)
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch.object(FullNode, 'request_block', side_effect=[block, block, block]) as patched_request_block:
            node = FullNode("127.0.0.1", "reward_address")
            node.full_nodes = {"127.0.0.1", "127.0.0.2", "127.0.0.3"}

            blocks = node.request_block_from_all("latest")

            self.assertEqual(blocks, [block, block, block])
            patched_request_block.assert_has_calls([
                call("127.0.0.1", 30013, "latest"),
                call("127.0.0.2", 30013, "latest"),
                call("127.0.0.3", 30013, "latest")
            ], True)

    def test_request_blocks_range(self):
        pass

    def test_request_blockchain(self):
        pass

    def test_mine(self):
        pass

    def test_broadcast_block(self):
        pass

    def test_add_node(self):
        pass

    def test_broadcast_node(self):
        pass

    def test_load_blockchain(self):
        pass

    def test_synchronize(self):
        pass

    def test_generate_ecc_instance(self):
        pass

    def test_get_pubkey(self):
        pass

    def test_get_privkey(self):
        pass

    def test_sign(self):
        pass

    def test_verify(self):
        pass

    def test_get_balance(self):
        pass

    def test_create_transaction(self):
        pass

    def test_calculate_transaction_hash(self):
        pass

    def test_generate_signable_transaction(self):
        pass
