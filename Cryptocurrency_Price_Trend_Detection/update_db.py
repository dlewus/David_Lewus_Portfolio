'''
Functions to update cryptocurrency price SQL database
'''

import sqlite3
import config
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit
import pandas as pd
from datetime import datetime, timedelta, timezone


def update(coin, timeframe, messages=True):
    '''
    Updates price data on SQL table
    coin - string of coin table name
    timeframe - string of timeframe table name
    '''

    # Set timeframe
    if timeframe not in [
            '1m', '5m', '15m', '1h', '4h', '6h', '12h', '1D', '1W']:
        print('Timeframe not supported, must be: 1m, 1h, 4h, 6h, 12h, 1D, 5D, 1W, 1M')
        return -1
    elif timeframe == '1m':
        APItimeframe = TimeFrame.Minute
    elif timeframe == '5m':
        APItimeframe = TimeFrame(5, TimeFrameUnit.Minute)
    elif timeframe == '15m':
        APItimeframe = TimeFrame(15, TimeFrameUnit.Minute)
    elif timeframe == '1h':
        APItimeframe = TimeFrame.Hour
    elif timeframe == '4h':
        APItimeframe = TimeFrame(4, TimeFrameUnit.Hour)
    elif timeframe == '6h':
        APItimeframe = TimeFrame(6, TimeFrameUnit.Hour)
    elif timeframe == '12h':
        APItimeframe = TimeFrame(12, TimeFrameUnit.Hour)
    elif timeframe == '1D':
        APItimeframe = TimeFrame.Day
    elif timeframe == '1W':
        APItimeframe = TimeFrame.Week

    # Set up database connection
    connection = sqlite3.connect(config.DB_FILE)

    cursor = connection.cursor()

    # Set up Alpaca API
    api = REST(
        key_id=config.KEY_ID,
        secret_key=config.SECRET_KEY,
        base_url=config.BASE_URL,
        api_version='v2')

    # Find last point timestamp in database
    cursor.execute(f"""
        SELECT timestamp
        FROM {coin}_price_{timeframe}
        ORDER BY ID DESC
        """)

    latest = cursor.fetchall()

    # Set up a blank database
    bars = pd.DataFrame()

    # Sets start to beginning of Coinbase if database is empty
    if len(latest) == 0:
        if coin == 'BTCUSD':
            start = '2015-01-07T00:00:00-00:00'  # this is where Coinbase data starts
        if coin == 'ETHUSD':
            start = '2016-05-25T00:00:00-00:00'
        else:
            print('find date where coin data starts')
            return

    # Else, sets start to last timestamp in database
    else:
        start = latest[0][0].replace(' ', 'T')
        start = start.replace('+', '-')

    # Find current time to the minute, put in format for Alpaca API
    now = f'{datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:00")}-00:00'

    # Find number of days between last timestamp and current day
    date_format = "%Y-%m-%dT%H:%M:00-00:00"
    start_day = datetime.strptime(start, date_format)
    now_day = datetime.strptime(now, date_format)
    delta = now_day - start_day

    # Allows you to update on the same day
    if delta.days < 1:
        delta += timedelta(days=2)

    # Split into batches, to not overload API
    batch_size = 30

    for i in range(0, delta.days, batch_size):
        end_day = start_day + timedelta(days=batch_size)
        if start_day > now_day:
            start_day = now_day

        start = f'{start_day.strftime("%Y-%m-%dT%H:%M:00")}-00:00'
        end = f'{end_day.strftime("%Y-%m-%dT%H:%M:00")}-00:00'

        if messages:
            print(start)  # Watch it work

        # Collect data, trim to only Coinbase, and convert timezone
        bars_batch = api.get_crypto_bars(coin, APItimeframe, start, end).df
        bars_batch = bars_batch[bars_batch.exchange == 'CBSE']

        # Add to bars df
        if bars.empty:
            bars = bars_batch
        else:
            bars = pd.concat([bars, bars_batch])

        start_day = end_day

    # Remove unnecessary columns
    bars.drop(columns=['exchange', 'vwap', 'trade_count'], inplace=True)

    bars = bars.iloc[:-1].copy()  # don't include last timestep which hasn't closed yet

    # Find coin_id and add to bars df
    cursor.execute(f"""
        SELECT id
        FROM coin_pair
        WHERE pair_symbol = '{coin}'
        """)
    id = cursor.fetchall()

    bars['coin_id'] = [id[0][0] for i in range(len(bars))]
    if messages:
        print(bars.close)

    # Send collected data to SQL database
    if messages:
        print('writing...')
    bars.to_sql(f'{coin}_price_{timeframe}', con=connection, if_exists='append')
    if messages:
        print('done writing!')
    connection.commit()


def clean(coin, timeframe, messages=False):

    # Set up database connection
    connection = sqlite3.connect(config.DB_FILE)

    cursor = connection.cursor()

    # Remove entries with duplicate timestamps
    if messages:
        print('cleaning...')
    cursor.execute(f'''
        DELETE
        FROM {coin}_price_{timeframe}
        WHERE ID NOT IN
        (
            SELECT MAX(ID)
            FROM {coin}_price_{timeframe}
            GROUP BY timestamp
        )
        ''')
    if messages:
        print('done cleaning!')
    connection.commit()
