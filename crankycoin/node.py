import grequests
import requests
from klein import Klein
from multiprocessing import Process
from Queue import Empty, Full

from blockchain import *
from transaction import *


class NodeMixin(object):

    FULL_NODE_PORT = config['network']['full_node_port']
    NODES_URL = config['network']['nodes_url']
    TRANSACTIONS_URL = config['network']['transactions_url']
    BLOCK_URL = config['network']['block_url']
    BLOCKS_RANGE_URL = config['network']['blocks_range_url']
    BLOCKS_URL = config['network']['blocks_url']
    TRANSACTION_HISTORY_URL = config['network']['transaction_history_url']
    BALANCE_URL = config['network']['balance_url']
    DNS_SEEDS = config['network']['dns_seeds']
    SEED_NODES = config['network']['seed_nodes']

    full_nodes = set(SEED_NODES)

    def request_nodes(self, node, port):
        url = self.NODES_URL.format(node, port)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                all_nodes = response.json()
                return all_nodes
        except requests.exceptions.RequestException as re:
            pass
        return None

    def request_nodes_from_all(self):
        full_nodes = self.full_nodes.copy()
        bad_nodes = set()

        for node in full_nodes:
            all_nodes = self.request_nodes(node, self.FULL_NODE_PORT)
            if all_nodes is not None:
                full_nodes = full_nodes.union(all_nodes["full_nodes"])
            else:
                bad_nodes.add(node)
        self.full_nodes = full_nodes

        for node in bad_nodes:
            self.remove_node(node)
        return

    def remove_node(self, node):
        # nodeset.discard(node)
        pass

    def broadcast_transaction(self, transaction):
        self.request_nodes_from_all()
        bad_nodes = set()
        data = {
            "transaction": transaction.to_json()
        }

        for node in self.full_nodes:
            url = self.TRANSACTIONS_URL.format(node, self.FULL_NODE_PORT)
            try:
                response = requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)
        for node in bad_nodes:
            self.remove_node(node)
        bad_nodes.clear()
        return
        # TODO: convert to grequests and return list of responses


