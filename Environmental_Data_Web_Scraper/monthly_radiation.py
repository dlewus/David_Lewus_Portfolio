'''
This program reads through an excel file outputted from timestep_change.py.
It takes all the values at a given time for each month and averages them
For example, what was the average at 11:00 everyday in September 2018?
This creates a composite radiation curve that can be used to simulate the month
'''

import pandas as pd
import sys
from datetime import date, time, datetime, timedelta
from math import cos


def monthly_radiation(year, startmonth, endmonth):
    '''
    year - int of year on workbook
    startmonth - int of month on sheet to start with
    endmonth - into of month on sheet to end with
    '''

    # list to hold string version of months
    months = []

    for i in range(startmonth, endmonth + 1):
        # if month or day is less than 10, add a preceding zero: for example, the month of July is 07
        if i < 10:
            months.append(f'0{i}')
        else:
            months.append(f'{i}')

    # make a list of times on the current day from 0:00 to 23:50, with a 10m time step
    time_list = []
    start = datetime.combine(date.today(), time(0, 0))
    for i in range(144):
        time_list.append(start.strftime("%H:%M"))
        start += timedelta(minutes=10)

    rad = {}

    # makes a dictionary where the 1st layer keys are the months, and the 2nd layer keys are the 10m time steps
    for month in months:
        rad[month] = {}

        # each value for the 2nd layer keys is a list that will be averaged
        for timestep in time_list:
            rad[month][timestep] = []

    # loop through each month, which is one sheet
    for month in months:
        # open excel file (remove sheet_name if you want the whole file instead of 1 day, needs more code)
        sheet = pd.read_excel(f"{year}_10m.xlsx", sheet_name=f'{month}-{year}', index_col=0)
        sheet.index = pd.to_datetime(sheet.index)

        # iterate over each row (timestep) in the sheet
        for index, row in sheet.iterrows():
            radiation = float(round(row['Solar(W/m2)'], 3))
            rad[month][index.strftime('%H:%M')].append(radiation)

        # iterate over all the 2nd layer keys in the given month, averaging the values for each timestep
        for key in rad[month]:

            average_rad = sum(rad[month][key]) / len(rad[month][key])
            # break up month into first half and second half
            first_half = sum(rad[month][key][:15]) / len(rad[month][key][:15])
            second_half = sum(rad[month][key][15:]) / len(rad[month][key][15:])

            # overwrite the current timestep with the averages
            rad[month][key] = round(average_rad, 3), round(first_half, 3), round(second_half, 3)

        # write the averages for the whole month to a dataframe
        df = pd.DataFrame.from_dict(rad[month], orient='index', columns=['Solar(W/m2)', 'First Half (W/m2)', 'Second Half (W/m2)'])

        # export that dataframe to excel
        try:
            with pd.ExcelWriter(f'{year}_radiation.xlsx', mode='a') as writer:
                df.to_excel(writer, sheet_name=f'{month}-{year}')
        except FileNotFoundError:
            df.to_excel(f'{year}_radiation.xlsx', sheet_name=f'{month}-{year}')

        # display progress to the monitor
        output_str = f'{month} is finished...\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()
