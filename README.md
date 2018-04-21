# Cranky Coin
[![Build Status](https://travis-ci.org/cranklin/crankycoin.svg?branch=master)](https://travis-ci.org/cranklin/crankycoin)

Cranky Coin is a simple blockchain, cryptocurrency, wallet implementation

## Getting Started

```
# apt-get install pip
# pip install virtualenv
# virtualenv venv
# . venv/bin/activate
# pip install -r requirements.txt
# pip install -r requirements-dev.txt
```

**Generating a wallet**

```
# python run.py client
Cranky Coin (CRNK) wallet > publickey
```
*copy your public key*
```
Cranky Coin (CRNK) wallet > privatekey
```
*copy your private key*

**Running a full node**
```
Cranky Coin (CRNK) wallet > quit
# python ./tools/encrypt.py
```
*enter a secure passphrase*
```
Choose a passphrase:
Re-enter your passphrase:
```
*enter your private key*
```
Secret:
Encrypted private key:
```
*copy your encrypted private key*

*edit config/config.yaml and populate the fields in the `user` section*

```
# python run.py full
Cranky Coin (CRNK) full node > help
```

**Running a mining node**
```
Cranky Coin (CRNK) full node > mine start
Cranky Coin (CRNK) full node > mine stop
```
