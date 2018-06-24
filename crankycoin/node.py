import json
import logging
import multiprocessing as mp
from bottle import Bottle

from crankycoin.models.block import Block, BlockHeader
from crankycoin.models.transaction import Transaction
from crankycoin.models.enums import MessageType, TransactionType
from crankycoin.services.queue import Queue
from crankycoin.routes.permissioned import permissioned_app
from crankycoin.routes.public import public_app
from crankycoin import config, logger


class NodeMixin(object):

    FULL_NODE_PORT = config['network']['full_node_port']
    NODES_URL = config['network']['nodes_url']
    INBOX_URL = config['network']['inbox_url']
    TRANSACTIONS_URL = config['network']['transactions_url']
    TRANSACTIONS_INV_URL = config['network']['transactions_inv_url']
    UNCONFIRMED_TRANSACTIONS_URL = config['network']['unconfirmed_transactions_url']
    BLOCKS_INV_URL = config['network']['blocks_inv_url']
    BLOCKS_URL = config['network']['blocks_url']
    TRANSACTION_HISTORY_URL = config['network']['transaction_history_url']
    BALANCE_URL = config['network']['balance_url']
    DOWNTIME_THRESHOLD = config['network']['downtime_threshold']
    STATUS_URL = config['network']['status_url']
    CONNECT_URL = config['network']['connect_url']
    MIN_PEERS = config['user']['min_peers']
    MAX_PEERS = config['user']['max_peers']

    def __init__(self, peers, api_client):
        self.peers = peers
        self.api_client = api_client

    def discover_peers(self):
        peers = self.peers.get_all_peers()
        discovered_peers = set(peers)
        for peer in peers:
            nodes = self.api_client.request_nodes(peer, self.FULL_NODE_PORT)
            if nodes is not None:
                discovered_peers = discovered_peers.union(nodes["full_nodes"])
        return list(discovered_peers)

    def check_peers(self):
        raise NotImplementedError


