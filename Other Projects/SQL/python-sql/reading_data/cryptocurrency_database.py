import sqlite3
import pandas as pd

# create a new connection to a db in memory
conn = sqlite3.connect(':memory:')

# create cursor
c = conn.cursor()

# turn sql code into a db
c.executescript(open('cryptos.sql', 'r').read())

crypto_df = pd.read_sql('''SELECT cryptocoins_cryptocurrency.name AS coin_name,
    cryptocoins_exchange.name AS exchange,
    cryptocoins_cryptocurrency.symbol,
    cryptocoins_cryptocurrency.price_usd,
    cryptocoins_cryptocurrency.percent_change_7d
    FROM cryptocoins_cryptocurrency
    INNER JOIN cryptocoins_exchange
    ON cryptocoins_cryptocurrency.exchange_id=cryptocoins_exchange.id;''',
    conn)

weekly_change_df = crypto_df.sort_values(by=['percent_change_7d'], ascending=False)

print(weekly_change_df)
