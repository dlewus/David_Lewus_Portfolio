'''
This program reads through an excel file outputted from timestep_change.py.
It takes all the values at a given time for each month and averages them
For example, what was the average at 11:00 everyday in September 2018?
This creates a composite temperature curve that can be used to simulate the month
'''

import pandas as pd
import sys
from datetime import date, time, datetime, timedelta


def monthly_temp(year, startmonth, endmonth):
    '''
    year - int of year on workbook
    startmonth - int of month on sheet to start with
    endmonth - into of month on sheet to end with
    '''

    months = []

    # change this range to fit the months in the excel file, ensuring that the end of the range is +1 the last month
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

    temperatures = {}

    # makes a dictionary where the 1st layer keys are the months, and the 2nd layer keys are the 10m time steps
    for month in months:
        temperatures[month] = {}
        # each value for the 2nd layer keys is a list that will be averaged
        for timestep in time_list:
            temperatures[month][timestep] = []

    # loop through each month, which is one sheet
    for month in months:
        # open excel file (remove sheet_name if you want the whole file instead of 1 day, needs more code)
        sheet = pd.read_excel(f"{year}_10m.xlsx", sheet_name=f'{month}-{year}', index_col=0)
        sheet.index = pd.to_datetime(sheet.index)

        # iterate over each row (timestep) in the sheet
        for index, row in sheet.iterrows():
            temperature = round(row['Temperature (C)'], 2)
            temperatures[month][index.strftime('%H:%M')].append(temperature)

        # iterate over all the 2nd layer keys in the given month, averaging the values for each timestep
        for key in temperatures[month]:

            average_temperature = sum(temperatures[month][key]) / len(temperatures[month][key])
            # break up month into first half and second half
            first_half = sum(temperatures[month][key][:15]) / len(temperatures[month][key][:15])
            second_half = sum(temperatures[month][key][15:]) / len(temperatures[month][key][15:])

            # overwrite the current timestep with the averages
            temperatures[month][key] = round(average_temperature, 2), round(first_half, 2), round(second_half, 2)

        # write the averages for the whole month to a dataframe
        df = pd.DataFrame.from_dict(temperatures[month], orient='index', columns=['Temperature (C)', 'First Half (C)', 'Second Half (C)'])

        # export that dataframe to excel
        try:
            with pd.ExcelWriter(f'{year}_averaged.xlsx', mode='a') as writer:
                df.to_excel(writer, sheet_name=f'{month}-{year}_halved')
        except FileNotFoundError:
            df.to_excel(f'{year}_averaged.xlsx', sheet_name=f'{month}-{year}_halved')

        # display progress to the monitor
        output_str = f'{month} is finished...\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()
