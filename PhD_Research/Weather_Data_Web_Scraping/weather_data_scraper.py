'''
This code pulls weather data from wunderground.com to an excel spreadsheet
You can change the site you are looking at in the graph_url and table_url variables
You can change the year and months you are looking at by altering the calendar variable
Keep in mind that each day takes 15-30s (depending on internet and CPU speed), so a full year will take ~1.5-3h
'''


from bs4 import BeautifulSoup
import requests
import sys
import io
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from time import sleep

# encoding fix
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

# date
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

# comment out months if you don't want to collect data on them
#calendar['01'] = days
#calendar['02'] = days[:28]  # change to days[:29] for leap years
#calendar['03'] = days
#calendar['04'] = days[:30]
#calendar['05'] = days
#calendar['06'] = days[9:30]
calendar['07'] = days
#calendar['08'] = days
#calendar['09'] = days[:30]
#calendar['10'] = days
#calendar['11'] = days[:30]
#calendar['12'] = days

for month in calendar:
    for day in calendar[month]:

        # urls
        graph_url = f'https://www.wunderground.com/dashboard/pws/KPAPENNS17/graph/{year}-{month}-{day}/{year}-{month}-{day}/daily'
        table_url = f'https://www.wunderground.com/dashboard/pws/KPAPENNS17/table/{year}-{month}-{day}/{year}-{month}-{day}/daily'

        # dataframe setup
        df = pd.DataFrame(columns=['Time', 'Profile Time', 'Temperature (C)', 'Humidity (%)', 'Wind Speed (m/s)', 'Wind Direction', 'Solar(W/m2)'])

        # browser set up
        browser = webdriver.Firefox()
        browser.get(graph_url)
        delay = 5  # secods

        while True:
            try:
                # open page and wait for graph to load
                WebDriverWait(browser, delay)
                sleep(5)

                # get html from webpage and store in Beautiful Soup object
                html = browser.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
                soup = BeautifulSoup(html, 'lxml')

                # search html for wind direction scatter plot graph
                graph = soup.find('g', class_='plot winddir scatter')
                break
            except TimeoutException:
                print("Loading took too much time!-Try again")
        browser.close()

        # make a list of all html strings with 'circle', which is where the data is stored for the scatter plot
        graph = graph.find_all('circle')
        graph_data = []

        for i in range(len(graph)):
            graph_data_i_str = str(graph[i])

            # cy and r bound the data in the html
            cy = graph_data_i_str.index('cy')
            r = graph_data_i_str.index('r', 4)

            # transform the data to degrees from (x,y) coordinates
            degree = int(360 - (float(graph_data_i_str[cy + 4:r - 2]) / 150) * 360)
            graph_data.append(degree)

        # using requests to get html from table
        source_table = requests.get(table_url).text
        soup = BeautifulSoup(source_table, 'lxml')
        table = soup.find('table', class_='history-table desktop-table')
        rows_table = table.find_all('tr')

        for i in range(2, len(rows_table)):
            items = rows_table[i].find_all('td')
            profile_time = 4 + 6 * (i - 2)  # HH:MM format to integers
            temp_c = (float(items[1].text[:4]) - 32) / 1.8  # degrees F to degrees C
            wind_speed = float(items[5].text[:3]) * 0.44704  # mph to m/s
            to_append = [items[0].text, profile_time, temp_c, items[3].text[:2], wind_speed, graph_data[i - 2], items[11].text[:-6]]  # table that will become new row for dataframe
            a_series = pd.Series(to_append, index=df.columns)
            df = df.append(a_series, ignore_index=True)

        # sets the index (first column) to Time
        df = df.set_index('Time')

        # typecast the entire row to numbers from strings
        df['Humidity (%)'] = pd.to_numeric(df['Humidity (%)'])
        df['Solar(W/m2)'] = pd.to_numeric(df['Solar(W/m2)'])

        # write to excel file, tries to make a new sheet of the day on exisiting month file, makes new month file if it doesn't exist
        try:
            with pd.ExcelWriter(f'{month}-{year}.xlsx', mode='a') as writer:
                df.to_excel(writer, sheet_name=f'{month}-{day}')
        except FileNotFoundError:
            df.to_excel(f'{month}-{year}.xlsx', sheet_name=f'{month}-{day}')
        output_str = f'{month} {day} is finished...\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()
output_str = 'All dates are finished!\n'
sys.stdout.write(output_str)
sys.stdout.flush()
