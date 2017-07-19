import datetime
import hashlib
import json


class Transaction(object):

    def __init__(self, source, destination, amount, signature):
        self.source = source
        self.destination = destination
        self.amount = amount
        self.timestamp = datetime.datetime.utcnow().isoformat()
        self.signature = signature
        self.tx_hash = self.calculate_tx_hash()

    def calculate_tx_hash(self):
        """
        Calculates sha-256 hash of transaction (source, destination, amount, timestamp, signature)

        :return: sha256 hash
        :rtype: str
        """
        # pop hash so method can calculate transactions pre or post hash
        data = {
            "source": self.source,
            "destination": self.destination,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature
        }
        data_json = json.dumps(data, sort_keys=True)
        hash_object = hashlib.sha256(data_json)
        return hash_object.hexdigest()

    def to_signable(self):
        return ":".join((self.source, self.destination, str(self.amount), str(self.timestamp)))

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __repr__(self):
        return "<Transaction {}>".format(self.tx_hash)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other