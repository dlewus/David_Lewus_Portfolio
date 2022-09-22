'''
This program reads through an excel file outputted from timestep_change.py.
It takes all the values at a given time for each month and averages them
For example, what was the average at 11:00 everyday in September 2018?
This creates a composite wind speed curve that can be used to simulate the month
'''

import pandas as pd
import sys
from datetime import date, time, datetime, timedelta
from math import cos


def monthly_temp(year, startmonth, endmonth):
    '''
    year - int of year on workbook
    startmonth - int of month on sheet to start with
    endmonth - into of month on sheet to end with
    '''
    # list to hold string version of months
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

    wspeed = {}
    wdirection = {}

    # makes a dictionary where the 1st layer keys are the months, and the 2nd layer keys are the 10m time steps
    for month in months:
        wspeed[month] = {}
        wdirection[month] = {}
        # each value for the 2nd layer keys is a list that will be averaged
        for timestep in time_list:
            wspeed[month][timestep] = []
            wdirection[month][timestep] = []

    # loop through each month, which is one sheet
    for month in months:
        # open excel file (remove sheet_name if you want the whole file instead of 1 day, needs more code)
        sheet = pd.read_excel(f"{year}_10m.xlsx", sheet_name=f'{month}-{year}', index_col=0)
        sheet.index = pd.to_datetime(sheet.index)

        # iterate over each row (timestep) in the sheet
        for index, row in sheet.iterrows():
            speed = float(round(row['Wind Speed (m/s)'], 3))
            direction = float(row['Wind Direction'])
            # only save if wind direction is close to prevailing
            if direction > 230 and direction < 290:
                wspeed[month][index.strftime('%H:%M')].append(speed)
                wdirection[month][index.strftime('%H:%M')].append(direction)
            # if not close to prevailing, find component of velocity that is normal to vents
            else:
                x_component = cos(259.6 - direction)
                # if there is a component going through leeward vent, set component 0
                if x_component < 0:
                    x_component = 0
                wspeed[month][index.strftime('%H:%M')].append(x_component * speed)
                wdirection[month][index.strftime('%H:%M')].append(259.6)
            # uncomment if you want unaltered results, comment out everything within the if/else statement
            # wspeed[month][index.strftime('%H:%M')].append(speed)
            # wdirection[month][index.strftime('%H:%M')].append(direction)

        # iterate over all the 2nd layer keys in the given month, averaging the values for each timestep
        for key in wspeed[month]:

            average_speed = sum(wspeed[month][key]) / len(wspeed[month][key])
            # break up month into first half and second half
            s_first_half = sum(wspeed[month][key][:15]) / len(wspeed[month][key][:15])
            s_second_half = sum(wspeed[month][key][15:]) / len(wspeed[month][key][15:])

            average_direction = sum(wdirection[month][key]) / len(wdirection[month][key])
            # break up month into first half and second half
            d_first_half = sum(wdirection[month][key][:15]) / len(wdirection[month][key][:15])
            d_second_half = sum(wdirection[month][key][15:]) / len(wdirection[month][key][15:])

            # overwrite the current timestep with the averages
            wspeed[month][key] = round(average_speed, 3), round(average_direction), round(s_first_half, 3), round(d_first_half, 3), round(s_second_half, 3), round(d_second_half, 3)

        # write the averages for the whole month to a dataframe
        df = pd.DataFrame.from_dict(wspeed[month], orient='index', columns=['Wind Speed (m/s)', 'Wind Direction', 'First Half (m/s)',
                                                                            'First Half Direction', 'Second Half (m/s)', 'Second Half Direction'])

        # export that dataframe to excel
        try:
            with pd.ExcelWriter(f'{year}_wind.xlsx', mode='a') as writer:
                df.to_excel(writer, sheet_name=f'{month}-{year}')
        except FileNotFoundError:
            df.to_excel(f'{year}_wind.xlsx', sheet_name=f'{month}-{year}')

        # display progress to the monitor
        output_str = f'{month} is finished...\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()
