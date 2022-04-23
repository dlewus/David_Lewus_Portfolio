import sqlite3
import pandas as pd

# create a new connection to a db in memory
conn = sqlite3.connect(':memory:')

# create cursor
c = conn.cursor()

# turn sql code into a db
c.executescript(open('van_crime_2003.sql', 'r').read())

van_crimes_df = pd.read_sql('''SELECT TYPE, MONTH, DAY, NEIGHBOURHOOD
    FROM van_crimes WHERE NEIGHBOURHOOD IN ('Stanley Park', 'West End');''', conn)

crime_types_count = van_crimes_df['TYPE'].value_counts()

print(crime_types_count)
