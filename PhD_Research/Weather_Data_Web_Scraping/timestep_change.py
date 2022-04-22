'''
This program reads in data from an excel sheet and transforms from 6m timestep to 10m timestep
'''

import pandas as pd
import sys
from datetime import date, time, datetime, timedelta

# month and year of sheet you want to convert
# if month or day is less than 10, add a preceding zero: for example, the month of July is 07
month = '11'
year = '2019'

# set up variable to loop through everyday in a month
calendar = {}
days = []
for i in range(1, 32):
    if i < 10:
        i = f'0{i}'
    else:
        i = f'{i}'
    days.append(i)

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
calendar['12'] = days

# for day in calendar[month]:

#     # open excel file (remove sheet_name if you want the whole file instead of 1 day, needs more code)
#     sheet = pd.read_excel(f"{month}-{year}.xlsx", sheet_name=f'{month}-{day}', index_col=0)

#     # stops program if input dataset is incomplete
#     if len(sheet) != 240:
#         output_str = f'Incomplete data on {month}/{day}, {240-len(sheet)} points missing\n'
#         sys.stdout.write(output_str)
#         sys.stdout.flush()
#     else:
#         output_str = f'...\n'
#         sys.stdout.write(output_str)
#         sys.stdout.flush()

# loop through every day in the selected month
for day in calendar[month]:

    # open excel file (remove sheet_name if you want the whole file instead of 1 day, needs more code)
    sheet = pd.read_excel(f"{month}-{year}.xlsx", sheet_name=f'{month}-{day}', index_col=0)

    # stops program if input dataset is incomplete
    if len(sheet) != 240:
        print(f"Incomplete data on {month}/{day}, {240-len(sheet)} points missing")
        break

    # make a list of times on the current day from 0:00 to 23:50, with a 10m time step
    time_list = []
    d = date(year=int(year), month=int(month), day=int(day))
    start = datetime.combine(d, time(0, 0))
    for i in range(144):
        time_list.append(start.strftime("%m/%d/%y %H:%M"))
        start += timedelta(minutes=10)

    # make a new temporary dataframe with the index being the 10m time step list and the columns being the same as those in the import excel sheet
    df_temp = pd.DataFrame(index=time_list, columns=sheet.columns.tolist())

    # average the data from the excel sheet to be a 10m timestep
    for row in sheet.columns:

        for index, item in enumerate(sheet[row].tolist()):
            # HH:00 and HH:30 don't get averaged
            if index % 5 == 0:
                df_temp[row][int(index / 5) * 3] = item
            # HH:06 and HH:12 get averaged to HH:10, HH:36 and HH:42 get averaged to HH:40
            if index % 5 == 1:
                average = (float(item) + float(sheet[row][index + 1])) / 2
                df_temp[row][int(index / 5) * 3 + 1] = average
            # HH:18 and HH:24 get averaged to HH:10, HH:48 and HH:54 get averaged to HH:50
            if index % 5 == 3:
                average = (float(item) + float(sheet[row][index + 1])) / 2
                df_temp[row][int(index / 5) * 3 + 2] = item

    # add temporary dataframe to master dataframe
    if day == '01':
        df = df_temp
    else:
        df = df.append(df_temp)

    # updates progress in the console
    output_str = f'{month}/{day} is finished...\n'
    sys.stdout.write(output_str)
    sys.stdout.flush()

# only run this if program completed successfully
if day == calendar[month][-1]:
    output_str = 'All dates are finished!\n'
    sys.stdout.write(output_str)
    sys.stdout.flush()

    # remove profile time column
    df = df.drop(columns='Profile Time')

    # write to excel file, tries to make a new sheet of the month on exisiting year file, makes new year file if it doesn't exist
    try:
        with pd.ExcelWriter(f'{year}_10m.xlsx', mode='a') as writer:
            df.to_excel(writer, sheet_name=f'{month}-{year}')
    except FileNotFoundError:
        df.to_excel(f'{year}_10m.xlsx', sheet_name=f'{month}-{year}')
