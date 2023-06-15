import random

from web3 import Web3
import time
from contracts import *
import traceback
import datetime
import hm_swap
import json
import requests
import hashlib
import multiprocessing
import subprocess
import platform
from sys import exit

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

stargate_chains = {'avalanche': 106, 'polygon': 109, 'arbitrum': 110, 'optimism': 111, 'fantom': 112}

stargate_abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint16","name":"chainId","type":"uint16"},{"indexed":false,"internalType":"bytes","name":"srcAddress","type":"bytes"},{"indexed":false,"internalType":"uint256","name":"nonce","type":"uint256"},{"indexed":false,"internalType":"address","name":"token","type":"address"},{"indexed":false,"internalType":"uint256","name":"amountLD","type":"uint256"},{"indexed":false,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"bytes","name":"payload","type":"bytes"},{"indexed":false,"internalType":"bytes","name":"reason","type":"bytes"}],"name":"CachedSwapSaved","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint16","name":"srcChainId","type":"uint16"},{"indexed":true,"internalType":"bytes","name":"srcAddress","type":"bytes"},{"indexed":true,"internalType":"uint256","name":"nonce","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"srcPoolId","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"dstPoolId","type":"uint256"},{"indexed":false,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"amountSD","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"mintAmountSD","type":"uint256"}],"name":"RedeemLocalCallback","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint8","name":"bridgeFunctionType","type":"uint8"},{"indexed":false,"internalType":"uint16","name":"chainId","type":"uint16"},{"indexed":false,"internalType":"bytes","name":"srcAddress","type":"bytes"},{"indexed":false,"internalType":"uint256","name":"nonce","type":"uint256"}],"name":"Revert","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint16","name":"srcChainId","type":"uint16"},{"indexed":false,"internalType":"uint256","name":"_srcPoolId","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"indexed":false,"internalType":"bytes","name":"to","type":"bytes"},{"indexed":false,"internalType":"uint256","name":"redeemAmountSD","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"mintAmountSD","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"nonce","type":"uint256"},{"indexed":true,"internalType":"bytes","name":"srcAddress","type":"bytes"}],"name":"RevertRedeemLocal","type":"event"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"}],"name":"activateChainPath","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"uint256","name":"_amountLD","type":"uint256"},{"internalType":"address","name":"_to","type":"address"}],"name":"addLiquidity","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"bridge","outputs":[{"internalType":"contract Bridge","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint16","name":"","type":"uint16"},{"internalType":"bytes","name":"","type":"bytes"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"cachedSwapLookup","outputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountLD","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"bytes","name":"payload","type":"bytes"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"bool","name":"_fullMode","type":"bool"}],"name":"callDelta","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint16","name":"_srcChainId","type":"uint16"},{"internalType":"bytes","name":"_srcAddress","type":"bytes"},{"internalType":"uint256","name":"_nonce","type":"uint256"}],"name":"clearCachedSwap","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"uint256","name":"_weight","type":"uint256"}],"name":"createChainPath","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"address","name":"_token","type":"address"},{"internalType":"uint8","name":"_sharedDecimals","type":"uint8"},{"internalType":"uint8","name":"_localDecimals","type":"uint8"},{"internalType":"string","name":"_name","type":"string"},{"internalType":"string","name":"_symbol","type":"string"}],"name":"createPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"uint256","name":"_srcPoolId","type":"uint256"},{"components":[{"internalType":"uint256","name":"credits","type":"uint256"},{"internalType":"uint256","name":"idealBalance","type":"uint256"}],"internalType":"struct Pool.CreditObj","name":"_c","type":"tuple"}],"name":"creditChainPath","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"contract Factory","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint16","name":"_srcPoolId","type":"uint16"},{"internalType":"uint256","name":"_amountLP","type":"uint256"},{"internalType":"address","name":"_to","type":"address"}],"name":"instantRedeemLocal","outputs":[{"internalType":"uint256","name":"amountSD","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"mintFeeOwner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"protocolFeeOwner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"uint8","name":"_functionType","type":"uint8"},{"internalType":"bytes","name":"_toAddress","type":"bytes"},{"internalType":"bytes","name":"_transferAndCallPayload","type":"bytes"},{"components":[{"internalType":"uint256","name":"dstGasForCall","type":"uint256"},{"internalType":"uint256","name":"dstNativeAmount","type":"uint256"},{"internalType":"bytes","name":"dstNativeAddr","type":"bytes"}],"internalType":"struct IStargateRouter.lzTxObj","name":"_lzTxParams","type":"tuple"}],"name":"quoteLayerZeroFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"uint256","name":"_srcPoolId","type":"uint256"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"address payable","name":"_refundAddress","type":"address"},{"internalType":"uint256","name":"_amountLP","type":"uint256"},{"internalType":"bytes","name":"_to","type":"bytes"},{"components":[{"internalType":"uint256","name":"dstGasForCall","type":"uint256"},{"internalType":"uint256","name":"dstNativeAmount","type":"uint256"},{"internalType":"bytes","name":"dstNativeAddr","type":"bytes"}],"internalType":"struct IStargateRouter.lzTxObj","name":"_lzTxParams","type":"tuple"}],"name":"redeemLocal","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint16","name":"_srcChainId","type":"uint16"},{"internalType":"bytes","name":"_srcAddress","type":"bytes"},{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"uint256","name":"_srcPoolId","type":"uint256"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"address","name":"_to","type":"address"},{"internalType":"uint256","name":"_amountSD","type":"uint256"},{"internalType":"uint256","name":"_mintAmountSD","type":"uint256"}],"name":"redeemLocalCallback","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint16","name":"_srcChainId","type":"uint16"},{"internalType":"bytes","name":"_srcAddress","type":"bytes"},{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"uint256","name":"_srcPoolId","type":"uint256"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"uint256","name":"_amountSD","type":"uint256"},{"internalType":"bytes","name":"_to","type":"bytes"}],"name":"redeemLocalCheckOnRemote","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"uint256","name":"_srcPoolId","type":"uint256"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"address payable","name":"_refundAddress","type":"address"},{"internalType":"uint256","name":"_amountLP","type":"uint256"},{"internalType":"uint256","name":"_minAmountLD","type":"uint256"},{"internalType":"bytes","name":"_to","type":"bytes"},{"components":[{"internalType":"uint256","name":"dstGasForCall","type":"uint256"},{"internalType":"uint256","name":"dstNativeAmount","type":"uint256"},{"internalType":"bytes","name":"dstNativeAddr","type":"bytes"}],"internalType":"struct IStargateRouter.lzTxObj","name":"_lzTxParams","type":"tuple"}],"name":"redeemRemote","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint16","name":"_srcChainId","type":"uint16"},{"internalType":"bytes","name":"_srcAddress","type":"bytes"},{"internalType":"uint256","name":"_nonce","type":"uint256"}],"name":"retryRevert","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint16","name":"","type":"uint16"},{"internalType":"bytes","name":"","type":"bytes"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"revertLookup","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"bytes","name":"_srcAddress","type":"bytes"},{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"address payable","name":"_refundAddress","type":"address"},{"components":[{"internalType":"uint256","name":"dstGasForCall","type":"uint256"},{"internalType":"uint256","name":"dstNativeAmount","type":"uint256"},{"internalType":"bytes","name":"dstNativeAddr","type":"bytes"}],"internalType":"struct IStargateRouter.lzTxObj","name":"_lzTxParams","type":"tuple"}],"name":"revertRedeemLocal","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"uint256","name":"_srcPoolId","type":"uint256"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"address payable","name":"_refundAddress","type":"address"}],"name":"sendCredits","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"contract Bridge","name":"_bridge","type":"address"},{"internalType":"contract Factory","name":"_factory","type":"address"}],"name":"setBridgeAndFactory","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"bool","name":"_batched","type":"bool"},{"internalType":"uint256","name":"_swapDeltaBP","type":"uint256"},{"internalType":"uint256","name":"_lpDeltaBP","type":"uint256"},{"internalType":"bool","name":"_defaultSwapMode","type":"bool"},{"internalType":"bool","name":"_defaultLPMode","type":"bool"}],"name":"setDeltaParam","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"address","name":"_feeLibraryAddr","type":"address"}],"name":"setFeeLibrary","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"uint256","name":"_mintFeeBP","type":"uint256"}],"name":"setFees","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_owner","type":"address"}],"name":"setMintFeeOwner","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_owner","type":"address"}],"name":"setProtocolFeeOwner","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"bool","name":"_swapStop","type":"bool"}],"name":"setSwapStop","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"uint16","name":"_weight","type":"uint16"}],"name":"setWeightForChainPath","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint16","name":"_dstChainId","type":"uint16"},{"internalType":"uint256","name":"_srcPoolId","type":"uint256"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"address payable","name":"_refundAddress","type":"address"},{"internalType":"uint256","name":"_amountLD","type":"uint256"},{"internalType":"uint256","name":"_minAmountLD","type":"uint256"},{"components":[{"internalType":"uint256","name":"dstGasForCall","type":"uint256"},{"internalType":"uint256","name":"dstNativeAmount","type":"uint256"},{"internalType":"bytes","name":"dstNativeAddr","type":"bytes"}],"internalType":"struct IStargateRouter.lzTxObj","name":"_lzTxParams","type":"tuple"},{"internalType":"bytes","name":"_to","type":"bytes"},{"internalType":"bytes","name":"_payload","type":"bytes"}],"name":"swap","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint16","name":"_srcChainId","type":"uint16"},{"internalType":"bytes","name":"_srcAddress","type":"bytes"},{"internalType":"uint256","name":"_nonce","type":"uint256"},{"internalType":"uint256","name":"_srcPoolId","type":"uint256"},{"internalType":"uint256","name":"_dstPoolId","type":"uint256"},{"internalType":"uint256","name":"_dstGasForCall","type":"uint256"},{"internalType":"address","name":"_to","type":"address"},{"components":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"eqFee","type":"uint256"},{"internalType":"uint256","name":"eqReward","type":"uint256"},{"internalType":"uint256","name":"lpFee","type":"uint256"},{"internalType":"uint256","name":"protocolFee","type":"uint256"},{"internalType":"uint256","name":"lkbRemove","type":"uint256"}],"internalType":"struct Pool.SwapObj","name":"_s","type":"tuple"},{"internalType":"bytes","name":"_payload","type":"bytes"}],"name":"swapRemote","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"address","name":"_to","type":"address"}],"name":"withdrawMintFee","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_poolId","type":"uint256"},{"internalType":"address","name":"_to","type":"address"}],"name":"withdrawProtocolFee","outputs":[],"stateMutability":"nonpayable","type":"function"}]'

