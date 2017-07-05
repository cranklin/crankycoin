import hashlib
import json
import pyelliptic
import random
import requests

from blockchain import *
from klein import Klein
from twisted.internet import threads

FULL_NODE_PORT = "30013"
NODES_URL = "http://{}:{}/nodes"
TRANSACTIONS_URL = "http://{}:{}/transactions"
BLOCK_URL = "http://{}:{}/block/{}"
BLOCKS_RANGE_URL = "http://{}:{}/blocks/{}/{}"
BLOCKS_URL = "http://{}:{}/blocks"
TRANSACTION_HISTORY_URL = "http://{}:{}/address/{}/transactions"
BALANCE_URL = "http://{}:{}/address/{}/balance"


class NodeMixin(object):
    full_nodes = {"127.0.0.1"}

    def request_nodes(self, node, port):
        url = NODES_URL.format(node, port)
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
            all_nodes = self.request_nodes(node, FULL_NODE_PORT)
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
            "transaction": transaction
        }

        for node in self.full_nodes:
            url = TRANSACTIONS_URL.format(node, FULL_NODE_PORT)
            try:
                response = requests.post(url, data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)
        for node in bad_nodes:
            self.remove_node(node)
        bad_nodes.clear()
        return
        # convert to grequests and return list of responses


class FullNode(NodeMixin):
    NODE_TYPE = "full"
    blockchain = None
    app = Klein()

    def __init__(self, host, reward_address, block_path=None):
        self.host = host
        self.request_nodes_from_all()
        self.reward_address = reward_address
        self.broadcast_node(host)
        if block_path is None:
            self.blockchain = Blockchain()
        else:
            self.load_blockchain(block_path)
        self.app.run("localhost", FULL_NODE_PORT)

    def request_block(self, node, port, index="latest"):
        url = BLOCK_URL.format(node, port, index)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                block_dict = json.loads(response.json())
                block = Block(
                    block_dict['index'],
                    block_dict['transactions'],
                    block_dict['previous_hash'],
                    block_dict['current_hash'],
                    block_dict['timestamp'],
                    block_dict['nonce']
                )
                return block
        except requests.exceptions.RequestException as re:
            pass
        return None

    def request_block_from_all(self, index="latest"):
        blocks = []

        full_nodes = self.full_nodes.copy()
        bad_nodes = set()

        for node in full_nodes:
            block = self.request_block(node, FULL_NODE_PORT, index)
            if block is not None:
                blocks.append(block)
            else:
                bad_nodes.add(node)

        for node in bad_nodes:
            self.remove_node(node)
        return blocks

    def request_blocks_range(self, node, port, start_index, stop_index):
        url = BLOCKS_RANGE_URL.format(node, port, start_index, stop_index)
        blocks = []
        try:
            response = requests.get(url)
            if response.status_code == 200:
                blocks_dict = json.loads(response.json())
                for block_dict in blocks_dict:
                    block = Block(
                        block_dict['index'],
                        block_dict['transactions'],
                        block_dict['previous_hash'],
                        block_dict['current_hash'],
                        block_dict['timestamp'],
                        block_dict['nonce']
                    )
                    blocks.append(block)
                return blocks
        except requests.exceptions.RequestException as re:
            pass
        return None

    def request_blockchain(self, node, port):
        url = BLOCKS_URL.format(node, port)
        blocks = []
        try:
            response = requests.get(url)
            if response.status_code == 200:
                blocks_dict = json.loads(response.json())
                for block_dict in blocks_dict:
                    block = Block(
                        block_dict['index'],
                        block_dict['transactions'],
                        block_dict['previous_hash'],
                        block_dict['current_hash'],
                        block_dict['timestamp'],
                        block_dict['nonce']
                    )
                    blocks.append(block)
                return blocks
        except requests.exceptions.RequestException as re:
            pass
        return None

    def mine(self):
        while True:
            block = self.blockchain.mine_block(self.reward_address)
            self.broadcast_block(block)

    def broadcast_block(self, block):
        self.request_nodes_from_all()
        bad_nodes = set()
        data = {
            "block": block,
            "host": self.host
        }

        for node in self.full_nodes:
            url = BLOCKS_URL.format(node, FULL_NODE_PORT)
            try:
                response = requests.post(url, data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)
        for node in bad_nodes:
            self.remove_node(node)
        bad_nodes.clear()
        return
        # convert to grequests and return list of responses

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
            url = NODES_URL.format(node, FULL_NODE_PORT)
            try:
                requests.post(url, data)
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
            url = BLOCK_URL.format(node, FULL_NODE_PORT, "latest")
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    remote_latest_block = response.json()
                    if remote_latest_block["index"] <= my_latest_block["index"]:
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
                        FULL_NODE_PORT,
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
                        for i in range(my_latest_block["index"], 1, -1):
                            # step backwards and look for the first remote block that fits the local chain
                            block = self.request_block(remote_host, FULL_NODE_PORT, str(i))
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

    @app.route('/transactions', methods=['POST'])
    def post_transactions(self, request):
        body = json.loads(request.content.read())
        return json.dumps({'success': self.blockchain.push_unconfirmed_transaction(body['transaction'])})

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
        remote_block = body['block']
        remote_host = body['host']
        block = Block(
            remote_block['index'],
            remote_block['transactions'],
            remote_block['previous_hash'],
            remote_block['current_hash'],
            remote_block['timestamp'],
            remote_block['nonce']
        )
        my_latest_block = self.blockchain.get_latest_block()

        if block.index > my_latest_block["index"] + 1:
            # new block index is greater than ours
            remote_diff_blocks = self.request_blocks_range(
                remote_host,
                FULL_NODE_PORT,
                my_latest_block.index + 1,
                remote_block['index']
            )

            if remote_diff_blocks[0].previous_hash == my_latest_block.current_hash:
                # first block in diff blocks fit local chain
                for block in remote_diff_blocks:
                    result = self.blockchain.add_block(block)
                    if not result:
                        request.setResponseCode(406) # not acceptable
                        return json.dumps({'message': 'block {} rejected'.format(block.index)})
                request.setResponseCode(202) # accepted
                return json.dumps({'message': 'accepted'})
            else:
                # first block in diff blocks does not fit local chain
                for i in range(my_latest_block["index"], 1, -1):
                    # step backwards and look for the first remote block that fits the local chain
                    block = self.request_block(remote_host, FULL_NODE_PORT, str(i))
                    remote_diff_blocks[0:0] = [block]
                    if block.previous_hash == self.blockchain.get_block_by_index(i-1):
                        # found the fork
                        result = self.blockchain.alter_chain(remote_diff_blocks)
                        if not result:
                            request.setResponseCode(406) # not acceptable
                            return json.dumps({'message': 'blocks rejected'})
                        request.setResponseCode(202) # accepted
                        return json.dumps({'message': 'accepted'})
                request.setResponseCode(406) # not acceptable
                return json.dumps({'message': 'blocks rejected'})

        elif block.index <= my_latest_block["index"]:
            # new block index is less than ours
            request.setResponseCode(409) # conflict
            return json.dumps({'message': 'Block index too low.  Fetch latest chain.'})

        # correct block index. verify txs, hash
        result = self.blockchain.add_block(block)
        if not result:
            request.setResponseCode(406) # not acceptable
            return json.dumps({'message': 'block {} rejected'.format(block.index)})
        request.setResponseCode(202) # accepted
        return json.dumps({'message': 'accepted'})

    @app.route('/blocks', methods=['GET'])
    def get_blocks(self, request):
        return json.dumps([block.__dict__ for block in self.blockchain.get_all_blocks()])

    @app.route('/blocks/<start_block_id>/<end_block_id>', methods=['GET'])
    def get_blocks_range(self, request, start_block_id, end_block_id):
        return json.dumps([block.__dict__ for block in self.blockchain.get_blocks_range(start_block_id, end_block_id)])

    @app.route('/block/<block_id>', methods=['GET'])
    def get_block(self, request, block_id):
        if block_id == "latest":
            return json.dumps(self.blockchain.get_latest_block())
        return json.dumps(self.blockchain.get_block_by_index(block_id))


