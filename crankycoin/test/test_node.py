import unittest
from mock import patch, Mock, MagicMock, call
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
        transaction = {}
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch.object(FullNode, 'request_nodes_from_all') as patched_request_nodes_from_all, \
                patch("crankycoin.requests.post") as patched_requests:
            node = FullNode("127.0.0.1", "reward_address")
            node.full_nodes = {"127.0.0.1", "127.0.0.2", "127.0.0.3"}

            node.broadcast_transaction(transaction)

            patched_request_nodes_from_all.assert_called_once()
            patched_requests.assert_has_calls([
                call("http://127.0.0.1:30013/transactions", {'transaction': {}}),
                call("http://127.0.0.2:30013/transactions", {'transaction': {}}),
                call("http://127.0.0.3:30013/transactions", {'transaction': {}})
            ], True)

    def test_broadcast_transaction_whenRequestException_thenFailsGracefully(self):
        transaction = {}
        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch.object(FullNode, 'request_nodes_from_all') as patched_request_nodes_from_all, \
                patch("crankycoin.requests.post", side_effect=requests.exceptions.RequestException()) as patched_requests:
            node = FullNode("127.0.0.1", "reward_address")
            node.full_nodes = {"127.0.0.1", "127.0.0.2", "127.0.0.3"}

            node.broadcast_transaction(transaction)

            patched_request_nodes_from_all.assert_called_once()
            patched_requests.assert_has_calls([
                call("http://127.0.0.1:30013/transactions", {'transaction': {}}),
                call("http://127.0.0.2:30013/transactions", {'transaction': {}}),
                call("http://127.0.0.3:30013/transactions", {'transaction': {}})
            ], True)

    def test_request_block_whenIndexIsLatest_thenRequestsLatestBlockFromNode(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = '{"nonce": 12345, "index": 35, "transactions": [], "timestamp": 1234567890, "current_hash": "current_hash", "previous_hash": "previous_hash"}'

        with patch.object(FullNode, '__init__', return_value=None) as patched_init, \
                patch("crankycoin.requests.get", return_value=mock_response) as patched_requests:
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
                patch("crankycoin.requests.get", return_value=mock_response) as patched_requests:
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