web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
web3_polygon = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
web3_arbitrum = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))
web3_optimism = Web3(Web3.HTTPProvider('https://mainnet.optimism.io'))
web3_avalanche = Web3(Web3.HTTPProvider('https://avalanche.blockpi.network/v1/rpc/public'))

chain_api = {'avalanche': web3_avalanche, 'polygon': web3_polygon, 'arbitrum': web3_arbitrum, 'optimism': web3_optimism}
chain_rate = {'avalanche': 19, 'polygon': 1.1, 'arbitrum': 1800, 'optimism': 1800, 'fantom': 0.5}


def balance_checker(address_wallet, chain):
    address_wallet = Web3.to_checksum_address(address_wallet)
    try:
        match chain:
            case 'polygon':
                balance = polygon_usdc_contract.functions.balanceOf(address_wallet).call()
            case 'arbitrum':
                balance = arbitrum_usdc_contract.functions.balanceOf(address_wallet).call()
            case 'optimism':
                balance = optimism_usdc_contract.functions.balanceOf(address_wallet).call()
            case 'fantom':
                balance = fantom_usdc_contract.functions.balanceOf(address_wallet).call()
            case 'avalanche':
                balance = avalanche_usdc_contract.functions.balanceOf(address_wallet).call()
            case _:
                print('provided wrong chain for check balance')
                raise ValueError
        return balance  # /10e5
    except Exception as error:
        print('Error: Balance checker error', address_wallet, chain)
        print(error)
        # traceback.print_exc()


