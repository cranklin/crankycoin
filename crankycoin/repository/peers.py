import os
import sqlite3

from crankycoin import config


class Peers(object):

    PEER_DB = config['user']['peer_db']
    MAX_PEERS = config['user']['max_peers']
    DOWNTIME_THRESHOLD = config['network']['downtime_threshold']

    def __init__(self):
        self.db_init()
        # TODO: do a health check of each peer

    def db_init(self):
        if not os.path.exists('./data'):
            os.makedirs('./data')
        with sqlite3.connect(self.PEER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(peers)")
            if len(cursor.fetchall()) > 0:
                return
            sql = open('config/init_peers.sql', 'r').read()
            cursor = conn.cursor()
            cursor.executescript(sql)
        return

    def get_peers_count(self):
        sql = 'SELECT count(*) FROM peers WHERE downtime < {}'.format(self.DOWNTIME_THRESHOLD)
        with sqlite3.connect(self.PEER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            count = cursor.fetchone()[0]
        return count

    def get_peer(self, host):
        sql = "SELECT * FROM peers WHERE host='{}'".format(host)
        with sqlite3.connect(self.PEER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            peer = cursor.fetchone()
        return peer if peer is None else peer[0]

    def get_all_peers(self):
        peers = []
        sql = 'SELECT host FROM peers ORDER BY downtime ASC LIMIT {}'.format(self.MAX_PEERS)
        with sqlite3.connect(self.PEER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            for peer in cursor:
                peers.append(peer[0])
        return peers

    def remove_peer(self, host):
        sql = "'DELETE FROM peers WHERE host='{}'".format(host)
        with sqlite3.connect(self.PEER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.rowcount

    def record_downtime(self, host):
        sql = "UPDATE peers SET downtime = downtime + 1 WHERE host='{}'".format(host)
        with sqlite3.connect(self.PEER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.rowcount

    def reset_downtime(self, host):
        sql = "UPDATE peers SET downtime = 0 WHERE host='{}'".format(host)
        with sqlite3.connect(self.PEER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.rowcount

    def add_peer(self, host):
        sql = "INSERT OR IGNORE INTO peers (host, downtime) VALUES ('{}', 0)".format(host)
        with sqlite3.connect(self.PEER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.lastrowid


if __name__ == "__main__":
    pass
