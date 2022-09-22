'''
This code combines several functions to scrape weather data,
then transform the timestep and create monthly averages for
each weather parameter.
'''

from weather_data_scraper import weather_data_scraper
from data_compile import data_compile
from timestep_change import timestep_change
from monthly_temp import monthly_temp
from monthly_wind import monthly_wind
from monthly_RH import monthly_RH
from monthly_radiation import monthly_radiation


if __name__ == '__main__':
    year = '2019'
    months = range(1, 13)
    startmonth = 1
    endmonth = 12

    # scrape data
    weather_data_scraper(year, months)

    # compile into one workbook
    data_compile(year, startmonth, endmonth)

    # change timestep from 6m to 10m
    for month in months:
        timestep_change(year, month)

    # create monthly averages for each weather parameter
    monthly_temp(year, startmonth, endmonth)
    monthly_wind(year, startmonth, endmonth)
    monthly_RH(year, startmonth, endmonth)
    monthly_radiation(year, startmonth, endmonth)
