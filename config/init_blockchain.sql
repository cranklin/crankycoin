CREATE TABLE IF NOT EXISTS blocks(
    hash CHAR(32) NOT NULL,
    prevHash CHAR(32) NOT NULL,
    merkleRoot CHAR(32) NOT NULL,
    height INTEGER NOT NULL,
    nonce INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,
    version INTEGER NOT NULL,
    branch INTEGER DEFAULT 0,
    PRIMARY KEY (hash),
    UNIQUE (prevHash, branch) ON CONFLICT ROLLBACK
) WITHOUT ROWID;

CREATE INDEX idx_blocks_height ON blocks(height);
CREATE INDEX idx_blocks_prevHash ON blocks(prevHash);

CREATE TABLE IF NOT EXISTS transactions(
    hash CHAR(32) NOT NULL,
    src CHAR(70) NOT NULL,
    dest CHAR(70) NOT NULL,
    amount REAL NOT NULL,
    fee REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    signature CHAR(32) NOT NULL,
    type INTEGER NOT NULL,
    blockHash CHAR(32) NOT NULL,
    asset CHAR(32) NOT NULL,
    data TEXT NOT NULL,
    branch INTEGER DEFAULT 0,
    prevHash CHAR(32) NOT NULL,
    PRIMARY KEY (hash, branch),
    UNIQUE (prevHash, branch) ON CONFLICT ROLLBACK
) WITHOUT ROWID;

CREATE INDEX idx_transactions_src ON transactions(src);
CREATE INDEX idx_transactions_dest ON transactions(dest);
CREATE INDEX idx_transactions_blockHash ON transactions(blockHash);
CREATE INDEX idx_transactions_type_asset ON transactions(type, asset);

CREATE TABLE IF NOT EXISTS branches(
    id INTEGER PRIMARY KEY,
    currentHash CHAR(32),
    currentHeight INTEGER
);

--INSERT INTO branches (id, currentHash, currentHeight)
--    VALUES (0, 'd30051890fe899813f441bd1e93d34790cbb44702668abca4cd8a380aa90e943', 1);
--
--INSERT INTO transactions (
--    hash, src, dest, amount, fee, timestamp, signature, type, blockHash, asset, data, branch, prevHash) VALUES (
--    '96409c929a70a52f1219b3eb3b064c9351f744b8e5023240013f30be572ac70a', '0',
--    '03dd1e57d05d9cab1d8d9b727568ad951ac2d9ecd082bc36f69e021b8427812924', 50, 0, 1524038353, '', 1,
--    'd30051890fe899813f441bd1e93d34790cbb44702668abca4cd8a380aa90e943',
--    '29bb7eb4fa78fc709e1b8b88362b7f8cb61d9379667ad4aedc8ec9f664e16680', '', 0, '0'
--);
--INSERT INTO transactions (
--    hash, src, dest, amount, fee, timestamp, signature, type, blockHash, asset, data, branch, prevHash) VALUES (
--    'ef5a5850b5377ee4f5a4ca953ed04b35d0910e886c121b565c1c4012e26636b0', '0',
--    '03dd1e57d05d9cab1d8d9b727568ad951ac2d9ecd082bc36f69e021b8427812924', 1000000, 0, 1524038329, '', 0,
--    'd30051890fe899813f441bd1e93d34790cbb44702668abca4cd8a380aa90e943',
--    '29bb7eb4fa78fc709e1b8b88362b7f8cb61d9379667ad4aedc8ec9f664e16680', '', 0, '0'
--);
--
--INSERT INTO blocks (hash, prevHash, merkleRoot, height, nonce, timestamp, version, branch) VALUES (
--    'd30051890fe899813f441bd1e93d34790cbb44702668abca4cd8a380aa90e943', '',
--    '4f27a78679e35963289fae864d1d6ec9b26848160a0d09e6e8fcd56e9ee969b0', 1, 0, 1524041935, 1, 0
--);