def check_approve(address_wallet, chain):
    try:
        match chain:
            case 'polygon':
                _contract = polygon_usdc_contract
                _spender = '0x45A01E4e04F14f7A4a6702c74187c5F6222033cd'
            case 'arbitrum':
                _contract = arbitrum_usdc_contract
                _spender = '0x53Bf833A5d6c4ddA888F69c22C88C9f356a41614'
            case 'optimism':
                _contract = optimism_usdc_contract
                _spender = '0xB0D502E938ed5f4df2E681fE6E419ff29631d62b'
            case 'fantom':
                _contract = fantom_usdc_contract
                _spender = '0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6'
            case 'avalanche':
                _contract = avalanche_usdc_contract
                _spender = '0x45A01E4e04F14f7A4a6702c74187c5F6222033cd'
            case _:
                print('provided wrong chain for check approve')
                raise ValueError
        _web3 = chain_api[chain]

        allowance = _contract.functions.allowance(
            Web3.to_checksum_address(address_wallet),
            Web3.to_checksum_address(_spender)
        ).call()
        if allowance > 1000_000_000:
            return True
        else:
            return False
    except Exception as error:
        print('Error: Check allowance error', address_wallet, chain)
        print(error)
        # traceback.print_exc()


def approve(private_key, chain):
    try:
        account = web3.eth.account.from_key(private_key)
        address_wallet = account.address
        match chain:
            case 'polygon':
                _contract = polygon_usdc_contract
                _spender = '0x45A01E4e04F14f7A4a6702c74187c5F6222033cd'
                _scan = rpc[3]['scan']
            case 'arbitrum':
                _contract = arbitrum_usdc_contract
                _spender = '0x53Bf833A5d6c4ddA888F69c22C88C9f356a41614'
                _scan = rpc[4]['scan']
            case 'optimism':
                _contract = optimism_usdc_contract
                _spender = '0xB0D502E938ed5f4df2E681fE6E419ff29631d62b'
                _scan = rpc[1]['scan']
            case 'fantom':
                _contract = fantom_usdc_contract
                _spender = '0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6'
                _scan = rpc[7]['scan']
            case 'avalanche':
                _contract = avalanche_usdc_contract
                _spender = '0x45A01E4e04F14f7A4a6702c74187c5F6222033cd'
                _scan = rpc[5]['scan']
            case _:
                print('provided wrong chain for approve')
                raise ValueError

        _web3 = chain_api[chain]
        nonce = _web3.eth.get_transaction_count(address_wallet)

        contract_txn = _contract.functions.approve(
            Web3.to_checksum_address(_spender),
            115792089237316195423570985008687907853269984665640564039457584007913129639935
        ).build_transaction({
            'from': address_wallet,
            'gasPrice': int(_web3.eth.gas_price * 1.03),
            'nonce': nonce,
        })
        gas_limit = _web3.eth.estimate_gas(contract_txn)
        contract_txn.update({'gas': gas_limit})

        signed_txn = _web3.eth.account.sign_transaction(contract_txn, private_key=private_key)
        tx_hash = _web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(datetime.datetime.now(), f'Approved USDC in {chain} for Stargate {_scan}{_web3.to_hex(tx_hash)}')
        return True
    except Exception as error:
        account = web3.eth.account.from_key(private_key)
        print('Error: Stargate approve error', account.address, chain)
        print(error)
        # traceback.print_exc()
        return False


