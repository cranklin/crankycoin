import sys
import zmq

from crankycoin import config, logger


class Queue(object):
    QUEUE_BIND_IN = config['user']['queue_bind_in']
    QUEUE_BIND_OUT = config['user']['queue_bind_out']
    QUEUE_PROCESSING_WORKERS = config['user']['queue_processing_workers']

    @classmethod
    def start_queue(cls):
        try:
            context = zmq.Context(1)
            # Socket facing producers
            frontend = context.socket(zmq.PULL)
            frontend.bind(cls.QUEUE_BIND_IN)
            # Socket facing consumers
            backend = context.socket(zmq.PUSH)
            backend.bind(cls.QUEUE_BIND_OUT)

            zmq.proxy(frontend, backend)

        except Exception as e:
            logger.error("could not start queue: %s", e)
            raise

    @classmethod
    def enqueue(cls, msg):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect(cls.QUEUE_BIND_IN)
        socket.send_json(msg)

    @classmethod
    def dequeue(cls):
        context = zmq.Context()
        socket = context.socket(zmq.PULL)
        socket.connect(cls.QUEUE_BIND_OUT)
        return socket.recv_json()
