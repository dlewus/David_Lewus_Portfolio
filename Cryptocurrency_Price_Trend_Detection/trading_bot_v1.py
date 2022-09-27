'''
Program to create price signals and place orders on GMX exchange
'''

# Imports
from web3 import Web3
import json
import orderbook as ob
import update_db as udb
from time import sleep
from datetime import datetime
from pytz import timezone
from tensorflow import keras
import joblib
import sys
import requests


# Load JSONs
f = open('GMXabi.json')  # GMX contract calls
abi = json.load(f)
f.close()

f = open('config_AVAX.json')  # contains config info
config = json.load(f)
f.close()

f = open('tokenABI.json')  # token contract calls
token_abi = json.load(f)
f.close()

f = open('JoeRouter02ABI.json')  # Trader Joe contract calls
JoeRouterABI = json.load(f)
f.close()

# Setup RPC
RPC = 'https://api.avax.network/ext/bc/C/rpc'
provider = Web3(Web3.HTTPProvider(RPC))

# Wallet info from config
wallet_address = config['wallet']['address']
private_key = config['wallet']['privateKey']

# Contracts
ReaderContract = provider.eth.contract(address=config['ReaderContract'], abi=abi)
Router = provider.eth.contract(address=config['Router'], abi=abi)
PositionRouter = provider.eth.contract(address=config['PositionRouter'], abi=abi)
JoeRouter = provider.eth.contract(address=config['JoeRouter'], abi=JoeRouterABI)
USDCContract = provider.eth.contract(address=config['USDC_address'], abi=token_abi)
ETHContract = provider.eth.contract(address=config['ETH_address'], abi=token_abi)

# Contract addresses
vault = config['VaultContract']
ETH_address = config['ETH_address']
USDC_address = config['USDC_address']
WAVAX_address = config['AVAX_address']

# Telegram bot variables
TELEGRAM_BOT_TOKEN = 'Your Telegram Bot Token'
chat_id = "Your Telegram Chat ID"
base_url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN

# Other Variables
current = None
first = True
coin = 'ETHUSD'
timeframe = '1h'
last = None
tp_price = None
sl_price = None
leverage = 10

# Load Model
path = 'Path to Keras model'
model = keras.models.load_model(path)

# Load scaler
scaler_path = 'Path to scikit-learn scaler'
scaler = joblib.load(scaler_path)