class FullNode(NodeMixin):
    NODE_TYPE = "full"
    blockchain = None
    app = Klein()

    def __init__(self, host, reward_address, **kwargs):
        self.host = host
        self.request_nodes_from_all()
        self.reward_address = reward_address
        self.broadcast_node(host)
        self.full_nodes.add(host)

        block_path = kwargs.get("block_path")
        if block_path is None:
            self.blockchain = Blockchain()
        else:
            self.load_blockchain(block_path)

        mining = kwargs.get("mining")
        if mining is True:
            self.NODE_TYPE = "miner"
            self.mining_process = Process(target=self.mine)
            self.mining_process.start()
            logger.debug("mining node started on %s with reward address of %s...", host, reward_address)
        logger.debug("full node server starting on %s with reward address of %s...", host, reward_address)
        self.node_process = Process(target=self.app.run, args=(host, self.FULL_NODE_PORT))
        self.node_process.start()
        logger.debug("full node server started on %s with reward address of %s...", host, reward_address)

    def shutdown(self, force=False):
        self.blockchain.unconfirmed_transactions.close()
        if force is True:
            self.blockchain.unconfirmed_transactions.cancel_join_thread()
            if self.NODE_TYPE == "miner":
                self.mining_process.terminate()
            self.node_process.terminate()
        else:
            self.blockchain.unconfirmed_transactions.join_thread()
            if self.NODE_TYPE == "miner":
                self.mining_process.join(1)
            self.node_process.join(1)

    def request_block(self, node, port, index="latest"):
        url = self.BLOCK_URL.format(node, port, index)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                block_dict = json.loads(response.json())
                block = Block(
                    block_dict['index'],
                    [Transaction(
                        transaction['source'],
                        transaction['destination'],
                        transaction['amount'],
                        transaction['fee'],
                        transaction['signature'])
                        for transaction in block_dict['transactions']
                     ],
                    block_dict['previous_hash'],
                    block_dict['timestamp'],
                    block_dict['nonce']
                )
                if block.current_hash != block_dict['current_hash']:
                    raise InvalidHash(block.index, "Block Hash Mismatch: {} {}".format(block_dict['current_hash'], block.current_hash))
                return block
        except requests.exceptions.RequestException as re:
            pass
        return None

    def request_block_from_all(self, index="latest"):
        blocks = []

        full_nodes = self.full_nodes.copy()
        bad_nodes = set()

        for node in full_nodes:
            block = self.request_block(node, self.FULL_NODE_PORT, index)
            if block is not None:
                blocks.append(block)
            else:
                bad_nodes.add(node)

        for node in bad_nodes:
            self.remove_node(node)
        return blocks

    def request_blocks_range(self, node, port, start_index, stop_index):
        url = self.BLOCKS_RANGE_URL.format(node, port, start_index, stop_index)
        blocks = []
        try:
            response = requests.get(url)
            if response.status_code == 200:
                blocks_dict = json.loads(response.json())
                for block_dict in blocks_dict:
                    block = Block(
                        block_dict['index'],
                        [Transaction(
                            transaction['source'],
                            transaction['destination'],
                            transaction['amount'],
                            transaction['fee'],
                            transaction['signature'])
                         for transaction in block_dict['transactions']
                         ],
                        block_dict['previous_hash'],
                        block_dict['timestamp'],
                        block_dict['nonce']
                    )
                    if block.current_hash != block_dict['current_hash']:
                        raise InvalidHash(block.index, "Block Hash Mismatch: {}".format(block_dict['current_hash']))
                    blocks.append(block)
                return blocks
        except requests.exceptions.RequestException as re:
            pass
        return None

    def request_blockchain(self, node, port):
        url = self.BLOCKS_URL.format(node, port)
        blocks = []
        try:
            response = requests.get(url)
            if response.status_code == 200:
                blocks_dict = json.loads(response.json())
                for block_dict in blocks_dict:
                    block = Block(
                        block_dict['index'],
                        [Transaction(
                            transaction['source'],
                            transaction['destination'],
                            transaction['amount'],
                            transaction['fee'],
                            transaction['signature'])
                         for transaction in block_dict['transactions']
                         ],
                        block_dict['previous_hash'],
                        block_dict['timestamp'],
                        block_dict['nonce']
                    )
                    if block.current_hash != block_dict['current_hash']:
                        raise InvalidHash(block.index, "Block Hash Mismatch: {}".format(block_dict['current_hash']))
                    blocks.append(block)
                return blocks
        except requests.exceptions.RequestException as re:
            pass
        return None

    def mine(self):
        logger.debug("mining node starting on %s with reward address of %s...", self.host, self.reward_address)
        while True:
            latest_block = self.blockchain.get_latest_block()
            latest_hash = latest_block.current_hash
            latest_index = latest_block.index

            block = self.blockchain.mine_block(self.reward_address)
            if not block:
                continue
            statuses = self.broadcast_block(block)
            if statuses['expirations'] > statuses['confirmations'] or \
                    statuses['invalidations'] > statuses['confirmations']:
                self.synchronize()
                new_latest_block = self.blockchain.get_latest_block()
                if latest_hash != new_latest_block.current_hash or \
                        latest_index != new_latest_block.index:
                    # latest_block changed after sync.. don't add the block.
                    self.blockchain.recycle_transactions(block)
                    continue
            self.blockchain.add_block(block)

    def broadcast_block(self, block):
        #TODO convert to grequests and concurrently gather a list of responses
        statuses = {
            "confirmations": 0,
            "invalidations": 0,
            "expirations": 0
        }

        self.request_nodes_from_all()
        bad_nodes = set()
        data = {
            "block": block.to_json(),
            "host": self.host
        }

        for node in self.full_nodes:
            if node == self.host:
                continue
            url = self.BLOCKS_URL.format(node, self.FULL_NODE_PORT)
            try:
                response = requests.post(url, json=data)
                if response.status_code == 202:
                    # confirmed and accepted by node
                    statuses["confirmations"] += 1
                elif response.status_code == 406:
                    # invalidated and rejected by node
                    statuses["invalidations"] += 1
                elif response.status_code == 409:
                    # expired and rejected by node
                    statuses["expirations"] += 1
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)
        for node in bad_nodes:
            self.remove_node(node)
        bad_nodes.clear()
        return statuses

    def add_node(self, host):
        if host == self.host:
            return

        if host not in self.full_nodes:
            self.broadcast_node(host)
            self.full_nodes.add(host)

    def broadcast_node(self, host):
        self.request_nodes_from_all()
        bad_nodes = set()
        data = {
            "host": host
        }

        for node in self.full_nodes:
            if node == self.host:
                continue
            url = self.NODES_URL.format(node, self.FULL_NODE_PORT)
            try:
                requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)
        for node in bad_nodes:
            self.remove_node(node)
        bad_nodes.clear()
        return

    def load_blockchain(self, block_path):
        # TODO load blockchain from path
        pass

    def synchronize(self):
        my_latest_block = self.blockchain.get_latest_block()
        """
        latest_blocks = {
            index1 : {
                current_hash1 : [node1, node2],
                current_hash2 : [node3]
            },
            index2 : {
                current_hash3 : [node4]
            }
        }
        """
        latest_blocks = {}

        self.request_nodes_from_all()
        bad_nodes = set()
        for node in self.full_nodes:
            url = self.BLOCK_URL.format(node, self.FULL_NODE_PORT, "latest")
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    remote_latest_block = json.loads(response.json())
                    if remote_latest_block["index"] <= my_latest_block.index:
                        continue
                    if latest_blocks.get(remote_latest_block["index"], None) is None:
                        latest_blocks[remote_latest_block["index"]] = {
                            remote_latest_block["current_hash"]: [node]
                        }
                        continue
                    if latest_blocks[remote_latest_block["index"]].get(remote_latest_block["current_hash"], None) is None:
                        latest_blocks[remote_latest_block["index"]][remote_latest_block["current_hash"]] = [node]
                        continue
                    latest_blocks[remote_latest_block["index"]][remote_latest_block["current_hash"]].append(node)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)
        if len(latest_blocks) > 0:
            for latest_block in sorted(latest_blocks.items(), reverse=True):
                index = latest_block[0]
                current_hashes = latest_block[1]
                success = True
                for current_hash in current_hashes:
                    remote_host = current_hash[1][0]

                    remote_diff_blocks = self.request_blocks_range(
                        remote_host,
                        self.FULL_NODE_PORT,
                        my_latest_block.index + 1,
                        index
                    )
                    if remote_diff_blocks[0].previous_hash == my_latest_block.current_hash:
                        # first block in diff blocks fit local chain
                        for block in remote_diff_blocks:
                            result = self.blockchain.add_block(block)
                            if not result:
                                success = False
                                break
                    else:
                        # first block in diff blocks does not fit local chain
                        for i in range(my_latest_block.index, 1, -1):
                            # step backwards and look for the first remote block that fits the local chain
                            block = self.request_block(remote_host, self.FULL_NODE_PORT, str(i))
                            remote_diff_blocks[0:0] = [block]
                            if block.previous_hash == self.blockchain.get_block_by_index(i-1):
                                # found the fork
                                result = self.blockchain.alter_chain(remote_diff_blocks)
                                success = result
                                break
                        success = False
                    if success:
                        break
                if success:
                    break
        return

    def __remove_unconfirmed_transactions(self, transactions):
        for transaction in transactions:
            self.blockchain.remove_unconfirmed_transaction(transaction.tx_hash)

    @app.route('/nodes', methods=['POST'])
    def post_node(self, request):
        body = json.loads(request.content.read())
        self.add_node(body['host'])
        return json.dumps({'success': True})

    @app.route('/nodes', methods=['GET'])
    def get_nodes(self, request):
        nodes = {
            "full_nodes": list(self.full_nodes)
        }
        return json.dumps(nodes)

    @app.route('/status', methods=['GET'])
    def get_status(self, request):
        return json.dumps(config['network'])

    @app.route('/transactions', methods=['POST'])
    def post_transactions(self, request):
        body = json.loads(request.content.read())
        transaction = Transaction(
            body['transaction']['source'],
            body['transaction']['destination'],
            body['transaction']['amount'],
            body['transaction']['fee'],
            body['transaction']['signature'])
        if transaction.tx_hash != body['transaction']['tx_hash']:
            logger.warn("Invalid transaction hash: {} should be {}".format(body['transaction']['tx_hash'], transaction.tx_hash))
            request.setResponseCode(406)
            return json.dumps({'message': 'Invalid transaction hash'})
        return json.dumps({'success': self.blockchain.push_unconfirmed_transaction(transaction)})

    @app.route('/transactions', methods=['GET'])
    def get_transactions(self, request):
        return json.dumps(self.blockchain.get_all_unconfirmed_transactions())

    @app.route('/address/<address>/balance', methods=['GET'])
    def get_balance(self, request, address):
        return json.dumps(self.blockchain.get_balance(address))

    @app.route('/address/<address>/transactions', methods=['GET'])
    def get_transaction_history(self, request, address):
        return json.dumps(self.blockchain.get_transaction_history(address))

    @app.route('/blocks', methods=['POST'])
    def post_block(self, request):
        body = json.loads(request.content.read())
        remote_block = json.loads(body['block'])
        remote_host = body['host']
        transactions = [Transaction(
            transaction['source'],
            transaction['destination'],
            transaction['amount'],
            transaction['fee'],
            transaction['signature'])
            for transaction in remote_block['transactions']
        ]
        block = Block(
            remote_block['index'],
            [Transaction(
                transaction['source'],
                transaction['destination'],
                transaction['amount'],
                transaction['fee'],
                transaction['signature'])
             for transaction in remote_block['transactions']
             ],
            remote_block['previous_hash'],
            remote_block['timestamp'],
            remote_block['nonce']
        )
        if block.current_hash != remote_block['current_hash']:
            request.setResponseCode(406)  # not acceptable
            return json.dumps({'message': 'block rejected due to invalid hash'})
        my_latest_block = self.blockchain.get_latest_block()

        if block.index > my_latest_block.index + 1:
            # new block index is greater than ours
            remote_diff_blocks = self.request_blocks_range(
                remote_host,
                self.FULL_NODE_PORT,
                my_latest_block.index + 1,
                remote_block['index']
            )

            if remote_diff_blocks[0].previous_hash == my_latest_block.current_hash:
                # first block in diff blocks fit local chain
                for block in remote_diff_blocks:
                    result = self.blockchain.add_block(block)
                    if not result:
                        request.setResponseCode(406)  # not acceptable
                        return json.dumps({'message': 'block {} rejected'.format(block.index)})
                self.__remove_unconfirmed_transactions(transactions)
                request.setResponseCode(202)  # accepted
                return json.dumps({'message': 'accepted'})
            else:
                # first block in diff blocks does not fit local chain
                for i in range(my_latest_block.index, 1, -1):
                    # step backwards and look for the first remote block that fits the local chain
                    block = self.request_block(remote_host, self.FULL_NODE_PORT, str(i))
                    remote_diff_blocks[0:0] = [block]
                    if block.previous_hash == self.blockchain.get_block_by_index(i-1):
                        # found the fork
                        result = self.blockchain.alter_chain(remote_diff_blocks)
                        if not result:
                            request.setResponseCode(406)  # not acceptable
                            return json.dumps({'message': 'blocks rejected'})
                        self.__remove_unconfirmed_transactions(transactions)
                        request.setResponseCode(202)  # accepted
                        return json.dumps({'message': 'accepted'})
                request.setResponseCode(406)  # not acceptable
                return json.dumps({'message': 'blocks rejected'})

        elif block.index <= my_latest_block.index:
            # new block index is less than ours
            request.setResponseCode(409)  # conflict
            return json.dumps({'message': 'Block index too low.  Fetch latest chain.'})

        # correct block index. verify txs, hash
        result = self.blockchain.add_block(block)
        if not result:
            request.setResponseCode(406)  # not acceptable
            return json.dumps({'message': 'block {} rejected'.format(block.index)})
        self.__remove_unconfirmed_transactions(transactions)
        request.setResponseCode(202)  # accepted
        return json.dumps({'message': 'accepted'})

    @app.route('/blocks', methods=['GET'])
    def get_blocks(self, request):
        return json.dumps([block.to_json() for block in self.blockchain.get_all_blocks()])

    @app.route('/blocks/<start_block_id>/<end_block_id>', methods=['GET'])
    def get_blocks_range(self, request, start_block_id, end_block_id):
        return json.dumps([block.to_json() for block in self.blockchain.get_blocks_range(start_block_id, end_block_id)])

    @app.route('/block/<block_id>', methods=['GET'])
    def get_block(self, request, block_id):
        if block_id == "latest":
            return json.dumps(self.blockchain.get_latest_block().to_json())
        return json.dumps(self.blockchain.get_block_by_index(block_id).to_json())


if __name__ == "__main__":
    pass
