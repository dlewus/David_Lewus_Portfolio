import sqlite3
import pandas as pd

#conn = sqlite3.connect('van_crime_2003.db')

# cur = conn.cursor()

# cur.execute('SELECT * FROM van_crimes LIMIT 5;')

# results = pd.DataFrame(cur.fetchall())

# print(results)

# cur.close()
# conn.close()

# create a new connection to a db in memory
conn = sqlite3.connect(':memory:')

# create cursor
c = conn.cursor()

# turn sql code into a db
c.executescript(open('van_crime_2003.sql', 'r').read())

df = pd.read_sql('SELECT * FROM van_crimes;', conn)

late_crimes = df[df['HOUR'] >= 18.0]

dangerous_month_crimes = df["MONTH"].value_counts().head(1)

print(dangerous_month_crimes)


