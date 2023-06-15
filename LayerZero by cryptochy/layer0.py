import random

from web3 import Web3
import requests
import time
import json
import datetime
from tx_l0 import *
import sqlite3
from json_req import *
import hashlib
from sys import exit
from pick import pick


web3 = Web3(Web3.HTTPProvider('INFURA URL HERE'))
keys = []
last_gas = 0
sleep_time = 2
config = {}
total_fees = {106: {0: 0.0, 106: 0, 109: 0, 110: 0},
              109: {0: 0, 106: 0, 109: 0, 110: 0},
              110: {0: 0, 106: 0, 109: 0, 110: 0}}  # from: to, to, to, to
next_fee_update = 0
stargate_chains = {'avalanche': 106, 'polygon': 109, 'arbitrum': 110, 'optimism': 111, 'fantom': 112}


def fee_parser():
    try:
        ava_fees = requests.post('https://api.avax.network/ext/bc/C/rpc', json=avalanche_fee_req)
        pol_fees = requests.post('https://poly-rpc.gateway.pokt.network', json=polygon_fee_req)
        arb_fees = requests.post('https://arb1.arbitrum.io/rpc', json=arbitrum_fee_req)

        ava_gas = int(ava_fees.json()[0]['result'], 16) / 1e18 * 18 * 400_000
        pol_gas = int(pol_fees.json()[0]['result'], 16) / 1e18 * 1.1 * 400_000
        arb_gas = int(arb_fees.json()[0]['result'], 16) / 1e18 * 1800 * 1_400_000
        for a in ava_fees.json():
            if a['id'] == 111 or a['id'] == 112:
                continue
            if len(a['result']) > 68:
                total_fees[106][a['id']] = int(a['result'][:-64], 16) / 1e18 * 18 + ava_gas
            else:
                total_fees[106][a['id']] = ava_gas

        for a in pol_fees.json():
            if a['id'] == 111 or a['id'] == 112:
                continue
            if len(a['result']) > 68:
                total_fees[109][a['id']] = int(a['result'][:-64], 16) / 1e18 * 1.1 + pol_gas
            else:
                total_fees[109][a['id']] = pol_gas

        for a in arb_fees.json():
            if a['id'] == 111 or a['id'] == 112:
                continue
            if len(a['result']) > 68:
                total_fees[110][a['id']] = int(a['result'][:-64], 16) / 1e18 * 1800 + arb_gas
            else:
                total_fees[110][a['id']] = arb_gas
    except Exception as error:
        print('Update fees error')
        print(error)
        # traceback.print_exc()


def tick():
    global sleep_time, config

    con = sqlite3.connect("multi.db")
    cur = con.cursor()

    weights = []
    res = cur.execute(f"SELECT transfers, lastactivitydate FROM layerzero")
    wallet_transfers = []
    wallet_lastdate = []
    for x in res:
        wallet_transfers.append(x[0])
        lad = abs(int(time.time()) - x[1])
        if lad > 1000000:
            lad = 100000
        wallet_lastdate.append(lad)

    _wallet_lastdate_min = min(wallet_lastdate)
    _wallet_lastdate_max = max(wallet_lastdate) - _wallet_lastdate_min + 1
    for x in range(len(wallet_lastdate)):
        wallet_lastdate[x] -= _wallet_lastdate_min
        wallet_lastdate[x] /= _wallet_lastdate_max
        wallet_lastdate[x] += random.randint(100, 1000) / 10000

    _wallet_transfers_max = max(wallet_transfers)
    if _wallet_transfers_max != 0:
        for x in range(len(wallet_transfers)):
            weights.append((1 - wallet_transfers[x] / _wallet_transfers_max) + (wallet_lastdate[x] * 0.5))
    else:
        for x in range(len(wallet_transfers)):
            weights.append((1 - wallet_transfers[x]) + (wallet_lastdate[x] * 0.5))

    _transfers = int(config['MAX_TX']) + 1
    while _transfers > int(config['MAX_TX']):
        pi = random.choices(keys, weights=weights)[0]
        address_wallet = web3.eth.account.from_key(pi).address
        res = cur.execute(f"SELECT transfers FROM layerzero WHERE wallet = '{address_wallet}'")
        _transfers = res.fetchone()[0]

    print('Wallet', address_wallet)

    balance = {'avalanche': balance_checker(address_wallet, 'avalanche'), 'polygon': balance_checker(address_wallet, 'polygon'),
               'arbitrum': balance_checker(address_wallet, 'arbitrum')}

    positive_balances = []
    for x in balance:
        if balance[x] > int(int(config['MIN_AMOUNT']) * 1e6):
            positive_balances.append(x)

    if len(positive_balances) > 0:
        res = cur.execute(f"SELECT lastfrom FROM layerzero WHERE wallet = '{address_wallet}'")
        last_chain = res.fetchone()[0]

        from_chain = random.choice(positive_balances)

        _fee_list = total_fees[stargate_chains[from_chain]].copy()
        _fee_list.pop(0)
        _fee_list.pop(stargate_chains[from_chain])
        __fee_list = _fee_list.copy()
        for x in _fee_list:
            if _fee_list[x] > 1:
                __fee_list.pop(x)
        _fee_list = __fee_list

        if random.choice([True, True, False]):
            to_chain = min(_fee_list, key=_fee_list.get)
        else:
            to_chain = random.choice(list(_fee_list.keys()))

        if last_chain != 0:
            while to_chain == last_chain:
                to_chain = random.choice(list(_fee_list.keys()))

        for x in stargate_chains.keys():  # converts from 1xx to chain name
            if stargate_chains[x] == to_chain:
                to_chain = x

        _amount = random.randint(int(balance[from_chain] * 0.7), balance[from_chain])
        if _amount < int(int(config['MIN_AMOUNT']) * 1e6):
            _amount = balance[from_chain]

        success = bridge(pi, from_chain, _amount, to_chain)
        if type(success) is not tuple and success:
            res = cur.execute(f"SELECT transfers FROM layerzero WHERE wallet = '{address_wallet}'")
            transfers = res.fetchone()[0]

            cur.execute(
                f"UPDATE layerzero SET transfers = {transfers + 1}, lastactivitydate = {int(time.time())}, lastfrom = {stargate_chains[from_chain]} WHERE wallet = '{address_wallet}'")
            con.commit()

            cur.execute(
                f"INSERT INTO layerzero_tx(wallet, from_chain, to_chain, amount, time) VALUES('{address_wallet}', '{from_chain}', '{to_chain}', '{_amount / 1e6}', {int(time.time())})")
            con.commit()
        else:
            if type(success) is not tuple:
                sleep_time = random.randint(int(config['MIN_TIME']), int(config['MAX_TIME']))
            else:
                sleep_time = 10
    else:
        print(address_wallet, 'Wallet without positive balances for L0')
        sleep_time = 10  # passing next sleep