class FullNode(NodeMixin):

    NODE_TYPE = "full"
    HOST = config['user']['ip']
    WORKER_PROCESSES = config['user']['queue_processing_workers']
    blockchain = None
    bottle_process = None
    queue_process = None
    worker_processes = None

    def __init__(self, peers, api_client, blockchain, mempool, validator):
        super(FullNode, self).__init__(peers, api_client)
        mp.log_to_stderr()
        mp_logger = mp.get_logger()
        mp_logger.setLevel(logging.DEBUG)
        self.app = Bottle()
        self.app.merge(public_app)
        self.app.merge(permissioned_app)
        self.blockchain = blockchain
        self.mempool = mempool
        self.validator = validator

    def start(self):
        logger.debug("queue process starting...")
        self.queue_process = mp.Process(target=Queue.start_queue)
        self.queue_process.start()
        logger.debug("worker process(es) starting...")
        self.worker_processes = [mp.Process(target=self.worker) for _ in range(self.WORKER_PROCESSES)]
        for wp in self.worker_processes:
            wp.start()
        logger.debug("full node server starting on %s...", self.HOST)
        self.bottle_process = mp.Process(target=self.app.run, kwargs=dict(host="0.0.0.0", port=self.FULL_NODE_PORT, debug=True))
        self.bottle_process.start()
        self.check_peers()

    def shutdown(self):
        logger.debug("full node on %s shutting down...", self.HOST)
        self.bottle_process.terminate()
        logger.debug("worker process(es) shutting down...")
        for wp in self.worker_processes:
            wp.terminate()
        logger.debug("queue process shutting down...")
        self.queue_process.terminate()

    def check_peers(self):
        known_peers = self.discover_peers()
        self.api_client.check_peers_full(self.HOST, known_peers)
        return

    def worker(self):
        while True:
            msg = Queue.dequeue()
            sender = msg.get('host', '')
            msg_type = MessageType(msg.get('type'))
            data = msg.get('data')
            if msg_type == MessageType.BLOCK_HEADER:
                block_header = BlockHeader.from_dict(json.loads(data))
                if sender == self.HOST:
                    self.api_client.broadcast_block_inv([block_header.hash], self.HOST)
                else:
                    self.__process_block_header(block_header, sender)
                continue
            elif msg_type == MessageType.UNCONFIRMED_TRANSACTION:
                unconfirmed_transaction = Transaction.from_dict(data)
                if sender == self.HOST:
                    # transaction already validated before being enqueued
                    valid = True
                else:
                    valid = self.validator.validate_transaction(unconfirmed_transaction)
                if valid:
                    self.api_client.broadcast_unconfirmed_transaction_inv([unconfirmed_transaction.tx_hash], self.HOST)
                continue
            elif msg_type == MessageType.BLOCK_INV:
                missing_block_headers = []
                for block_hash in data:
                    # aggregate unknown block header hashes
                    block_header = self.blockchain.get_block_header_by_hash(block_hash)
                    if block_header is None:
                        missing_block_headers.append(block_hash)
                for block_hash in missing_block_headers:
                    # We don't have these blocks in our database.  Fetch them from the sender
                    block_header = self.api_client.request_block_header(sender, self.FULL_NODE_PORT,
                                                                        block_hash=block_hash)
                    self.__process_block_header(block_header, sender)
                continue
            elif msg_type == MessageType.UNCONFIRMED_TRANSACTION_INV:
                missing_transactions = []
                new_unconfirmed_transactions = []
                for tx_hash in data:
                    # skip known unconfirmed transactions
                    transaction = self.blockchain.get_transaction_by_hash(tx_hash)
                    if transaction:
                        continue
                    unconfirmed_transaction = self.mempool.get_unconfirmed_transaction(tx_hash)
                    if unconfirmed_transaction:
                        continue
                    missing_transactions.append(tx_hash)
                for tx_hash in missing_transactions:
                    # retrieve unknown unconfirmed transactions
                    transaction = self.api_client.request_transaction(sender, self.FULL_NODE_PORT, tx_hash)
                    valid = self.validator.validate_transaction(transaction)
                    if valid:
                        # validate and store retrieved unconfirmed transactions
                        self.mempool.push_unconfirmed_transaction(transaction)
                        new_unconfirmed_transactions.append(tx_hash)
                if len(new_unconfirmed_transactions):
                    # broadcast new unconfirmed transactions
                    self.api_client.broadcast_unconfirmed_transaction_inv(new_unconfirmed_transactions)
                continue
            else:
                logger.warn("Encountered unknown message type %s from %s", msg_type, sender)
                pass

    def __process_block_header(self, block_header, sender):
        """
        Request transactions_inv and Validate header

        :param block_header:
        :param sender:
        :return:
        """
        # request transactions inv and missing transactions and add block
        transactions_inv = self.api_client.request_transactions_inv(sender, self.FULL_NODE_PORT, block_header.hash)
        valid_block_height = self.validator.validate_block_header(block_header, transactions_inv)
        if valid_block_height:
            block_transactions, missing_transactions_inv = self.validator.validate_block_transactions_inv(
                transactions_inv)
            for tx_hash in missing_transactions_inv:
                transaction = self.api_client.request_transaction(sender, self.FULL_NODE_PORT, tx_hash)
                if TransactionType(transaction.tx_type) == TransactionType.COINBASE:
                    block_transactions.insert(0, transaction)
                else:
                    if not self.validator.validate_transaction(transaction):
                        return False
                    block_transactions.append(transaction)
            block = Block(
                valid_block_height,
                block_transactions,
                block_header.previous_hash,
                timestamp=block_header.timestamp,
                nonce=block_header.nonce)
            if self.validator.validate_block(block, block_header.merkle_root) and self.blockchain.add_block(block):
                self.api_client.broadcast_block_inv([block_header.hash], self.HOST)
        elif valid_block_height is None:
            self.__synchronize(sender)

    def __synchronize(self, node):
        # synchronize with sender
        repeat_sync = True
        while repeat_sync is True:
            current_height = self.blockchain.get_height()
            peer_height = self.api_client.request_height(node)
            if peer_height is not None and peer_height > current_height:
                # 100 blocks of overlap should be sufficient to find a common block lest we are on a forked branch
                start_height = current_height - 100 if current_height > 100 else 1
                if current_height < peer_height - 500:
                    # we are way behind.
                    end_height = start_height + 500
                else:
                    end_height = peer_height
                    repeat_sync = False
                peer_blocks_inv = self.api_client.audit(node, start_height, end_height)
                last_common_block = self.__find_last_common_block(peer_blocks_inv)
                if last_common_block is None:
                    logger.warn("Completely out of sync with peer at {}".format(node))
                    break
                block_header, branch, height = last_common_block
                # construct list of missing block hashes to request from the peer
                hashes_to_query = peer_blocks_inv[peer_blocks_inv.index(block_header.hash)+1:]
                for block_hash in hashes_to_query:
                    block_header = self.api_client.request_block_header(node, self.FULL_NODE_PORT,
                                                                        block_hash=block_hash)
                    self.__process_block_header(block_header, node)
            else:
                repeat_sync = False

    def __find_last_common_block(self, peer_blocks_inv):
        """
        Identify the last common between the local chain and the peer chain.
        :param peer_blocks_inv:
        :return: latest common block height, latest common block hash
        :rtype: tuple(int, string)
        """
        last_common_block = None
        for hash in peer_blocks_inv:
            block = self.blockchain.get_block_header_by_hash(hash)
            if block is None:
                break
            last_common_block = block
        return last_common_block


if __name__ == "__main__":
    pass
