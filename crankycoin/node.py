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
                    valid = True
                else:
                    valid = self.validator.validate_transaction(unconfirmed_transaction)
                if valid:
                    self.api_client.broadcast_transaction_inv([unconfirmed_transaction.tx_hash], self.HOST)
                continue
            elif msg_type == MessageType.BLOCK_INV:
                missing_block_headers = []
                for block_hash in data:
                    block_header = self.blockchain.get_block_header_by_hash(block_hash)
                    if block_header is None:
                        missing_block_headers.append(block_hash)
                for block_hash in missing_block_headers:
                    # We don't have these blocks in our database.  Fetch them from the sender
                    block_header = self.api_client.request_block_header(sender, self.FULL_NODE_PORT, block_hash=block_hash)
                    prev_header = self.blockchain.get_block_header_by_hash(block_header.previous_hash)
                    # TODO: validate block_header hash
                    transactions_inv = self.api_client.request_transactions_index(sender, self.FULL_NODE_PORT, block_hash)
                    # TODO: validate transaction hashes and merkle root
                    block_transactions = []
                    for tx_hash in transactions_inv:
                        transaction = self.mempool.get_unconfirmed_transaction(tx_hash)
                        if transaction is None:
                            # We don't have this transaction in our database.  Fetch it from the sender
                            transaction = self.api_client.request_transaction(sender, self.FULL_NODE_PORT, tx_hash)
                        block_transactions.append(transaction)
                    # TODO: construct block
                    # TODO: add block
                    # TODO: re-broadcast INV
                continue
            elif msg_type == MessageType.TRANSACTION_INV:
                missing_transactions = []
                for tx_hash in data:
                    transaction = self.blockchain.get_transaction_by_hash(tx_hash)
                    if transaction:
                        continue
                    unconfirmed_transaction = self.mempool.get_unconfirmed_transaction(tx_hash)
                    if unconfirmed_transaction:
                        continue
                    missing_transactions.append(tx_hash)
                for tx_hash in missing_transactions:
                    transaction = self.api_client.request_transaction(sender, self.FULL_NODE_PORT, tx_hash)
                    # TODO: validate transaction and place in mempool
                    if valid:
                        self.mempool.push_unconfirmed_transaction(transaction)
                continue
            else:
                logger.warn("Encountered unknown message type %s from %s", msg_type, sender)
                pass

    def __process_block_header(self, block_header, sender):
        """
        Block was mined by a (1st degree) peer.  Request transactions_inv and Validate header

        :param block_header:
        :param sender:
        :return:
        """
        # request transactions inv and missing transactions and add block
        transactions_inv = self.api_client.request_transactions_inv(sender, self.FULL_NODE_PORT, block_header.hash)
        valid_block_height = self.validator.validate_block_header(block_header, transactions_inv)
        if valid_block_height:
            block_transactions, missing_transactions_inv = self.validator.validate_transactions_inv(transactions_inv)
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
            # TODO: synchronize with sender
            self.api_client.request_blocks_inv(sender, self.FULL_NODE_PORT, )

    # def check_peers(self):
    #     if self.peers.get_peers_count() < self.MIN_PEERS:
    #         known_peers = self.find_known_peers()
    #         host_data = {
    #             "host": self.HOST
    #         }
    #
    #         for peer in known_peers:
    #             if self.peers.get_peers_count() >= self.MAX_PEERS:
    #                 break
    #             if peer == self.HOST:
    #                 continue
    #
    #             status_url = self.STATUS_URL.format(peer, self.FULL_NODE_PORT)
    #             connect_url = self.CONNECT_URL.format(peer, self.FULL_NODE_PORT)
    #             try:
    #                 response = requests.get(status_url)
    #                 if response.status_code != 200 or json.loads(response.json()) != config['network']:
    #                     continue
    #                 response = requests.post(connect_url, json=host_data)
    #                 if response.status_code == 202 and json.loads(response.json()).get("success") is True:
    #                     self.peers.add_peer(peer)
    #             except requests.exceptions.RequestException as re:
    #                 pass
    #     return
    #
    # def request_block_header(self, node, port, block_hash=None, height=None):
    #     if block_hash is not None:
    #         url = self.BLOCKS_URL.format(node, port, "hash", block_hash)
    #     elif height is not None:
    #         url = self.BLOCKS_URL.format(node, port, "height", height)
    #     else:
    #         url = self.BLOCKS_URL.format(node, port, "height", "latest")
    #     try:
    #         response = requests.get(url)
    #         if response.status_code == 200:
    #             block_dict = json.loads(response.json())
    #             block_header = BlockHeader(
    #                 block_dict['previous_hash'],
    #                 block_dict['merkle_root'],
    #                 block_dict['timestamp'],
    #                 block_dict['nonce'],
    #                 block_dict['version'])
    #             return block_header
    #     except requests.exceptions.RequestException as re:
    #         logger.warn("Request Exception with host: {}".format(node))
    #         self.peers.record_downtime(node)
    #     return None
    #
    # def request_transaction(self, node, port, tx_hash):
    #     url = self.TRANSACTIONS_URL.format(node, port, tx_hash)
    #     try:
    #         response = requests.get(url)
    #         if response.status_code == 200:
    #             tx_dict = json.loads(response.json())
    #             transaction = Transaction(
    #                 tx_dict['source'],
    #                 tx_dict['destination'],
    #                 tx_dict['amount'],
    #                 tx_dict['fee'],
    #                 tx_dict['prev_hash'],
    #                 tx_dict['tx_type'],
    #                 tx_dict['timestamp'],
    #                 tx_dict['tx_hash'],
    #                 tx_dict['asset'],
    #                 tx_dict['data'],
    #                 tx_dict['signature']
    #             )
    #             if transaction.tx_hash != tx_dict['tx_hash']:
    #                 logger.warn("Invalid transaction hash: {} should be {}.  Transaction ignored."
    #                             .format(tx_dict['tx_hash'], transaction.tx_hash))
    #                 return None
    #             return transaction
    #     except requests.exceptions.RequestException as re:
    #         logger.warn("Request Exception with host: {}".format(node))
    #         self.peers.record_downtime(node)
    #     return None
    #
    # def request_transactions_index(self, node, port, block_hash):
    #     # Request a list of transaction hashes that belong to a block hash. Used when recreating a block from a
    #     # block header
    #     url = self.TRANSACTIONS_INV_URL.format(node, port, block_hash)
    #     try:
    #         response = requests.get(url)
    #         if response.status_code == 200:
    #             tx_dict = json.loads(response.json())
    #             return tx_dict['tx_hashes']
    #     except requests.exceptions.RequestException as re:
    #         logger.warn("Request Exception with host: {}".format(node))
    #         self.peers.record_downtime(node)
    #     return None
    #
    # def request_blocks_inv(self, node, port, start_height, stop_height):
    #     # Used when a synchronization between peers is needed
    #     url = self.BLOCKS_INV_URL.format(node, port, start_height, stop_height)
    #     try:
    #         response = requests.get(url)
    #         if response.status_code == 200:
    #             block_dict = json.loads(response.json())
    #             return block_dict['block_hashes']
    #     except requests.exceptions.RequestException as re:
    #         logger.warn("Request Exception with host: {}".format(node))
    #         self.peers.record_downtime(node)
    #     return None
    #
    # def broadcast_block_inv(self, block_hashes):
    #     # Used for (re)broadcasting a new block that was received and added
    #     self.check_peers()
    #     data = {
    #         "block_hashes": block_hashes
    #     }
    #     for node in self.peers.get_all_peers():
    #         url = self.INBOX_URL.format(node, self.FULL_NODE_PORT)
    #         try:
    #             response = requests.post(url, json=data)
    #         except requests.exceptions.RequestException as re:
    #             logger.warn("Request Exception with host: {}".format(node))
    #             self.peers.record_downtime(node)
    #     return
    #
    # def broadcast_transaction_inv(self, tx_hashes):
    #     # Used for (re)broadcasting a new transaction that was received and added
    #     self.check_peers()
    #     data = {
    #         "tx_hashes": tx_hashes
    #     }
    #     for node in self.peers.get_all_peers():
    #         url = self.INBOX_URL.format(node, self.FULL_NODE_PORT)
    #         try:
    #             response = requests.post(url, json=data)
    #         except requests.exceptions.RequestException as re:
    #             logger.warn("Request Exception with host: {}".format(node))
    #             self.peers.record_downtime(node)
    #     return
    #
    # def broadcast_block_header(self, block_header):
    #     # Used only when broadcasting a block header that originated (mined) locally
    #     self.check_peers()
    #     data = {
    #         "block_header": block_header.to_json()
    #     }
    #     for node in self.peers.get_all_peers():
    #         url = self.INBOX_URL.format(node, self.FULL_NODE_PORT)
    #         try:
    #             response = requests.post(url, json=data)
    #         except requests.exceptions.RequestException as re:
    #             logger.warn("Request Exception with host: {}".format(node))
    #             self.peers.record_downtime(node)
    #     return

    # def request_blocks_range(self, node, port, start_index, stop_index):
    #     # TODO: Deprecate
    #     # TODO: Limit number of blocks
    #     url = self.BLOCKS_RANGE_URL.format(node, port, start_index, stop_index)
    #     blocks = []
    #     try:
    #         response = requests.get(url)
    #         if response.status_code == 200:
    #             blocks_dict = json.loads(response.json())
    #             for block_dict in blocks_dict:
    #                 block = Block(
    #                     block_dict['index'],
    #                     [Transaction(
    #                         transaction['source'],
    #                         transaction['destination'],
    #                         transaction['amount'],
    #                         transaction['fee'],
    #                         transaction['signature'])
    #                      for transaction in block_dict['transactions']
    #                      ],
    #                     block_dict['previous_hash'],
    #                     block_dict['timestamp'],
    #                     block_dict['nonce']
    #                 )
    #                 if block.current_hash != block_dict['current_hash']:
    #                     raise InvalidHash(block.index, "Block Hash Mismatch: {}".format(block_dict['current_hash']))
    #                 blocks.append(block)
    #     except requests.exceptions.RequestException as re:
    #         pass
    #     return blocks

    # def request_blockchain(self, node, port):
    #     # TODO: Deprecate
    #     url = self.BLOCKS_URL.format(node, port, "")
    #     blocks = []
    #     try:
    #         response = requests.get(url)
    #         if response.status_code == 200:
    #             blocks_dict = json.loads(response.json())
    #             for block_dict in blocks_dict:
    #                 block = Block(
    #                     block_dict['index'],
    #                     [Transaction(
    #                         transaction['source'],
    #                         transaction['destination'],
    #                         transaction['amount'],
    #                         transaction['fee'],
    #                         transaction['signature'])
    #                      for transaction in block_dict['transactions']
    #                      ],
    #                     block_dict['previous_hash'],
    #                     block_dict['timestamp'],
    #                     block_dict['nonce']
    #                 )
    #                 if block.block_header.hash != block_dict['current_hash']:
    #                     raise InvalidHash(block.height, "Block Hash Mismatch: {}".format(block_dict['current_hash']))
    #                 blocks.append(block)
    #             return blocks
    #     except requests.exceptions.RequestException as re:
    #         pass
    #     return None
    # def broadcast_block(self, block):
    #     # TODO DEPRECATE
    #     # TODO convert to grequests and concurrently gather a list of responses
    #     statuses = {
    #         "confirmations": 0,
    #         "invalidations": 0,
    #         "expirations": 0
    #     }
    #
    #     self.check_peers()
    #     bad_nodes = set()
    #     data = {
    #         "block": block.to_json(),
    #         "host": self.HOST
    #     }
    #
    #     for node in self.full_nodes:
    #         if node == self.HOST:
    #             continue
    #         url = self.BLOCKS_URL.format(node, self.FULL_NODE_PORT, "")
    #         try:
    #             response = requests.post(url, json=data)
    #             if response.status_code == 202:
    #                 # confirmed and accepted by node
    #                 statuses["confirmations"] += 1
    #             elif response.status_code == 406:
    #                 # invalidated and rejected by node
    #                 statuses["invalidations"] += 1
    #             elif response.status_code == 409:
    #                 # expired and rejected by node
    #                 statuses["expirations"] += 1
    #         except requests.exceptions.RequestException as re:
    #             bad_nodes.add(node)
    #     for node in bad_nodes:
    #         self.remove_node(node)
    #     bad_nodes.clear()
    #     return statuses

    # def add_node(self, host):
    #     # TODO: Deprecate
    #     if host == self.HOST:
    #         return
    #
    #     if host not in self.full_nodes:
    #         self.broadcast_node(host)
    #         self.full_nodes.add(host)

    # def broadcast_node(self, host):
    #     # TODO: Deprecate
    #     self.check_peers()
    #     bad_nodes = set()
    #     data = {
    #         "host": host
    #     }
    #
    #     for node in self.full_nodes:
    #         if node == self.HOST:
    #             continue
    #         url = self.NODES_URL.format(node, self.FULL_NODE_PORT)
    #         try:
    #             requests.post(url, json=data)
    #         except requests.exceptions.RequestException as re:
    #             bad_nodes.add(node)
    #     for node in bad_nodes:
    #         self.remove_node(node)
    #     bad_nodes.clear()
    #     return

    # def synchronize(self):
    #     # TODO: Deprecate
    #     my_latest_block = self.blockchain.get_tallest_block_header()
    #     """
    #     latest_blocks = {
    #         index1 : {
    #             current_hash1 : [node1, node2],
    #             current_hash2 : [node3]
    #         },
    #         index2 : {
    #             current_hash3 : [node4]
    #         }
    #     }
    #     """
    #     latest_blocks = {}
    #
    #     self.check_peers()
    #     bad_nodes = set()
    #     for node in self.full_nodes:
    #         url = self.BLOCKS_URL.format(node, self.FULL_NODE_PORT, "latest")
    #         try:
    #             response = requests.get(url)
    #             if response.status_code == 200:
    #                 remote_latest_block = json.loads(response.json())
    #                 if remote_latest_block["index"] <= my_latest_block.index:
    #                     continue
    #                 if latest_blocks.get(remote_latest_block["index"], None) is None:
    #                     latest_blocks[remote_latest_block["index"]] = {
    #                         remote_latest_block["current_hash"]: [node]
    #                     }
    #                     continue
    #                 if latest_blocks[remote_latest_block["index"]].get(remote_latest_block["current_hash"], None) is None:
    #                     latest_blocks[remote_latest_block["index"]][remote_latest_block["current_hash"]] = [node]
    #                     continue
    #                 latest_blocks[remote_latest_block["index"]][remote_latest_block["current_hash"]].append(node)
    #         except requests.exceptions.RequestException as re:
    #             bad_nodes.add(node)
    #     if len(latest_blocks) > 0:
    #         for latest_block in sorted(latest_blocks.items(), reverse=True):
    #             index = latest_block[0]
    #             current_hashes = latest_block[1]
    #             success = True
    #             for current_hash in current_hashes:
    #                 remote_host = current_hash[1][0]
    #
    #                 remote_diff_blocks = self.request_blocks_range(
    #                     remote_host,
    #                     self.FULL_NODE_PORT,
    #                     my_latest_block.index + 1,
    #                     index
    #                 )
    #                 if remote_diff_blocks[0].previous_hash == my_latest_block.current_hash:
    #                     # first block in diff blocks fit local chain
    #                     for block in remote_diff_blocks:
    #                         # TODO: validate
    #                         result = self.blockchain.add_block(block)
    #                         if not result:
    #                             success = False
    #                             break
    #                         else:
    #                             self.__remove_unconfirmed_transactions(block.transactions[1:])
    #                 else:
    #                     # first block in diff blocks does not fit local chain
    #                     for i in range(my_latest_block.index, 1, -1):
    #                         # step backwards and look for the first remote block that fits the local chain
    #                         block = self.request_block(remote_host, self.FULL_NODE_PORT, str(i))
    #                         remote_diff_blocks[0:0] = [block]
    #                         if block.block_header.previous_hash == self.blockchain.get_block_headers_by_height(i-1):
    #                             # found the fork
    #                             result = self.blockchain.alter_chain(remote_diff_blocks)
    #                             success = result
    #                             break
    #                     success = False
    #                 if success:
    #                     break
    #             if success:
    #                 break
    #     return

    # @app.route('/nodes/', methods=['POST'])
    # def post_node(self, request):
    #     # TODO: Deprecate
    #     body = json.loads(request.content.read())
    #     self.add_node(body['host'])
    #     return json.dumps({'success': True})

    # @app.route('/blocks/', methods=['POST'])
    # def post_block(self, request):
    #     # TODO: Deprecate
    #     body = json.loads(request.content.read())
    #     remote_block = json.loads(body['block'])
    #     remote_host = body['host']
    #     block = Block.from_dict(remote_block)
    #     if block.current_hash != remote_block['current_hash']:
    #         request.setResponseCode(406)  # not acceptable
    #         return json.dumps({'message': 'block rejected due to invalid hash'})
    #     my_latest_block = self.blockchain.get_tallest_block_header()
    #
    #     if block.index > my_latest_block.index + 1:
    #         # new block index is greater than ours
    #         remote_diff_blocks = self.request_blocks_range(
    #             remote_host,
    #             self.FULL_NODE_PORT,
    #             my_latest_block.index + 1,
    #             remote_block['index']
    #         )
    #
    #         if remote_diff_blocks[0].previous_hash == my_latest_block.current_hash:
    #             # first block in diff blocks fit local chain
    #             for block in remote_diff_blocks:
    #                 # TODO: validate
    #                 result = self.blockchain.add_block(block)
    #                 if not result:
    #                     request.setResponseCode(406)  # not acceptable
    #                     return json.dumps({'message': 'block {} rejected'.format(block.index)})
    #             self.__remove_unconfirmed_transactions(block.transactions)
    #             request.setResponseCode(202)  # accepted
    #             return json.dumps({'message': 'accepted'})
    #         else:
    #             # first block in diff blocks does not fit local chain
    #             for i in range(my_latest_block.index, 1, -1):
    #                 # step backwards and look for the first remote block that fits the local chain
    #                 block = self.request_block(remote_host, self.FULL_NODE_PORT, str(i))
    #                 remote_diff_blocks[0:0] = [block]
    #                 if block.block_header.previous_hash == self.blockchain.get_block_headers_by_height(i-1):
    #                     # found the fork
    #                     result = self.blockchain.alter_chain(remote_diff_blocks)
    #                     if not result:
    #                         request.setResponseCode(406)  # not acceptable
    #                         return json.dumps({'message': 'blocks rejected'})
    #                     self.__remove_unconfirmed_transactions(block.transactions)
    #                     request.setResponseCode(202)  # accepted
    #                     return json.dumps({'message': 'accepted'})
    #             request.setResponseCode(406)  # not acceptable
    #             return json.dumps({'message': 'blocks rejected'})
    #
    #     elif block.index <= my_latest_block.index:
    #         # new block index is less than ours
    #         request.setResponseCode(409)  # conflict
    #         return json.dumps({'message': 'Block index too low.  Fetch latest chain.'})
    #
    #     # correct block index. verify txs, hash
    #     # TODO: validate
    #     result = self.blockchain.add_block(block)
    #     if not result:
    #         request.setResponseCode(406)  # not acceptable
    #         return json.dumps({'message': 'block {} rejected'.format(block.index)})
    #     self.__remove_unconfirmed_transactions(block.transactions)
    #     request.setResponseCode(202)  # accepted
    #     return json.dumps({'message': 'accepted'})

    # @app.route('/blocks/start/<start_block_id>/end/<end_block_id>', methods=['GET'])
    # def get_blocks_range(self, request, start_block_id, end_block_id):
    #     return json.dumps([block.to_dict() for block in self.blockchain.get_blocks_range(int(start_block_id), int(end_block_id))])


if __name__ == "__main__":
    pass
