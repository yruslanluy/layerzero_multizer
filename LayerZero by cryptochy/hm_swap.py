from web3 import Web3
import time
import json
import random
import requests
from contracts import polygon_usdc_abi
# from tx_l0 import rpc
import traceback


rpc = [
    {'chain': 'eth', 'chain_id': 1, 'rpc': 'https://rpc.ankr.com/eth', 'scan': 'https://etherscan.io/tx/',
     'token': 'ETH'},
    {'chain': 'optimism', 'chain_id': 10, 'rpc': 'https://rpc.ankr.com/optimism',
     'scan': 'https://optimistic.etherscan.io/tx/', 'token': 'ETH'},
    {'chain': 'bnb', 'chain_id': 56, 'rpc': 'https://bsc-dataseed.binance.org', 'scan': 'https://bscscan.com/tx/',
     'token': 'BNB'},
    {'chain': 'polygon', 'chain_id': 137, 'rpc': 'https://polygon-rpc.com', 'scan': 'https://polygonscan.com/tx/',
     'token': 'MATIC'},
    {'chain': 'arbitrum', 'chain_id': 42161, 'rpc': 'https://arb1.arbitrum.io/rpc', 'scan': 'https://arbiscan.io/tx/',
     'token': 'ETH'},
    {'chain': 'avalanche', 'chain_id': 43114, 'rpc': 'https://api.avax.network/ext/bc/C/rpc',
     'scan': 'https://snowtrace.io/tx/', 'token': 'AVAX'},
    {'chain': 'nova', 'chain_id': 42170, 'rpc': 'https://nova.arbitrum.io/rpc', 'scan': 'https://nova.arbiscan.io/tx/',
     'token': 'ETH'},
    {'chain': 'fantom', 'chain_id': 250, 'rpc': 'https://rpc.ankr.com/fantom', 'scan': 'https://ftmscan.com/tx/',
     'token': 'FTM'}
]

web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
web3_polygon = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
web3_arbitrum = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
web3_optimism = Web3(Web3.HTTPProvider('https://mainnet.optimism.io'))
web3_avalanche = Web3(Web3.HTTPProvider('https://avalanche.blockpi.network/v1/rpc/public'))
chain_api = {'avalanche': web3_avalanche, 'polygon': web3_polygon, 'arbitrum': web3_arbitrum, 'optimism': web3_optimism}


def inch_approve(private_key, from_token_address, chain):
    try:
        match chain:
            case 'polygon':
                _scan = rpc[3]['scan']
                chain_id = rpc[3]['chain_id']
            case 'arbitrum':
                _scan = rpc[4]['scan']
                chain_id = rpc[4]['chain_id']
            case 'optimism':
                _scan = rpc[1]['scan']
                chain_id = rpc[1]['chain_id']
            case 'fantom':
                _scan = rpc[7]['scan']
                chain_id = rpc[7]['chain_id']
            case 'avalanche':
                _scan = rpc[5]['scan']
                chain_id = rpc[5]['chain_id']
            case _:
                print('provided wrong chain for approve')
                raise ValueError

        _web3 = chain_api[chain]

        account = _web3.eth.account.from_key(private_key)
        address_wallet = account.address

        inch_url = f'https://api.1inch.io/v4.0/{chain_id}/approve/transaction?tokenAddress={Web3.to_checksum_address(from_token_address)}&amount=115792089237316195423570985008687907853269984665640564039457584007913129639935'
        json_data = requests.get(inch_url).json()
        nonce = _web3.eth.get_transaction_count(address_wallet)

        tx = {
            'chainId': chain_id,
            "nonce": nonce,
            "to": _web3.to_checksum_address(json_data["to"]),
            "data": json_data["data"],
            "gasPrice": int(_web3.eth.gas_price * 1.02),
            "from": Web3.to_checksum_address(address_wallet)
        }
        gas_limit = _web3.eth.estimate_gas(tx)
        tx['gas'] = gas_limit

        signed_tx = _web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = _web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f'Token {from_token_address} approved for 1inch in {chain} // {_scan}{_web3.to_hex(tx_hash)}')
        return True
    except Exception as error:
        print('Error: 1inch approve failed // Token:', from_token_address, chain)
        print(error)
        # traceback.print_exc()
        return False


#  currently don't support swap from native token
def inch_swap(private_key, amount_to_swap, from_token_address, to_token_address, chain):
    try:
        match chain:
            case 'polygon':
                _scan = rpc[3]['scan']
                chain_id = rpc[3]['chain_id']
            case 'arbitrum':
                _scan = rpc[4]['scan']
                chain_id = rpc[4]['chain_id']
            case 'optimism':
                _scan = rpc[1]['scan']
                chain_id = rpc[1]['chain_id']
                print('code not optimized for optimism, change approve address for optimism')
                return ValueError
            case 'fantom':
                _scan = rpc[7]['scan']
                chain_id = rpc[7]['chain_id']
            case 'avalanche':
                _scan = rpc[5]['scan']
                chain_id = rpc[5]['chain_id']
            case _:
                print('provided wrong chain for approve')
                raise ValueError

        _web3 = chain_api[chain]

        # if from_token_address
        from_token_contract = _web3.eth.contract(address=_web3.to_checksum_address(from_token_address), abi=polygon_usdc_abi)
        from_symbol = from_token_contract.functions.symbol().call()

        account = _web3.eth.account.from_key(private_key)
        address_wallet = account.address

        allowance = from_token_contract.functions.allowance(
            Web3.to_checksum_address(address_wallet),
            Web3.to_checksum_address(Web3.to_checksum_address('0x1111111254fb6c44bAC0beD2854e76F90643097d'))
        ).call()
        if allowance < 1000_000_000:
            _approved = inch_approve(private_key, from_token_address, chain)
            if not _approved:
                return False
            time.sleep(random.randint(30, 40))

        inch_url = f'https://api.1inch.io/v4.0/{chain_id}/swap?fromTokenAddress={from_token_address}&toTokenAddress={to_token_address}&amount={amount_to_swap}&fromAddress={address_wallet}&slippage=2'
        json_data = requests.get(inch_url).json()

        try:
            tx = json_data['tx']
        except:
            print('Error: 1inch swap with tx', json_data)
            # print(inch_url)
            return False

        try:
            to_token_contract = _web3.eth.contract(address=_web3.to_checksum_address(to_token_address), abi=polygon_usdc_abi)
            to_symbol = to_token_contract.functions.symbol().call()
        except:
            to_symbol = 'native coin'

        nonce = _web3.eth.get_transaction_count(address_wallet)

        tx['nonce'] = nonce
        tx['to'] = Web3.to_checksum_address(tx['to'])
        tx['gasPrice'] = int(float(tx['gasPrice']) * 1.02)
        tx['value'] = int(tx['value'])
        tx['chainId'] = chain_id

        signed_tx = _web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = _web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f'1inch swap {from_symbol} to {to_symbol} in {chain} // Amount: {round(amount_to_swap / 1e6, 6)} // {_scan}{_web3.to_hex(tx_hash)}')
        return True
    except Exception as error:
        print('Error: 1inch swap failed //', from_token_address, '>', to_token_address, chain)
        print(error)
        # traceback.print_exc()
        return False