def stargate_swaps():
    global keys, next_fee_update, sleep_time, config
    p = 0
    fee_parser()
    next_fee_update = 30
    while True:
        print('\n', datetime.datetime.now(), 'Tick', p, '\n')

        if next_fee_update <= 0:
            fee_parser()
            next_fee_update = 30

        sleep_time = random.randint(int(config['MIN_TIME']), int(config['MAX_TIME']))
        try:
            tick()
        except Exception as error:
            print('Tick error', p)
            traceback.print_exc()

        p += 1
        print(f'Waiting before next tx {sleep_time} seconds. Approx at {datetime.datetime.now() + datetime.timedelta(seconds=sleep_time)}')
        next_fee_update -= sleep_time
        time.sleep(sleep_time)


def start(_config):
    global keys, next_fee_update, sleep_time, config
    config = _config

    conn = sqlite3.connect('multi.db')
    c = conn.cursor()
    c.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="layerzero"')
    res = c.fetchone()
    if res is None:
        c.execute('CREATE TABLE "layerzero" ("id" INTEGER, "wallet" TEXT, "transfers" INTEGER, "lastactivitydate" INTEGER, "liquidity" INTEGER, "staking" INTEGER, "lastfrom" INTEGER, PRIMARY KEY("id" AUTOINCREMENT))')
        c.execute('CREATE TABLE "layerzero_tx" ("id" INTEGER, "wallet" TEXT, "from_chain" TEXT, "to_chain" TEXT, "amount" TEXT, "time" INTEGER, PRIMARY KEY("id" AUTOINCREMENT))')
        conn.commit()

        keys = []
        with open('private_keys.txt', 'r') as file:
            for line in file.readlines():
                keys.append(line.rstrip())

        for x in keys:
            address_wallet = web3.eth.account.from_key(x).address
            conn = sqlite3.connect('multi.db')
            c = conn.cursor()
            c.execute(f"INSERT INTO layerzero(wallet, transfers, lastactivitydate, liquidity, staking, lastfrom) VALUES('{address_wallet}', 0, 1682888400, 0, 0, 0, 0)")
            conn.commit()

    keys = []
    with open('private_keys.txt', 'r') as file:
        for line in file.readlines():
            keys.append(line.rstrip())

    option, index = pick(['Stargate swaps', 'Refactor database'], 'Select run function', indicator='>', default_index=0)
    print('You select', option.lower())

    match option:
        case 'Stargate swaps':
            stargate_swaps()
        case 'Refactor database':
            conn = sqlite3.connect('multi.db')
            c = conn.cursor()
            c.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="layerzero"')
            res = c.fetchone()
            if res is None:
                c.execute(
                    'CREATE TABLE "layerzero" ("id" INTEGER, "wallet" TEXT, "transfers" INTEGER, "lastactivitydate" INTEGER, "liquidity" INTEGER, "staking" INTEGER, "lastfrom" INTEGER, PRIMARY KEY("id" AUTOINCREMENT))')
                c.execute(
                    'CREATE TABLE "layerzero_tx" ("id" INTEGER, "wallet" TEXT, "from_chain" TEXT, "to_chain" TEXT, "amount" TEXT, "time" INTEGER, PRIMARY KEY("id" AUTOINCREMENT))')
                conn.commit()

                for x in keys:
                    address_wallet = web3.eth.account.from_key(x).address
                    c.execute(
                        f"INSERT INTO layerzero(wallet, transfers, lastactivitydate, liquidity, staking, lastfrom) VALUES('{address_wallet}', 0, 1682888400, 0, 0, 0)")
                    conn.commit()
            else:
                c.execute('SELECT * FROM layerzero')
                res = c.fetchall()
                prev = {}
                for x in res:
                    prev[x[1]] = x

                c.execute('DELETE FROM layerzero')
                conn.commit()
                c.execute("UPDATE sqlite_sequence SET seq = 0")
                for x in keys:
                    address_wallet = web3.eth.account.from_key(x).address
                    if address_wallet in prev:
                        _prev = prev[address_wallet]
                        c.execute(
                            f"INSERT INTO layerzero(wallet, transfers, lastactivitydate, liquidity, staking, lastfrom) VALUES('{address_wallet}', {_prev[2]}, {_prev[3]}, {_prev[4]}, {_prev[5]}, {_prev[6]})")
                        conn.commit()
                    else:
                        c.execute(
                            f"INSERT INTO layerzero(wallet, transfers, lastactivitydate, liquidity, staking, lastfrom) VALUES('{address_wallet}', 0, 1682888400, 0, 0, 0)")
                        conn.commit()

            print('Database updated. Restart software')
