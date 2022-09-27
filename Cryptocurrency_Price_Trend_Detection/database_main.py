'''
This code creates and populates a database with cryptocurrency prices
'''

import create_db as cdb
import update_db as udb

# Data Import
coin = 'ETHUSD'
timeframe = '1D'


# Create database
cdb.create_db()

cdb.populate_db([coin], [timeframe])


# Update database
udb.update(coin, timeframe)

udb.clean(coin, timeframe)
