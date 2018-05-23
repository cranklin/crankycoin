import zmq
import random
import sys
import time

from crankycoin import config, logger

class PubSub(object):

    @classmethod
    def start_pubsub(cls):
        try:
            port = "5556"
            if len(sys.argv) > 1:
                port =  sys.argv[1]
                int(port)

            context = zmq.Context()
            server_socket = context.socket(zmq.PUB)
            server_socket.bind("tcp://*:%s" % port)

            client_socket = context.socket(zmq.SUB)
