import sqlite3
import config

# Set up connection to SQL database
connection = sqlite3.connect(config.DB_FILE)

cursor = connection.cursor()

# Create table that holds stock names and ticker symbols
cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY,
        symbol TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        exchange TEXT NOT NULL
    )
""")

# Create table to hold stock prices, which will get regularly updated
cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_price (
        id INTEGER PRIMARY KEY,
        stock_id INTEGER,
        date NOT NULL,
        open NOT NULL,
        high NOT NULL,
        low NOT NULL,
        close NOT NULL,
        volume NOT NULL,
        FOREIGN KEY (stock_id) REFERENCES stock (id)
    )
""")

# Create tables to hold trading strategies
cursor.execute("""
    CREATE TABLE IF NOT EXISTS strategy (
        id INTEGER PRIMARY KEY,
        name NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_strategy (
        stock_id INTEGER NOT NULL,
        strategy_id INTEGER NOT NULL,
        FOREIGN KEY (stock_id) REFERENCES stock (id)
        FOREIGN KEY (strategy_id) REFERENCES strategy (id)
        UNIQUE(stock_id,strategy_id)
    )
""")

strategies = ['opening_range_breakout', 'opening_range_breakdown']

for strategy in strategies:
    cursor.execute("""
        INSERT INTO strategy (name) VALUES (?)
    """, (strategy,))

connection.commit()
