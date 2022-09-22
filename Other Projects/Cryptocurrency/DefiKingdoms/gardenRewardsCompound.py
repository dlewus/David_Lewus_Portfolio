
from web3 import Web3, exceptions
import json
from math import floor
from time import sleep
import datetime
import sys


# Load JSONs
f = open('abi.json')
abi = json.load(f)
f.close()

f = open('config.json')
config = json.load(f)
f.close()

# Setup RPC
RPC = "https://harmony-0-rpc.gateway.pokt.network"
provider = Web3(Web3.HTTPProvider(RPC))

# Wallet info from config
private_key = config['wallet']['privateKey']
wallet_address = config['wallet']['address']

# Contracts
WBTC = Web3.toChecksumAddress(config['WBTC'])
LP = Web3.toChecksumAddress(config['JEWEL_WBTC_LP'])
JEWELContract = provider.eth.contract(address=config['JEWEL'], abi=abi)
LPContract = provider.eth.contract(address=LP, abi=abi)
WBTCContract = provider.eth.contract(address=WBTC, abi=abi)
UniswapRouter = provider.eth.contract(address=config["UniswapRouter"], abi=abi)
MasterGardener = provider.eth.contract(address=config["MasterGardener"], abi=abi)

# Claim rewards
def claimRewards():

    try:
        # set up transaction to claim gardening rewards
        nonce = provider.eth.getTransactionCount(wallet_address)
        # 7 is the pid for the JEWEL-1WBTC pool, this would need to be changed if you farm something else
        tx = MasterGardener.functions.claimReward(7).buildTransaction({
            'gas': 2000000,
            'gasPrice': provider.toWei('35', 'gwei'),
            'from': wallet_address,
            'nonce': nonce
        })
        signed_tx = provider.eth.account.sign_transaction(tx, private_key=private_key)
        receipt = provider.eth.send_raw_transaction(signed_tx.rawTransaction)
        output_str = f'Submitted Claim Rewards with tx hash {receipt.hex()}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()

    except ValueError:
        time.sleep(10)

    # Wait for receipt
    waiting = True
    while waiting:
        try:
            wait = provider.eth.get_transaction_receipt(receipt.hex())
            waiting = False
            output_str = f'Claim Rewards successful with tx hash {receipt.hex()}\n'
            sys.stdout.write(output_str)
            sys.stdout.flush()
        except exceptions.TransactionNotFound:
            sleep(5)
    # Wait for receipt

# Trade half of balance to 1WBTC (swap exact tokens)
def tradeJEWELtoWBTC():

    # Get JEWEL balance
    JEWELBalance = JEWELContract.functions.balanceOf(wallet_address).call()
    halfJEWELBalance = floor(JEWELBalance * 0.5)

    # Check price of 1WBTC per JEWEL
    WBTCOut = UniswapRouter.functions.getAmountsOut(halfJEWELBalance, [config['JEWEL'], WBTC]).call()
    WBTCOutMin = floor(WBTCOut[1] * 0.995)  # 0.5% slippage

    # Swap tokens
    try:
        # set up transaction to trade half of JEWEL to 1WBTC
        nonce = provider.eth.getTransactionCount(wallet_address)
        deadline = floor(datetime.datetime.timestamp(datetime.datetime.now())) + (20 * 60)
        tx = UniswapRouter.functions.swapExactTokensForTokens(halfJEWELBalance, WBTCOutMin, [config['JEWEL'], WBTC], wallet_address, deadline).buildTransaction({
            'gas': 2000000,
            'gasPrice': provider.toWei('35', 'gwei'),
            'from': wallet_address,
            'nonce': nonce
        })
        signed_tx = provider.eth.account.sign_transaction(tx, private_key=private_key)
        receipt = provider.eth.send_raw_transaction(signed_tx.rawTransaction)
        output_str = f'Submitted Swap JEWEL for 1WBTC with tx hash {receipt.hex()}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()

    except ValueError:
        time.sleep(10)

    # Wait for receipt
    waiting = True
    while waiting:
        try:
            wait = provider.eth.get_transaction_receipt(receipt.hex())
            waiting = False
            output_str = f'Swap JEWEL for 1WBTC successful with tx hash {receipt.hex()}\n'
            sys.stdout.write(output_str)
            sys.stdout.flush()
        except exceptions.TransactionNotFound:
            sleep(5)

