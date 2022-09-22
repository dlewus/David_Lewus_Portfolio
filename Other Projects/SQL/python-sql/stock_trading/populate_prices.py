import config
import sqlite3
import alpaca_trade_api as tradeapi

# Set up connection to SQL database
connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

# Fetch all stocks in the database
cursor.execute("""
    SELECT id, symbol, name FROM stock
    """)

rows = cursor.fetchall()

symbols = []
stock_dict = {}
for row in rows:
    symbol = row['symbol']
    symbols.append(symbol)
    stock_dict[symbol] = row['id']

# Connect to Alpace API
api = tradeapi.REST(config.KEY_ID, config.SECRET_KEY, base_url=config.BASE_URL)

# Create a chunk to only work with a certain amount of data at a time
chunk_size = 200
for i in range(0, len(symbols), chunk_size):
    symbol_chunk = symbols[i:i + chunk_size]
    # Get stock price data from Alpaca API
    barsets = api.get_barset(symbol_chunk, 'day')

    # Add stock price data to stock_price table
    for symbol in barsets:
        print(f'processing symbol {symbol}')

        for bar in barsets[symbol]:
            stock_id = stock_dict[symbol]
            cursor.execute("""
                INSERT INTO stock_price (stock_id, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v))

connection.commit()
