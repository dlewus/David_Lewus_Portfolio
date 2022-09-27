'''
Functions to create cryptocurrency price SQL database
'''


import sqlite3
import config


def create_db():
    '''
    Creates new database file, based off filename in config.py
    '''

    # Set up connection to SQL database
    connection = sqlite3.connect(config.DB_FILE)

    cursor = connection.cursor()

    # Create table that holds coin names and symbols
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coin_pair (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair_symbol TEXT NOT NULL UNIQUE
        )
    """)

    connection.commit()


def populate_db(coins, timeframes):
    '''
    Creates table for each coin in coins and timeframe in timeframes
    coins - list of strings of cryptocurrencies to pass to Alpaca API
    timeframes - list of strings of timeframes to pass to Alpaca API
    '''

    # Set up connection to SQL database
    connection = sqlite3.connect(config.DB_FILE)

    cursor = connection.cursor()

    if not isinstance(coins, list):
        print('List not passed to populate_db()')
        return
    # Loop through list of coins and add to table
    for coin in coins:

        cursor.execute("""
            INSERT INTO coin_pair(pair_symbol)
            SELECT (?)
            WHERE NOT EXISTS
            (SELECT pair_symbol
            FROM coin_pair
            WHERE pair_symbol = (?))
        """, (coin, coin))

        for timeframe in timeframes:
            # Create table to hold coin prices, which will get regularly updated
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {coin}_price_{timeframe} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coin_id INTEGER,
                    timestamp NOT NULL,
                    open NOT NULL,
                    high NOT NULL,
                    low NOT NULL,
                    close NOT NULL,
                    volume NOT NULL,
                    FOREIGN KEY (coin_id) REFERENCES coin_pair (id)
            )
            """)

    connection.commit()
