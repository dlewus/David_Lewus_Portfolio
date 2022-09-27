'''
Functions to place orders and check trading signals
'''


import load_data as ld
import indicators as ind
import numpy as np
from datetime import datetime, timedelta
from pytz import timezone
import requests
from math import floor
import sys
from web3 import exceptions
from time import sleep

# check positions


def checkPositions(
        _vault,
        _account,
        _collateralTokens,
        _indexTokens,
        _isLong,
        readerContract):
    '''
    returnBool  True if there is an open position
                False if there is no open position

    return list with the following values at index:
    0 - position size in USD * 1e30
    1 - collateral size in USD * 1e30
    2 - average entry price in USD * 1e30
    3 - funding rate
    4 - realized profit bool
    5 - realized PnL bool
    6 - timestamp of last time position was increased
    7 - bool, 1 in profit 0 otherwise
    8 - amount of profit or loss in USD * 1e30

    _vault - string of Vault contract address
    _account - string of wallet address
    _collateralTokens - list of strings of collateral tokens addresses
        typically ETH address for longs and USDC address for shorts
        typically only want one address in the list
    _indexTokens - list of strings of index tokens addresses
        token being traded, typically only want ETH address in the list
    _isLong - list of bool of if trade is long or not
        typically only want one bool in list
        [True] for long, [False] for short
    readerContract - web3 contract object for Reader contract
    '''

    result = readerContract.functions.getPositions(
        _vault,
        _account,
        _collateralTokens,
        _indexTokens,
        _isLong).call()

    if result[0] > 0:
        returnBool = True

    elif result[0] == 0:
        returnBool = False

    return result, returnBool


def placeCloseOrder(
        provider,
        Router,
        ReaderContract,
        vault,
        wallet_address,
        private_key,
        ETH_address,
        USDC_address,
):
    '''
    places close order for entire WETH.e position
    prioritizes long positions

    provider - web3 RPC connection object
    Router - web3 contract object for Router contract
    ReaderContract - web3 contract object for ReaderContract
    vault - web3 contract object for vault contract
    wallet_address - str of wallet address
    private_key - str of wallet key
    ETH_address - str of WETH.e contract address
    USDC_address - str of USDC contract address
    '''
    # call checkPositions to figure out what position is open

    # check long
    long_position, long_bool = checkPositions(
        vault,
        wallet_address,
        [ETH_address],
        [ETH_address],
        [True],
        ReaderContract
    )

    # check short
    short_position, short_bool = checkPositions(
        vault,
        wallet_address,
        [USDC_address],
        [ETH_address],
        [False],
        ReaderContract
    )

    price = checkPrice(rounded=False)

    if long_bool:
        position = long_position
        collateralToken = ETH_address
        isLong = True
        price = floor(price * 0.995)  # 0.5% slippage

    elif short_bool:
        position = short_position
        collateralToken = USDC_address
        isLong = False
        price = floor(price * 1.005)  # 0.5% slippage

    else:
        return

    # collateralDelta = position[1]
    collateralDelta = 0
    sizeDelta = position[0]

    try:
        nonce = provider.eth.getTransactionCount(wallet_address)
        tx = Router.functions.decreasePosition(
            collateralToken,
            ETH_address,
            collateralDelta,
            sizeDelta,
            isLong,
            wallet_address,
            price
        ).buildTransaction(
            {
                'gas': 500000,
                'gasPrice': provider.toWei('50', 'gwei'),
                'from': wallet_address,
                'nonce': nonce
            }
        )

        signed_tx = provider.eth.account.sign_transaction(tx, private_key=private_key)
        receipt = provider.eth.send_raw_transaction(signed_tx.rawTransaction)
        output_str = f'Submitted Decrease Position with tx hash {receipt.hex()}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()

    except ValueError:
        sleep(10)

    # Wait for receipt
    waiting = True
    while waiting:
        try:
            wait = provider.eth.get_transaction_receipt(receipt.hex())
            waiting = False
            output_str = f'Decrease Position successful with tx hash {receipt.hex()}\n'
            sys.stdout.write(output_str)
            sys.stdout.flush()
        except exceptions.TransactionNotFound:
            sleep(5)

    return output_str