# Pair JEWEL-1WBTC (add liquidity)
def addLiquidity():

    # Get JEWEL and 1WBTC balance
    WBTCBalance = WBTCContract.functions.balanceOf(wallet_address).call()
    JEWELBalance = JEWELContract.functions.balanceOf(wallet_address).call()

    # Check price of JEWEL per 1WBTC
    JEWELOut = UniswapRouter.functions.getAmountsOut(WBTCBalance, [WBTC, config['JEWEL']]).call()
    JEWELOut = JEWELOut[1]

    # Make sure you have enough JEWEL to pair with 1WBTC
    if JEWELOut > JEWELBalance:
        WBTCOut = UniswapRouter.functions.getAmountsOut(JEWELBalance, [config['JEWEL'], WBTC]).call()
        WBTCBalance = WBTCOut[1]
        JEWELOut = JEWELBalance

    # Set 0.5% slippage
    WBTCOutMin = floor(WBTCBalance*0.995)
    JEWELOutMin = floor(JEWELOut*0.995)

    # Add liquidity
    try:
        # set up transaction to add liquidity for JEWEL and 1WBTC
        nonce = provider.eth.getTransactionCount(wallet_address)
        deadline = floor(datetime.datetime.timestamp(datetime.datetime.now())) + (20 * 60)
        tx = UniswapRouter.functions.addLiquidity(config['JEWEL'], WBTC, JEWELOut, WBTCBalance, JEWELOutMin, WBTCOutMin, wallet_address, deadline).buildTransaction({
            'gas': 2000000,
            'gasPrice': provider.toWei('35', 'gwei'),
            'from': wallet_address,
            'nonce': nonce
        })
        signed_tx = provider.eth.account.sign_transaction(tx, private_key=private_key)
        receipt = provider.eth.send_raw_transaction(signed_tx.rawTransaction)
        output_str = f'Submitted Add Liquidity JEWEL-1WBTC with tx hash {receipt.hex()}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()

    except ValueError:
        time.sleep(10)

    # Wait for receipt
    waiting = True
    while waiting:
        try:
            wait = provider.eth.get_transaction_receipt(receipt.hex())
            waiting = False
            output_str = f'Add Liquidity JEWEL-1WBTC successful with tx hash {receipt.hex()}\n'
            sys.stdout.write(output_str)
            sys.stdout.flush()
        except exceptions.TransactionNotFound:
            sleep(5)

# Deposit JEWEL-1WBTC
def deposit():

    # Get balance of LP token
    LPBalance = LPContract.functions.balanceOf(wallet_address).call()

    # Deposit
    try:
        # set up transaction to deposit JEWEL-1WBTC LP
        nonce = provider.eth.getTransactionCount(wallet_address)
        # 7 is the pid for the JEWEL-1WBTC pool, this would need to be changed if you farm something else
        tx = MasterGardener.functions.deposit(7,LPBalance,config['_ref']).buildTransaction({
            'gas': 2000000,
            'gasPrice': provider.toWei('35', 'gwei'),
            'from': wallet_address,
            'nonce': nonce
        })
        signed_tx = provider.eth.account.sign_transaction(tx, private_key=private_key)
        receipt = provider.eth.send_raw_transaction(signed_tx.rawTransaction)
        output_str = f'Submitted Deposit JEWEL-1WBTC LP with tx hash {receipt.hex()}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()

    except ValueError:
        time.sleep(10)

    # Wait for receipt
    waiting = True
    while waiting:
        try:
            wait = provider.eth.get_transaction_receipt(receipt.hex())
            waiting = False
            output_str = f'Deposit JEWEL-1WBTC LP successful with tx hash {receipt.hex()}\n'
            sys.stdout.write(output_str)
            sys.stdout.flush()
        except exceptions.TransactionNotFound:
            sleep(5)
            sys.stdout.write('.\n')
            sys.stdout.flush()

# Run function at specific times
    # Run every night at 9:30PM


def main():
    claimRewards()
    tradeJEWELtoWBTC()
    addLiquidity()
    deposit()

if __name__ == "__main__":
    main()
