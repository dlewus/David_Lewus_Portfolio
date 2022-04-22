'''This adds a sheet and calculates DLI. It takes sheet in the format made from timestep_change.py
1. Convert W*m-2 to J*m-2: With a ten minute timestep, multiply each timestep by 60s*10m = 600
2. Sum the total J*m-2 per day
3. Convert J*m-2*d-1 to MJ*m-2*d-1: divide by 1,000,000
4. Convert MJ*m-2*d-1 to mol*m-2*d-1: multiply by conversion factor fo 2.0804
'''


import pandas as pd
import sys

# year of sheet you want to add DLI
year = "2019"

# sets up calendar that will pass dates to the browser
calendar = {}
days = []
for i in range(1, 32):
    if i < 10:
        i = f'0{i}'
    else:
        i = f'{i}'
    days.append(i)

# comment out months that don't exist in dataset
calendar['01'] = days
calendar['02'] = days[:13] + days[19:24] + days[25:28]  # change to days[:29] for leap years
# 2/19 had a big gap from 2/14/19 - 2/20/19 and on 2/25/19
calendar['03'] = days
calendar['04'] = days[:30]
calendar['05'] = days
calendar['06'] = days[:30]
calendar['07'] = days[:20] + days[22:]
# last 5 hors of 7/21/19 and first half of 7/22/19 is missing
calendar['08'] = days[:17] + days[18:]
# 5 hours in row missing on 8/18/19
calendar['09'] = days[:30]
calendar['10'] = days
calendar['11'] = days[:30]
#calendar['12'] = days

dli_dict = {}  # set up dictionary to collect DLI
conversion_factor = 2.0804  # mol * m-2 * d-1 per MJ*m-2*d-1

# iterate over each months in dataset
for month in calendar:
    # set up and reset total to calculate the monthly average
    total = 0
    # iterate over each day in the month
    for day in calendar[month]:
        # read in the sheet for month and day
        sheet = pd.read_excel(f"Datasets/{month}-{year}.xlsx", sheet_name=f'{month}-{day}', index_col=0)
        # calculate DLI, based off steps at top of this file
        mj_day = sheet['Solar(W/m2)'].sum() * 600 / 1000000
        dli = mj_day * conversion_factor
        # add the current days DLI to the dictionary that collects DLI
        dli_dict[f'{month}/{day}/{year}'] = dli
        # add the DLI to the monthly total
        total += dli
        # monitor progress
        output_str = f'{day}...'
        sys.stdout.write(output_str)
        sys.stdout.flush()
    # calculate and print monthly average
    monthly_average = total / len(calendar[month])
    print(f'Monthly average for {month}: {monthly_average}')

# convert dli_dict to dataframe to be outputted to excel
df = pd.DataFrame.from_dict(dli_dict, orient='index', columns=['DLI (mol * m-2 * d-1)'])

# add a sheet and output to 10m data sheet
with pd.ExcelWriter(f'{year}_10m.xlsx', mode='a') as writer:
    df.to_excel(writer, sheet_name=f'DLI')