class Client(NodeMixin):
    """
    Never do this with an actual private key.  I'm only including it in the comments because this is a demonstration

    private key: 'a3dab7c3c83d19f6caadc82e748f08e53d07974ececa450c1d8d3d01fb39b9aa'
    public key: '0442c0fe0050d53426395a046e3c4e6216189666544005567b0b3ed3dcf0151a1ac5b926bdfe93f15ecea3230951ed4151dadab28f2906d0052febea1b7453ce6f'
    """
    __private_key__ = None
    __public_key__ = None

    def __init__(self, private_key=None, public_key=None):
        if private_key is not None and public_key is not None:
            self.__private_key__ = private_key.decode('hex')
            self.__public_key__ = public_key.decode('hex')
        self.ecc = self.generate_ecc_instance()

    def generate_ecc_instance(self):
        if self.__private_key__ is None or self.__public_key__ is None:
            print "ECC keys not provided.  Generating ECC keys"
            ecc = pyelliptic.ECC(curve='secp256k1')
            self.__private_key__ = ecc.get_privkey()
            self.__public_key__ = ecc.get_pubkey()
        else:
            ecc = pyelliptic.ECC(curve='secp256k1', privkey=self.__private_key__, pubkey=self.__public_key__)
        return ecc

    def get_pubkey(self, hex=True):
        return self.ecc.get_pubkey().encode('hex') if hex else self.ecc.get_pubkey()

    def get_privkey(self, hex=True):
        return self.ecc.get_privkey().encode('hex') if hex else self.ecc.get_privkey()

    def sign(self, message):
        return self.ecc.sign(message).encode('hex')

    def verify(self, signature, message, public_key=None):
        if public_key is not None:
            return pyelliptic.ECC(curve='secp256k1', pubkey=public_key.decode('hex')).verify(signature.decode('hex'), message)
        return self.ecc.verify(signature, message)

    def get_balance(self):
        url = BALANCE_URL.format(self.get_pubkey())
        try:
            response = requests.get(url)
            return response.json()
        except requests.exceptions.RequestException as re:
            pass
        return None

    def create_transaction(self, to, amount):
        timestamp = datetime.datetime.utcnow().isoformat()
        signature = self.sign(
            self.generate_signable_transaction(
                self.get_pubkey(),
                to,
                amount,
                timestamp))
        transaction = {
            "from": self.get_pubkey(),
            "to": to,
            "amount": amount,
            "signature": signature,
            "timestamp": timestamp,
        }
        transaction["hash"] = self.calculate_transaction_hash(transaction)
        return self.broadcast_transaction(transaction)

    def calculate_transaction_hash(self, transaction):
        """
        Calculates sha-256 hash of transaction

        :param transaction: transaction
        :type transaction: dict(from, to, amount, timestamp, signature, (hash))

        :return: sha256 hash
        :rtype: str
        """
        # pop hash so method can calculate transactions pre or post hash
        data = transaction.copy()
        data.pop("hash", None)
        data_json = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def generate_signable_transaction(self, from_address, to_address, amount, timestamp):
        return ":".join((from_address, to_address, amount, timestamp))


if __name__ == "__main__":
    pass
