from unittest import TestCase, skip
from mock import Mock, patch

from crankycoin import config
from crankycoin.repository.peers import Peers
from crankycoin.services.api_client import ApiClient, requests


class TestApiClient(TestCase):

    def setUp(self):
        self.mock_peers = Mock(Peers)
        self.subject = ApiClient(self.mock_peers)
        self.node = "1.2.3.4"
        self.port = 30013

    def test_request_nodes_Returns_nodes(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_peers
        with patch.object(requests, 'get', return_value=mock_response) as patched_requests:
            response = self.subject.request_nodes(self.node, self.port)
        self.assertEqual(response, self.mock_peers)

    def test_request_nodes_When_status_code_not_200_Returns_none(self):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = self.mock_peers
        with patch.object(requests, 'get', return_value=mock_response) as patched_requests:
            response = self.subject.request_nodes(self.node, self.port)
        self.assertIsNone(response)

    def test_ping_status_Returns_status(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = config['network']
        with patch.object(requests, 'get', return_value=mock_response) as patched_requests:
            response = self.subject.ping_status(self.node)
        self.assertTrue(response)

    def test_ping_status_When_config_mismatch_Returns_false(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = dict()
        with patch.object(requests, 'get', return_value=mock_response) as patched_requests:
            response = self.subject.ping_status(self.node)
        self.assertFalse(response)

    def test_request_height_Returns_height(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'height': 125}
        with patch.object(requests, 'get', return_value=mock_response) as patched_requests:
            response = self.subject.request_height(self.node)
        self.assertEqual(response, 125)

    def test_request_height_When_status_code_not_200_Returns_none(self):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'height': 125}
        with patch.object(requests, 'get', return_value=mock_response) as patched_requests:
            response = self.subject.request_height(self.node)
        self.assertIsNone(response)

    @skip
    def test_broadcast_transaction(self):
        # TODO: Not testing this until implementation of a better broadcast pattern
        pass

    @skip
    def test_check_peers_light(self):
        # TODO: Not testing this until implementation of a better broadcast pattern
        pass

    @skip
    def test_check_peers_full(self):
        # TODO: Not testing this until implementation of a better broadcast pattern
        pass

    def test_get_balance_Returns_balance(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = 12500
        with patch.object(requests, 'get', return_value=mock_response) as patched_requests:
            response = self.subject.get_balance(self.node)
        self.assertEqual(response, 12500)