def bridge(private_key, chain, amount, to_chain):
    try:
        account = web3.eth.account.from_key(private_key)
        address_wallet = account.address
        match chain:
            case 'polygon':
                _contract = '0x45A01E4e04F14f7A4a6702c74187c5F6222033cd'
                _usdc_address = '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'
                _scan = rpc[3]['scan']
            case 'arbitrum':
                _contract = '0x53Bf833A5d6c4ddA888F69c22C88C9f356a41614'
                _usdc_address = '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8'
                _scan = rpc[4]['scan']
            case 'optimism':
                _contract = '0xB0D502E938ed5f4df2E681fE6E419ff29631d62b'
                _usdc_address = '0x7F5c764cBc14f9669B88837ca1490cCa17c31607'
                _scan = rpc[1]['scan']
            case 'fantom':
                _contract = '0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6'
                _usdc_address = '0x04068DA6C83AFCFA0e13ba15A6696662335D5B75'
                _scan = rpc[7]['scan']
            case 'avalanche':
                _contract = '0x45A01E4e04F14f7A4a6702c74187c5F6222033cd'
                _usdc_address = '0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E'
                _scan = rpc[5]['scan']
            case _:
                print('provided wrong chain for check balance')
                raise ValueError

        _web3 = chain_api[chain]
        _rate = chain_rate[chain]

        _refuel = 0
        if _to_balance := chain_api[to_chain].eth.get_balance(address_wallet) < 1e18 / chain_rate[to_chain]:  # if income network balance < $1
            _refuel = random.randint(10, 15) * 1e17 / chain_rate[to_chain] - _to_balance  # random between $1 and $1.50

        _contract_stg = _web3.eth.contract(address=Web3.to_checksum_address(_contract), abi=stargate_abi)

        fees = _contract_stg.functions.quoteLayerZeroFee(
            stargate_chains[to_chain],
            1,
            address_wallet,
            "0x",
            [0, int(_refuel), address_wallet]
        ).call()
        fee = fees[0]
        _local_refuel = _refuel * chain_rate[to_chain] / chain_rate[chain]  # refuel amount in current native coin

        if fee - _local_refuel > 1e18 / _rate:  # if fee - refuel > $1
            print('Error: High swap cost error', address_wallet, chain, '>', to_chain, '//', f'Amount: {amount} //, Fee: ${round((fee - _local_refuel) / 1e18 * _rate, 2)}')
            return False

        if (_balance := _web3.eth.get_balance(address_wallet)) < 0.5 * 1e18 / _rate + fee:  # if balance smaller than $0.5 + fee
            if _balance < 0.5 * 1e18 / _rate:  # in most chains it's enough for swap and approve
                print('Error: Not enough balance for L0 transfer (1)', address_wallet, chain, '>', to_chain,
                      f'// Amount: {amount / 1e6} USDC // Balance: ${round(_balance / 1e18 * _rate, 2)} // Fee: ${round(fee / 1e18 * _rate, 2)} // Refuel: ${round(_local_refuel / 1e18 * _rate, 2)}')
                return False, False  # wait time after this will be 0 seconds

            _swap_amount = random.randint(1_000_000 - int(_balance / 1e18 * _rate), 1_200_000 - int(_balance / 1e18 * _rate))  # amount of swap usdc to native coin
            if amount - _swap_amount < 1_000_000:
                amount = balance_checker(address_wallet, chain)
                if amount - _swap_amount < 1_000_000:
                    print('Error: Not enough balance for L0 transfer (2)', address_wallet, chain, '>', to_chain,
                          f'// Amount: {amount / 1e6} USDC // Balance: ${round(_balance / 1e18 * _rate, 2)} // Fee: ${round(fee / 1e18 * _rate, 2)} // Refuel: ${round(_local_refuel / 1e18 * _rate, 2)}')
                    return False, False

            _swapped = hm_swap.inch_swap(private_key, _swap_amount, _usdc_address,
                                         '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE', chain)
            if _swapped:
                time.sleep(40)
                amount -= _swap_amount
            else:
                return False

        if not check_approve(address_wallet, chain):  # if token not approve for stargate
            _approved = approve(private_key, chain)
            if not _approved:
                return False
            for i in range(6):
                if check_approve(address_wallet, chain):
                    break
                else:
                    time.sleep(10)
                    if i >= 5 and not check_approve(address_wallet, chain):
                        print('Error: Approve going too long', address_wallet, chain)
                        return False
        time.sleep(10)
        nonce = _web3.eth.get_transaction_count(address_wallet)
        contract_txn = _contract_stg.functions.swap(
            stargate_chains[to_chain],
            1,
            1,
            Web3.to_checksum_address(address_wallet),
            amount,
            int(amount * 0.995),
            [0, int(_refuel), Web3.to_checksum_address(address_wallet)],
            Web3.to_checksum_address(address_wallet),
            '0x'
        ).build_transaction({
            'from': address_wallet,
            'value': fee,
            'gasPrice': int(_web3.eth.gas_price * 1.03),
            'nonce': nonce,
        })
        gas_limit = _web3.eth.estimate_gas(contract_txn)
        contract_txn.update({'gas': gas_limit})
        _total_fee = (fee - _local_refuel) + gas_limit * _web3.eth.gas_price  # fee in wei

        signed_txn = _web3.eth.account.sign_transaction(contract_txn, private_key=private_key)
        tx_hash = _web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        print(datetime.datetime.now(), f'Stargate transfer from {chain} to {to_chain} // Amount: {round(amount / 1e6, 2)} '
                                       f'// Fee: {round(_total_fee / 1e18, 6)} '
                                       f'(${round(_total_fee / 1e18 * _rate, 2)}) // Refuel: ${round(_local_refuel / 1e18 * _rate, 2)}'
                                       f'\n{_scan}{_web3.to_hex(tx_hash)}')
        return True
    except Exception as error:
        account = web3.eth.account.from_key(private_key)
        print('Error bridge', account.address, chain, to_chain, amount / 1e6)
        print(error)
        # traceback.print_exc()
        return False
