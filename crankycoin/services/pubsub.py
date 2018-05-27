import zmq
import time

from crankycoin import config, logger

"""
Experimental.  
"""
class PubSub(object):

    PUBSUB_PORT = config['network']['full_node_port']

    @classmethod
    def sync_with_subscriber(cls, bind_to):
        # use bind socket + 1
        sync_with = ':'.join(bind_to.split(':')[:-1] +
                             [str(int(bind_to.split(':')[-1]) + 1)])
        ctx = zmq.Context.instance()
        s = ctx.socket(zmq.REP)
        s.bind(sync_with)
        print("Waiting for subscriber to connect...")
        s.recv()
        print("   Done.")
        s.send('GO')

    @classmethod
    def sync_with_publisher(cls, connect_to):
        # use connect socket + 1
        sync_with = ':'.join(connect_to.split(':')[:-1] +
                             [str(int(connect_to.split(':')[-1]) + 1)]
                             )
        ctx = zmq.Context.instance()
        s = ctx.socket(zmq.REQ)
        s.connect(sync_with)
        s.send('READY')
        s.recv()

    @classmethod
    def start_publisher(cls):
        try:
            bind_to = "tcp://*:{}".format(cls.PUBSUB_PORT)
            ctx = zmq.Context()
            s = ctx.socket(zmq.PUB)
            s.bind(bind_to)

            #cls.sync_with_subscriber(bind_to)
        except Exception as e:
            logger.error("could not start publishing server: %s", e.message)
            raise

        print("Publishing...")
        while True:
            a = time.clock()
            s.send_string(str(a))

    @classmethod
    def start_subscriber(cls):
        try:
            connect_to = "tcp://localhost:{}".format(cls.PUBSUB_PORT)
            array_count = 10
            ctx = zmq.Context()
            s = ctx.socket(zmq.SUB)
            s.connect(connect_to)
            s.setsockopt(zmq.SUBSCRIBE,'')

            #cls.sync_with_publisher(connect_to)
        except Exception as e:
            logger.error("could not start subscribe: %s", e.message)
            raise

        print("Listening...")
        while True:
            a = s.recv_string()
            print(a)

