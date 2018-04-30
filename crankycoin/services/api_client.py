import json
import requests

from crankycoin import config, logger
from crankycoin.models.enums import MessageType
from crankycoin.models.transaction import Transaction
from crankycoin.models.block import BlockHeader


class ApiClient(object):

    FULL_NODE_PORT = config['network']['full_node_port']
    NODES_URL = config['network']['nodes_url']
    INBOX_URL = config['network']['inbox_url']
    TRANSACTIONS_URL = config['network']['transactions_url']
    TRANSACTIONS_INV_URL = config['network']['transactions_inv_url']
    BLOCKS_INV_URL = config['network']['blocks_inv_url']
    BLOCKS_URL = config['network']['blocks_url']
    HEIGHT_URL = config['network']['height_url']
    TRANSACTION_HISTORY_URL = config['network']['transaction_history_url']
    BALANCE_URL = config['network']['balance_url']
    DOWNTIME_THRESHOLD = config['network']['downtime_threshold']
    STATUS_URL = config['network']['status_url']
    CONNECT_URL = config['network']['connect_url']
    MIN_PEERS = config['user']['min_peers']
    MAX_PEERS = config['user']['max_peers']

    def __init__(self, peers):
        self.peers = peers

    # Common

    def request_nodes(self, node, port):
        url = self.NODES_URL.format(node, port)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                all_nodes = response.json()
                return all_nodes
        except requests.exceptions.RequestException as re:
            self.peers.record_downtime(node)
            logger.debug('Downtime recorded for host {}'.format(node))
        return None

    def ping_status(self, host):
        url = self.STATUS_URL.format(host, self.FULL_NODE_PORT)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                status_dict = response.json()
                return status_dict == config['network']
        except requests.exceptions.RequestException as re:
            pass
        return None

    def request_height(self, node):
        url = self.HEIGHT_URL.format(node, self.FULL_NODE_PORT)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                height_dict = response.json()
                return height_dict.get('height')
        except requests.exceptions.RequestException as re:
            pass
        return None

    def broadcast_transaction(self, transaction):
        # Used only when broadcasting a transaction that originated locally
        data = {
            "type": MessageType.UNCONFIRMED_TRANSACTION.value,
            "data": transaction.to_dict()
        }
        for node in self.peers.get_all_peers():
            url = self.TRANSACTIONS_URL.format(node, self.FULL_NODE_PORT, "")
            try:
                response = requests.post(url, json=data)
                return response
            except requests.exceptions.RequestException as re:
                self.peers.record_downtime(node)
        return None
        # TODO: convert to grequests and return list of responses

    def check_peers_light(self, known_peers):
        # Light client version of check peers
        if self.peers.get_peers_count() < self.MIN_PEERS:
            for peer in known_peers:
                if self.peers.get_peers_count() >= self.MIN_PEERS:
                    break

                status_url = self.STATUS_URL.format(peer, self.FULL_NODE_PORT)
                try:
                    response = requests.get(status_url)
                    if response.status_code == 200 and response.json() == config['network']:
                        self.peers.add_peer(peer)
                except requests.exceptions.RequestException as re:
                    pass
        return

    def check_peers_full(self, host, known_peers):
        if self.peers.get_peers_count() < self.MIN_PEERS:
            host_data = {
                "host": host,
                "network": config['network']
            }

            for peer in known_peers:
                if self.peers.get_peers_count() >= self.MAX_PEERS:
                    break
                if peer == host:
                    continue

                status_url = self.STATUS_URL.format(peer, self.FULL_NODE_PORT)
                connect_url = self.CONNECT_URL.format(peer, self.FULL_NODE_PORT)
                try:
                    response = requests.get(status_url)
                    if response.status_code != 200:  # Downtime or error
                        if self.peers.get_peer(peer):
                            self.peers.record_downtime(peer)
                            logger.warn("Downtime recorded for node %s", peer)
                        continue
                    if response.json() != config['network']:  # Incompatible network
                        if self.peers.get_peer(peer):
                            self.peers.remove_peer(peer)
                        logger.warn("Incompatible network with node %s", peer)
                        continue
                    if self.peers.get_peer(peer) is None:
                        response = requests.post(connect_url, json=host_data)
                        if response.status_code == 202 and response.json().get("success") is True:
                            self.peers.add_peer(peer)
                except requests.exceptions.RequestException as re:
                    logger.warn("Request exception while attempting to reach %s", peer)
                    if self.peers.get_peer(peer):
                        self.peers.record_downtime(peer)
        return

    # Light Client

    def get_balance(self, address=None, node=None):
        url = self.BALANCE_URL.format(node, self.FULL_NODE_PORT, address)
        try:
            response = requests.get(url)
            return response.json()
        except requests.exceptions.RequestException as re:
            pass
        return None

    def get_transaction_history(self, address=None, node=None):
        url = self.TRANSACTION_HISTORY_URL.format(node, self.FULL_NODE_PORT, address)
        try:
            response = requests.get(url)
            return response.json()
        except requests.exceptions.RequestException as re:
            pass
        return None

    # Full Node

    def request_block_header(self, node, port, block_hash=None, height=None):
        if block_hash is not None:
            url = self.BLOCKS_URL.format(node, port, "hash", block_hash)
        elif height is not None:
            url = self.BLOCKS_URL.format(node, port, "height", height)
        else:
            url = self.BLOCKS_URL.format(node, port, "height", "latest")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                block_dict = response.json()
                block_header = BlockHeader(
                    block_dict['previous_hash'],
                    block_dict['merkle_root'],
                    block_dict['timestamp'],
                    block_dict['nonce'],
                    block_dict['version'])
                return block_header
        except requests.exceptions.RequestException as re:
            logger.warn("Request Exception with host: {}".format(node))
            self.peers.record_downtime(node)
        return None

    def request_transaction(self, node, port, tx_hash):
        url = self.TRANSACTIONS_URL.format(node, port, tx_hash)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                tx_dict = response.json()
                transaction = Transaction(
                    tx_dict['source'],
                    tx_dict['destination'],
                    tx_dict['amount'],
                    tx_dict['fee'],
                    tx_dict['prev_hash'],
                    tx_dict['tx_type'],
                    tx_dict['timestamp'],
                    tx_dict['tx_hash'],
                    tx_dict['asset'],
                    tx_dict['data'],
                    tx_dict['signature']
                )
                if transaction.tx_hash != tx_dict['tx_hash']:
                    logger.warn("Invalid transaction hash: {} should be {}.  Transaction ignored."
                                .format(tx_dict['tx_hash'], transaction.tx_hash))
                    return None
                return transaction
        except requests.exceptions.RequestException as re:
            logger.warn("Request Exception with host: {}".format(node))
            self.peers.record_downtime(node)
        return None

    def request_transactions_inv(self, node, port, block_hash):
        # Request a list of transaction hashes that belong to a block hash. Used when recreating a block from a
        # block header
        url = self.TRANSACTIONS_INV_URL.format(node, port, block_hash)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                tx_dict = response.json()
                return tx_dict['tx_hashes']
        except requests.exceptions.RequestException as re:
            logger.warn("Request Exception with host: {}".format(node))
            self.peers.record_downtime(node)
        return None

    def request_blocks_inv(self, node, port, start_height, stop_height):
        # Used when a synchronization between peers is needed
        url = self.BLOCKS_INV_URL.format(node, port, start_height, stop_height)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                block_dict = response.json()
                return block_dict['block_hashes']
        except requests.exceptions.RequestException as re:
            logger.warn("Request Exception with host: {}".format(node))
            self.peers.record_downtime(node)
        return None

    def broadcast_block_inv(self, block_hashes, host):
        # Used for (re)broadcasting a new block that was received and added
        data = {
            "host": host,
            "type": MessageType.BLOCK_INV.value,
            "data": block_hashes
        }
        logger.debug("broadcasting block inv: {}".format(data))
        for node in self.peers.get_all_peers():
            url = self.INBOX_URL.format(node, self.FULL_NODE_PORT)
            try:
                response = requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                logger.warn("Request Exception with host: {}".format(node))
                self.peers.record_downtime(node)
        return

    def broadcast_unconfirmed_transaction_inv(self, tx_hashes, host):
        # Used for (re)broadcasting a new transaction that was received and added
        data = {
            "host": host,
            "type": MessageType.UNCONFIRMED_TRANSACTION_INV.value,
            "data": tx_hashes
        }
        logger.debug("broadcasting transaction inv: {}".format(data))
        for node in self.peers.get_all_peers():
            url = self.INBOX_URL.format(node, self.FULL_NODE_PORT)
            try:
                response = requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                logger.warn("Request Exception with host: {}".format(node))
                self.peers.record_downtime(node)
        return

    def broadcast_block_header(self, block_header, host):
        # Used only when broadcasting a block header that originated (mined) locally
        data = {
            "host": host,
            "type": MessageType.BLOCK_HEADER.value,
            "data": block_header.to_json()
        }
        logger.debug("broadcasting block header: {}".format(data))
        for node in self.peers.get_all_peers():
            url = self.INBOX_URL.format(node, self.FULL_NODE_PORT)
            try:
                response = requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                logger.warn("Request Exception with host: {}".format(node))
                self.peers.record_downtime(node)
        return

    def push_synchronize(self, node, blocks_inv, current_height, host):
        # Push local blocks_inv to remote node to initiate a sync
        data = {
            "host": host,
            "type": MessageType.SYNCHRONIZE.value,
            "data": {"height": current_height, "blocks_inv": blocks_inv}
        }
        logger.debug("sending sync request to peer at: {}".format(node))
        url = self.INBOX_URL.format(node, self.FULL_NODE_PORT)
        try:
            response = requests.post(url, json=data)
        except requests.exceptions.RequestException as re:
            logger.warn("Request Exception with host: {}".format(node))
            self.peers.record_downtime(node)
        return

    def audit(self, node, start_height, end_height):
        # Audit node's blocks_inv and sync if necessary
        url = self.BLOCKS_INV_URL.format(node, self.FULL_NODE_PORT, start_height, end_height)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                tx_dict = response.json()
                return tx_dict.get('blocks_inv')
        except requests.exceptions.RequestException as re:
            logger.warn("Request Exception with host: {}".format(node))
            self.peers.record_downtime(node)
        return None
