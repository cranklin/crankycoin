from enum import Enum


class MessageType(Enum):

    BLOCK_HEADER = 1
    BLOCK_INV = 2
    UNCONFIRMED_TRANSACTION = 3
    UNCONFIRMED_TRANSACTION_INV = 4
    BLOCK_TRANSACTION_INV = 5
    SYNCHRONIZE = 6


class TransactionType(Enum):

    GENESIS = 1
    COINBASE = 2
    STANDARD = 3
    ASSET_CREATION = 4
    ASSET_ADDENDUM = 5
    ORDER = 6
    FILL = 7
    CANCEL_ORDER = 8
    REGISTRATION = 9