def placeOpenOrder(
    amountIn,
    leverage,
    isLong,
    USDC_address,
    ETH_address,
    PositionRouter,
    provider,
    wallet_address,
    private_key,
    minOut=0,
    executionFee=20000000000000000,
    referralCode=''.encode('utf-8')
):
    '''
    places open order to either short or long WETH.e

    amountIn - int of amount to place in order
    leverage - float of leverage value
    isLong - bool, True if long, False if short
    USDC_address - str of USDC contract address
    ETH_address - str of WETH.e contract address
    PositionRouter - web3 contract object for PositionRouter contract
    provider - web3 RPC connection object
    wallet_address - str of wallet address
    private_key - str of wallet key
    minOut - int of minimum value excepted on swap, can be 0
    executionFee - int of fee required for trade
    referralCode - byte string of referral code
    '''
    price = checkPrice(rounded=False)

    if isLong:
        path = [USDC_address, ETH_address]
        price = floor(price * 1.005)  # 0.5% slippage

    elif not isLong:
        path = [USDC_address]
        price = floor(price * 0.995)  # 0.5% slippage

    sizeDelta = floor(((amountIn / 1e6) * 1e30 * leverage) * 0.999)

    try:
        nonce = provider.eth.getTransactionCount(wallet_address)
        tx = PositionRouter.functions.createIncreasePosition(
            path,
            ETH_address,
            amountIn,
            minOut,
            sizeDelta,
            isLong,
            price,
            executionFee,
            referralCode
        ).buildTransaction(
            {
                'value': executionFee,
                'gas': 500000,
                'gasPrice': provider.toWei('50', 'gwei'),
                'from': wallet_address,
                'nonce': nonce
            }
        )

        signed_tx = provider.eth.account.sign_transaction(tx, private_key=private_key)
        receipt = provider.eth.send_raw_transaction(signed_tx.rawTransaction)
        output_str = f'Submitted Increase Position with tx hash {receipt.hex()}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()

    except ValueError:
        sleep(10)

    # Wait for receipt
    waiting = True
    while waiting:
        try:
            wait = provider.eth.get_transaction_receipt(receipt.hex())
            waiting = False
            output_str = f'Increase Position successful with tx hash {receipt.hex()}\n'
            sys.stdout.write(output_str)
            sys.stdout.flush()
        except exceptions.TransactionNotFound:
            sleep(5)

    return output_str


def checkPrice(
        api_path='https://gmx-avax-server.uc.r.appspot.com/prices',
        coin_address='0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB',
        rounded=True):
    '''
    returns float of price at coin_address, rounded to 2 decimals
    or int of price at coin_address, USD * 1e30

    api_path - str of api website path
    coin_address - str of coin's smart contract address
    rounded - bool, True if price should be converted from displayed format to USD
    '''

    response = requests.get(api_path)
    prices = response.json()
    coin_price = int(prices[coin_address])

    if rounded:
        coin_price /= (1e30)
        coin_price = round(coin_price, 2)

    return coin_price


# swap from ETH to USDC
def swap(
    ETHContract,
    JoeRouter,
    wallet_address,
    ETH_address,
    WAVAX_address,
    USDC_address,
    provider,
    private_key
):
    '''
    swaps total WETH.e balance to USDC

    JoeRouter - web3 contract object for JoeRouter contract
    wallet_address - str of wallet address
    ETH_address - str of WETH.e contract address
    WAVAX_address - str of WAVAX contract address
    USDC_address - str of USDC contract address
    provider - web3 RPC connection object
    private_key - str of wallet key
    '''
    amountIn = ETHContract.functions.balanceOf(wallet_address).call()
    amountOutMin = JoeRouter.functions.getAmountsOut(
        amountIn,
        [ETH_address, WAVAX_address, USDC_address]
    ).call()

    amountOutMin = amountOutMin[2]
    try:
        nonce = provider.eth.getTransactionCount(wallet_address)
        deadline = floor(datetime.timestamp(datetime.now())) + (20 * 60)
        tx = JoeRouter.functions.swapExactTokensForTokens(
            amountIn,
            amountOutMin,
            [ETH_address, WAVAX_address, USDC_address],
            wallet_address,
            deadline
        ).buildTransaction(
            {
                'gas': 500000,
                'gasPrice': provider.toWei('50', 'gwei'),
                'from': wallet_address,
                'nonce': nonce
            }
        )

        signed_tx = provider.eth.account.sign_transaction(tx, private_key=private_key)
        receipt = provider.eth.send_raw_transaction(signed_tx.rawTransaction)
        output_str = f'Submitted ETH to USDC swap with tx hash {receipt.hex()}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()

    except ValueError:
        sleep(10)

    # Wait for receipt
    waiting = True
    while waiting:
        try:
            wait = provider.eth.get_transaction_receipt(receipt.hex())
            waiting = False
            output_str = f'ETH to USDC swap successful with tx hash {receipt.hex()}\n'
            sys.stdout.write(output_str)
            sys.stdout.flush()
        except exceptions.TransactionNotFound:
            sleep(5)

    return output_str


