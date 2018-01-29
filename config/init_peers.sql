CREATE TABLE IF NOT EXISTS peers(
    host CHAR(100) NOT NULL,
    downtime INT NOT NULL,
    PRIMARY KEY (host)
);

INSERT INTO peers (host, downtime) VALUES ('127.0.0.1', 0);
INSERT INTO peers (host, downtime) VALUES ('127.0.0.2', 0);