# Infinite loop
while True:

    # update database and check for signal every hour
    now = datetime.now(timezone('UTC'))

    if (now.minute >= 1 and now.second >= 5 and now.hour != current) or first:

        # Reset current hour
        current = now.hour

        # Update database
        udb.update(coin, timeframe, messages=False)
        udb.clean(coin, timeframe, messages=False)

        # Check signal
        signal_dict = ob.checkSignal(
            scaler=scaler,
            model=model,
            last=last,
            tp_price=tp_price,
            sl_price=sl_price)

        # Set variables from signal check
        last = signal_dict['last']
        signal = signal_dict['signal']
        tp_price = signal_dict['tp_price']
        sl_price = signal_dict['sl_price']
        message = signal_dict['message']

        # Do nothing on start up
        if first:
            signal = 1
            first = False

        # Output message
        sys.stdout.write(message)
        sys.stdout.flush()

        # Send output message to Telegram
        parameters = {
            "chat_id": chat_id,
            "text": message,
        }
        resp = requests.get(base_url + "/sendMessage", data=parameters)

        # Check for current positions if signal to buy was given, both long and shorts separately
        if signal != 1:

            _, short_bool = ob.checkPositions(
                vault,
                wallet_address,
                [USDC_address],
                [ETH_address],
                [False],
                ReaderContract
            )

            _, long_bool = ob.checkPositions(
                vault,
                wallet_address,
                [ETH_address],
                [ETH_address],
                [True],
                ReaderContract
            )

            # if in position or signal 3, close position
            if short_bool or long_bool or signal == 3:
                message = ob.placeCloseOrder(
                    provider=provider,
                    Router=Router,
                    ReaderContract=ReaderContract,
                    vault=vault,
                    wallet_address=wallet_address,
                    private_key=private_key,
                    ETH_address=ETH_address,
                    USDC_address=USDC_address
                )

                # Send output message to Telegram
                parameters = {
                    "chat_id": chat_id,
                    "text": message,
                }
                resp = requests.get(base_url + "/sendMessage", data=parameters)

                # If ETH was given as part of placeCloseOrder, swap to USDC (can't keep WETH.e in wallet)
                ETHBalance = ETHContract.functions.balanceOf(wallet_address).call()

                if ETHBalance > 0:
                    message = ob.swap(
                        ETHContract=ETHContract,
                        JoeRouter=JoeRouter,
                        wallet_address=wallet_address,
                        ETH_address=ETH_address,
                        WAVAX_address=WAVAX_address,
                        USDC_address=USDC_address,
                        provider=provider,
                        private_key=private_key
                    )

                    # Send output message to Telegram
                    parameters = {
                        "chat_id": chat_id,
                        "text": message,
                    }
                    resp = requests.get(base_url + "/sendMessage", data=parameters)

            # place order if buy or sell signal given

                # puts entire USDC balance into order (can test by swapping to USDC.e)
            amountIn = USDCContract.functions.balanceOf(wallet_address).call()

            # short order
            if signal == 0:
                message = ob.placeOpenOrder(
                    amountIn=amountIn,
                    leverage=leverage,
                    isLong=False,
                    USDC_address=USDC_address,
                    ETH_address=ETH_address,
                    PositionRouter=PositionRouter,
                    provider=provider,
                    wallet_address=wallet_address,
                    private_key=private_key
                )

                # Send output message to Telegram
                parameters = {
                    "chat_id": chat_id,
                    "text": message,
                }
                resp = requests.get(base_url + "/sendMessage", data=parameters)

            # long order
            elif signal == 2:
                message = ob.placeOpenOrder(
                    amountIn=amountIn,
                    leverage=leverage,
                    isLong=True,
                    USDC_address=USDC_address,
                    ETH_address=ETH_address,
                    PositionRouter=PositionRouter,
                    provider=provider,
                    wallet_address=wallet_address,
                    private_key=private_key
                )

                # Send output message to Telegram
                parameters = {
                    "chat_id": chat_id,
                    "text": message,
                }
                resp = requests.get(base_url + "/sendMessage", data=parameters)

    # check for positions (outside of signal check 'if' statement)
    _, short_bool = ob.checkPositions(
        vault,
        wallet_address,
        [USDC_address],
        [ETH_address],
        [False],
        ReaderContract
    )

    _, long_bool = ob.checkPositions(
        vault,
        wallet_address,
        [ETH_address],
        [ETH_address],
        [True],
        ReaderContract
    )

    # if in position, routinely check price for take profit level
    if short_bool or long_bool:
        price = ob.checkPrice()
        # if take profit level reached, place close order
        if tp_price is not None:

            if (short_bool and price <= tp_price) or (long_bool and price >= tp_price):
                message = ob.placeCloseOrder(
                    provider=provider,
                    Router=Router,
                    ReaderContract=ReaderContract,
                    vault=vault,
                    wallet_address=wallet_address,
                    private_key=private_key,
                    ETH_address=ETH_address,
                    USDC_address=USDC_address
                )

                # Send output message to Telegram
                parameters = {
                    "chat_id": chat_id,
                    "text": message,
                }
                resp = requests.get(base_url + "/sendMessage", data=parameters)

                # If ETH was given as part of placeCloseOrder, swap to USDC (can't keep WETH.e in wallet)
                ETHBalance = ETHContract.functions.balanceOf(wallet_address).call()

                if ETHBalance > 0:
                    message = ob.swap(
                        ETHContract=ETHContract,
                        JoeRouter=JoeRouter,
                        wallet_address=wallet_address,
                        ETH_address=ETH_address,
                        WAVAX_address=WAVAX_address,
                        USDC_address=USDC_address,
                        provider=provider,
                        private_key=private_key
                    )

                    # Send output message to Telegram
                    parameters = {
                        "chat_id": chat_id,
                        "text": message,
                    }
                    resp = requests.get(base_url + "/sendMessage", data=parameters)

        # sleep 5 seconds to space out API and contract calls
        sleep(5)