def checkSignal(
    scaler,
    model,
    coin='ETHUSD',
    timestamp='2022-01-01 00:00:00+00:00',
    timeframe='1h',
    SMA_range=[10, 20, 50],
    EMA_range=[8, 21, 55],
    ZLMA_range=[8, 21, 55],
    N=5,
    date_format="%m/%d/%Y %H:%M",
    tz=timezone('America/New_York'),
    buy_target=2,
    hold_target=1,
    sell_target=0,
    last=None,
    tp_price=None,
    sl_price=None,
    sl=0.8,
    tp=0.2,
    leverage=10
):
    '''
    NOTE: This is a simplified version of signal checking algorithm.
          Complexity is omitted for intellectual property protection.

    returns dictionary containing
        last - int of last prediction given, needed as input for future function calls
        signal - int of signal to place orders (0 - sell, 1 - none, 2 - buy, 3 - close hold)
        tp_price - float of take profit price, 2 decimals
        sl_price - float of stop loss price, 2 decimals
        message - string message for telegram

    scaler - sklearn scaler object
    model - tensorflow keras model object
    last - int of last prediction given
    coin, timeframe, timestampe - reference load_data.py
    SMA_range, EMA_range, ZLMA_range - reference indicators.py
    N - int of sequence lookback
    buy/hold/sell_target - int of model targets
    tp_price/sl_price - float of take profit/stop loss, needed for proper message generation
    sl - float of stop loss percent
    tp - float of take profit percent
    leverage - int of leverage multiplier
    '''

    # Load from database
    bars = ld.load_df_from_date(coin, timeframe, timestamp, messages=False)

    # Add indicators
    bars = ind.add_features(
        bars,
        SMA_range=SMA_range,
        EMA_range=EMA_range,
        ZLMA_range=ZLMA_range,
        ma=True,
        below=True,
        price_cross=True,
        supertrend=True,
        percent_diff=True
    )

    # Remove excess columns
    bars = bars.dropna()

    to_delete = ['id', 'coin_id',
                 'high', 'low', 'open',
                 'close', 'volume',
                 ]

    data = bars.drop(to_delete, axis=1)
    data = data.dropna()

    # Preprocessing
    X = data.copy()
    X = X.to_numpy()
    X_sequences = []

    # Make sequences
    for i in range(N, len(X)):

        to_append = X[i - N:i]

        X_sequences.append(to_append)

    X = np.asarray(X_sequences).astype('float32')

    X = scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)

    # Predictions
    pred = model.predict(X, verbose=0)
    pred_list = []
    for i, value in enumerate(pred):
        pred_list.append(np.argmax(value))
    pred = pred_list

    # Current prediction and time
    curr_pred = pred[-1]
    curr_time = data.index[-1] + timedelta(hours=1)
    curr_time = curr_time.astimezone(tz).strftime(date_format)

    # Check if current prediciton is the same as last
    if curr_pred != last:

        last = curr_pred

        # Send appropriate signal and message
        if curr_pred == sell_target:
            sl_price = round(((1 + (sl / leverage)) * bars.close.iloc[-1]), 2)
            tp_price = round(((1 - (tp / leverage)) * bars.close.iloc[-1]), 2)
            message = f'''
SELL @ {curr_time}
CLOSE: {bars.close.iloc[-1]}
TAKE PROFIT: {tp_price}
STOP LOSS: {sl_price}
            '''
            signal = 0

        elif curr_pred == buy_target:
            sl_price = round(((1 - (sl / leverage)) * bars.close.iloc[-1]), 2)
            tp_price = round(((1 + (tp / leverage)) * bars.close.iloc[-1]), 2)
            message = f'''
BUY @ {curr_time}
CLOSE: {bars.close.iloc[-1]}
TAKE PROFIT: {tp_price}
STOP LOSS: {sl_price}
            '''
            signal = 2

        elif curr_pred == hold_target:
            sl_price = None
            tp_price = None
            message = f'''
CLOSE POSITION @ {curr_time}
CLOSE: {bars.close.iloc[-1]}
TAKE PROFIT: {tp_price}
STOP LOSS: {sl_price}
            '''
            signal = 3

    # if curr_pred == last you just hold
    elif curr_pred == last:
        message = f'''
HOLD @ {curr_time}
CLOSE: {bars.close.iloc[-1]}
TAKE PROFIT: {tp_price}
STOP LOSS: {sl_price}
            '''
        signal = 1

    return_dict = {
        'last': last,
        'signal': signal,
        'tp_price': tp_price,
        'sl_price': sl_price,
        'message': message
    }

    return return_dict
