import hashlib
import json
import pyelliptic
import random
import requests
import datetime

class Client(object):
    """
    Never do this with an actual private key.  I'm only including it in the comments because this is a demonstration

    private key: 'a3dab7c3c83d19f6caadc82e748f08e53d07974ececa450c1d8d3d01fb39b9aa'
    public key: '0442c0fe0050d53426395a046e3c4e6216189666544005567b0b3ed3dcf0151a1ac5b926bdfe93f15ecea3230951ed4151dadab28f2906d0052febea1b7453ce6f'
    """

    NODE_TYPE = "client"

    def __init__(self, private_key=None, public_key=None):
        self.private_key = private_key.decode('hex')
        self.public_key = public_key.decode('hex')
        self.generate_ecc_instance(private_key, public_key)

    def generate_ecc_instance(self):
        if self.private_key is None or self.public_key is None:
            print "ECC keys not provided.  Generating ECC keys"
            self.ecc = pyelliptic.ECC(curve='secp256k1')
            self.private_key = self.ecc.get_privkey()
            self.public_key = self.ecc.get_pubkey()
        else:
            self.ecc = pyelliptic.ECC(curve='secp256k1', privkey=self.private_key, pubkey=self.public_key)
        return

    def get_pubkey(self, hex=True):
        return self.ecc.get_pubkey().encode('hex') if hex else self.ecc.get_pubkey()

    def get_privkey(self, hex=True):
        return self.ecc.get_privkey().encode('hex') if hex else self.ecc.get_privkey()

    def sign(self, message):
        return self.ecc.sign(message)

    def verify(self, signature, message, public_key=None):
        if public_key is not None:
            return pyelliptic.ECC(pubkey=public_key.decode('hex')).verify(signature, message)
        return self.ecc.verify(signature, message)

    def get_balance(self):
        pass

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
