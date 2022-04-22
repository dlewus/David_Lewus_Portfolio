'''
This program works in conjuction with weather_data_scraper
to compile all the months into one file per year
'''

import pandas as pd
import sys

# set up date to read in files
year = "2019"

months = []
for i in range(7, 8):
    if i < 10:
        i = f'0{i}'
    else:
        i = f'{i}'
    months.append(i)


for month in months:
    # Reads in excel document where each sheet is a day into a panda df
    all_sheets = pd.read_excel(f"{month}-{year}.xlsx", sheet_name=None, index_col=0)
    # Each sheet is a key
    for key in all_sheets:
        # Need to change index (Time column) to include day
        as_list = all_sheets[key].index.tolist()
        date = key.split("-")
        if date[0][0] == '0':
            date[0] = date[0][1]
        if date[1][0] == '0':
            date[1] = date[1][1]
        date = '/'.join(date)
        for index, time in enumerate(as_list):
            time = f'{date}/{year} {time}'
            as_list[index] = time
        all_sheets[key].index = as_list
    # Concatenates all sheets into one df
    df = pd.concat(all_sheets)

    # write to excel file, tries to make a new sheet of the month on exisiting year file, makes new year file if it doesn't exist
    try:
        with pd.ExcelWriter(f'{year}.xlsx', mode='a') as writer:
            df.to_excel(writer, sheet_name=f'{month}-{year}')
    except FileNotFoundError:
        df.to_excel(f'{year}.xlsx', sheet_name=f'{month}-{year}')
    # updates on progress
    output_str = f'{month} is finished...\n'
    sys.stdout.write(output_str)
    sys.stdout.flush()

# updates on finish
output_str = f'Finished...\n'
sys.stdout.write(output_str)
sys.stdout.flush()
