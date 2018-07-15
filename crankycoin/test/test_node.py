import unittest

from mock import patch, Mock, call

from crankycoin.node import NodeMixin, FullNode
from crankycoin.repository.blockchain import Blockchain
from crankycoin.repository.mempool import Mempool
from crankycoin.repository.peers import Peers
from crankycoin.services.api_client import ApiClient
from crankycoin.services.validator import Validator


class TestNode(unittest.TestCase):

    def setUp(self):
        self.mock_peers = Mock(Peers)
        self.mock_api_client = Mock(ApiClient)
        self.mock_validator = Mock(Validator)
        self.mock_blockchain = Mock(Blockchain)
        self.mock_mempool = Mock(Mempool)
        self.HOST = '123.456.789.012'
        self.WORKER_PROCESSES = 3

        self.subject = FullNode(self.mock_peers, self.mock_api_client, self.mock_blockchain, self.mock_mempool,
                                self.mock_validator)
        self.subject.HOST = self.HOST
        self.subject.WORKER_PROCESSES = self.WORKER_PROCESSES

    def test_check_peers_Calls_check_peers_full(self):
        mock_discovered_peers = Mock()

        with patch.object(NodeMixin, 'discover_peers', return_value=mock_discovered_peers) as patched_find_known_peers:
            self.subject.check_peers()

        expected_calls = [call.check_peers_full(self.HOST, mock_discovered_peers)]
        self.assertEqual(self.mock_api_client.method_calls, expected_calls)
        patched_find_known_peers.assert_called_once_with()

    def test_discover_peers_Returns_discovered_peers(self):
        self.mock_peers.get_all_peers.return_value = ['111.222.333.444', '222.333.444.555']
        self.mock_api_client.request_nodes.return_value = {"full_nodes": ['333.444.555.777', '444.555.777.888']}

        result = self.subject.discover_peers()

        expected_request_nodes_calls = [call.request_nodes('111.222.333.444', 30013),
                                        call.request_nodes('222.333.444.555', 30013)]
        self.assertEqual(self.mock_api_client.method_calls, expected_request_nodes_calls)
        self.assertEqual(len(result), 4)
        self.assertEqual(set(result), {'111.222.333.444', '222.333.444.555', '333.444.555.777', '444.555.777.888'})

    def test_discover_peers_When_no_new_peers_Returns_known_peers(self):
        self.mock_peers.get_all_peers.return_value = ['111.222.333.444', '222.333.444.555']
        self.mock_api_client.request_nodes.return_value = {"full_nodes": []}

        result = self.subject.discover_peers()

        expected_request_nodes_calls = [call.request_nodes('111.222.333.444', 30013),
                                        call.request_nodes('222.333.444.555', 30013)]
        self.assertEqual(self.mock_api_client.method_calls, expected_request_nodes_calls)
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result), {'111.222.333.444', '222.333.444.555'})

    def test_discover_peers_When_new_peers_none_Returns_known_peers(self):
        self.mock_peers.get_all_peers.return_value = ['111.222.333.444', '222.333.444.555']
        self.mock_api_client.request_nodes.return_value = None

        result = self.subject.discover_peers()

        expected_request_nodes_calls = [call.request_nodes('111.222.333.444', 30013),
                                        call.request_nodes('222.333.444.555', 30013)]
        self.assertEqual(self.mock_api_client.method_calls, expected_request_nodes_calls)
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result), {'111.222.333.444', '222.333.444.555'})
