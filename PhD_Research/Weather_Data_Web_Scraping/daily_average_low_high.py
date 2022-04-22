'''
This program reads through an excel file outputted from timestep_change.py. Given a certain period of days, it will report the average high, average low,
and average daily temperatures.
'''

import pandas as pd
import sys

# year of sheet you want to calculate
year = '2019'


months = []

# change this range to fit the months in the excel file, ensuring that the end of the range is +1 the last month
for i in range(1, 12):
    # if month or day is less than 10, add a preceding zero: for example, the month of July is 07
    if i < 10:
        months.append(f'0{i}')
    else:
        months.append(f'{i}')

averages = {}

# loop through each month, which is one sheet
for month in months:
    # open excel file (remove sheet_name if you want the whole file instead of 1 day, needs more code)
    sheet = pd.read_excel(f"{year}_10m.xlsx", sheet_name=f'{month}-{year}', index_col=0)
    averages[month] = {}
    sheet.index = pd.to_datetime(sheet.index)
    day = 1  # start day count at first day of month
    dailya = 0  # daily average
    high = -273  # lowest temp possible
    low = 100  # unfeasible high air temp
    count = 0

    for index, row in sheet.iterrows():
        if index.day == day:
            temperature = round(row['Temperature (C)'], 2)
            dailya += temperature
            count += 1
            if temperature > high:
                high = temperature
            if temperature < low:
                low = temperature
        else:
            if count != 0:
                # calculate average
                dailya /= count
                dailya = round(dailya, 2)
                # save to dictionary
                averages[month][day] = [dailya, high, low]
            # increment day
            day += 1
            # reset variables
            average = 0
            high = -273
            low = 100
            count = 0

    montha = 0
    monthh = 0
    monthl = 0
    firsta = 0
    firsth = 0
    firstl = 0
    seconda = 0
    secondh = 0
    secondl = 0
    firstcount = 0
    secondcount = 0

    for key in averages[month]:
        montha += averages[month][key][0]
        monthh += averages[month][key][1]
        monthl += averages[month][key][2]
        if int(key) <= 15:
            firsta += averages[month][key][0]
            firsth += averages[month][key][1]
            firstl += averages[month][key][2]
            firstcount += 1
        elif int(key) > 15:
            seconda += averages[month][key][0]
            secondh += averages[month][key][1]
            secondl += averages[month][key][2]
            secondcount += 1

    count = len(averages[month].keys())

    montha /= count
    monthh /= count
    monthl /= count

    firsta /= firstcount
    firsth /= firstcount
    firstl /= firstcount

    seconda /= secondcount
    secondh /= secondcount
    secondl /= secondcount

    print(f'{month} | Monthly Average: {round(montha,2)} C | Average Monthly High: {round(monthh,2)} C | Average Monthly Low: {round(monthl,2)} C')
    print(f'{month} First Half | Average: {round(firsta,2)} C | Average High: {round(firsth,2)} C | Average Low: {round(firstl,2)} C')
    print(f'{month} Second Half | Average: {round(seconda,2)} C | Average High: {round(secondh,2)} C | Average Low: {round(secondl,2)} C')
