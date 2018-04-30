import json
from bottle import Bottle, response, request, abort

from crankycoin.services.queue import Queue
from crankycoin.models.enums import MessageType
from crankycoin.repository.peers import Peers
from crankycoin.repository.blockchain import Blockchain

permissioned_app = Bottle()


def valid_ip():
    peers = Peers()
    host = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    peer = peers.get_peer(host)
    return True if peer else False


def requires_whitelist(func):
    def wrapper(*a, **ka):
        if not valid_ip():
            abort(401, {'code': 'token_expired', 'description': 'token is expired'})
        return func(*a, **ka)
    return wrapper


@permissioned_app.route('/inbox/', method='POST')
@requires_whitelist
def post_to_inbox():
    body = request.json
    # TODO: validate sender really is who they say they are using signature
    host = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    msg_type = body.get('type')
    if MessageType(msg_type) in MessageType:
        msg = {'host': host, 'type': msg_type, 'data': body.get('data')}
        Queue.enqueue(msg)
        response.status = 200
        return json.dumps({'success': True})
    response.status = 400
    return json.dumps({'success': False})


@permissioned_app.route('/blocks/start/<start_block_height:int>/end/<end_block_height:int>')
@requires_whitelist
def get_blocks_inv(start_block_height, end_block_height):
    blockchain = Blockchain()
    blocks_range = end_block_height - start_block_height
    if blocks_range < 1 or blocks_range > 500:
        response.status = 400
        return json.dumps({'success': False, 'reason': 'Bad request'})
    blocks_inv = blockchain.get_hashes_range(start_block_height, end_block_height)
    if blocks_inv:
        return json.dumps({'blocks_inv': blocks_inv})
    response.status = 404
    return json.dumps({'success': False, 'reason': 'Blocks not found'})


@permissioned_app.route('/transactions/block_hash/<block_hash>')
@requires_whitelist
def get_transactions_index(block_hash):
    blockchain = Blockchain()
    transaction_inv = blockchain.get_transaction_hashes_by_block_hash(block_hash)
    if transaction_inv:
        return json.dumps({'tx_hashes': transaction_inv})
    response.status = 404
    return json.dumps({'success': False, 'reason': 'Transactions Not Found'})


@permissioned_app.route('/blocks/hash/<block_hash>')
@requires_whitelist
def get_block_header_by_hash(block_hash):
    blockchain = Blockchain()
    block_header = blockchain.get_block_header_by_hash(block_hash)
    if block_header is None:
        response.status = 404
        return json.dumps({'success': False, 'reason': 'Block Not Found'})
    return json.dumps(block_header.to_dict())


@permissioned_app.route('/blocks/height/<height:int>')
@requires_whitelist
def get_block_header_by_height(height):
    blockchain = Blockchain()
    if height == "latest":
        block_header = blockchain.get_tallest_block_header()
    else:
        block_header = blockchain.get_block_headers_by_height(height)
    if block_header is None:
        response.status = 404
        return json.dumps({'success': False, 'reason': 'Block Not Found'})
    return json.dumps(block_header.to_dict())
