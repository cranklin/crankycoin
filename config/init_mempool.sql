CREATE TABLE IF NOT EXISTS unconfirmed_transactions(
    hash CHAR(32) NOT NULL,
    src CHAR(70) NOT NULL,
    dest CHAR(70) NOT NULL,
    amount REAL NOT NULL,
    fee REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    signature CHAR(32) NOT NULL,
    type INTEGER NOT NULL,
    asset CHAR(32) NOT NULL,
    data TEXT NOT NULL,
    prevHash CHAR(32) NOT NULL,
    PRIMARY KEY (hash)
) WITHOUT ROWID;

CREATE INDEX idx_unconfirmed_transactions_fee ON unconfirmed_transactions(fee);