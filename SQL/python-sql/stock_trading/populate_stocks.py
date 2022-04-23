import sqlite3
import config
import alpaca_trade_api as tradeapi

# Set up connection to SQL database
connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

# Fetch all stocks in the database
cursor.execute("""
    SELECT symbol, name FROM stock
""")
rows = cursor.fetchall()
symbols = [row['symbol'] for row in rows]

# Connect to Alpace API and collect all available stocks
api = tradeapi.REST(config.KEY_ID, config.SECRET_KEY, base_url=config.BASE_URL)
assets = api.list_assets()

# Add stocks to stock table that aren't already present
for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable and asset.symbol not in symbols:
            print(f"Added a new stock {asset.symbol} {asset.name}")
            cursor.execute("""
                    INSERT INTO stock (symbol, name, exchange)
                    VALUES (?, ?, ?)
            """, (asset.symbol, asset.name, asset.exchange))
    except Exception as e:
        print(asset.symbol)
        print(e)

connection.commit()
