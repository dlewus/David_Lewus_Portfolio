import sqlite3
import config
import pandas as pd


def load_sql_from_date(coin, timeframe, timestamp):

    sql = f"""
    SELECT *
    FROM {coin}_price_{timeframe}
    WHERE timestamp > '{timestamp}'
    """

    return sql


def load_df_from_date(coin, timeframe, timestamp, messages=True):

    # Set up database connection
    connection = sqlite3.connect(config.DB_FILE)

    # Load SQL
    sql = load_sql_from_date(coin, timeframe, timestamp)
    if messages:
        print('reading...')
    bars = pd.read_sql(
        sql, connection,
        index_col='timestamp',
        parse_dates=['timestamp'])
    if messages:
        print('done reading!')
    return bars
