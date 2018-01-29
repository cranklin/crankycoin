class BlockchainException(Exception):

    def __init__(self, index, message):
        super(BlockchainException, self).__init__(message)
        self.index = index


class InvalidHash(BlockchainException):
    pass


class ChainContinuityError(BlockchainException):
    pass


class InvalidTransactions(BlockchainException):
    pass


class GenesisBlockMismatch(BlockchainException):
    pass


class InvalidTransactionHash(Exception):
    pass


class InvalidCoinbaseTransaction(BlockchainException):
    pass
