
import argparse
import logging
import sys
import pandas as pd
import xlsxwriter


# Command line arguments
parser = argparse.ArgumentParser(description='Formats output from ANSYS Fluent .out files.')
parser.add_argument("-f", "--file", help="Full path to output .out file, default is C:\\Users\\Rutgers\\Desktop\\David_Lewus_Research\\CFD\\Energy_Model_v3\\report-file-0.out", default='C:\\Users\\Rutgers\\Desktop\\David_Lewus_Research\\CFD\\Energy_Model_v3\\report-file-0.out')
parser.add_argument("-p", "--path", help="Use when your path is C:\\Users\\Rutgers\\Desktop\\David_Lewus_Research\\CFD\\Energy_Model_v3 and you just want to put the relative path from there.", action="store_true")
parser.add_argument("-e", "--excel", help="Creates excel output in C:\\Users\\Rutgers\\Desktop\\David_Lewus_Research\\CFD\\Energy_Model_v3\\", action="store_true")
parser.add_argument("-t", "--tenminute", help="Excel output is based on ten minute timestep", action="store_true")
args = parser.parse_args()
filename = args.file
path = args.path

# Generate filename with path option
if path:
    filename = f'C:\\Users\\Rutgers\\Desktop\\David_Lewus_Research\\CFD\\Energy_Model_v3\\{filename}'


# Create logger
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Try to open file and read data
try:
    with open(filename) as f:
        logging.info('File opened')

        data = {}

        for line in f:
            # data lines
            if line[0] not in '"(' and line.strip():
                line = line.strip().split()
                line = [float(ele) for ele in line]
                # convert temp from K to C
                floor_temp = line[1] - 273.15
                air_temp = line[5] - 273.15
                plant_temp = line[7] - 273.15
                # convert RH from number to %
                air_rh = line[4] * 100
                plant_rh = line[8] * 100
                # set radiation
                radiation = line[3]
                # set vents, 0 - closed, 1 - open
                vents = line[9]
                if vents == 0:
                    vents = "closed"
                elif vents == 1:
                    vents = "open"
                # round air speed to 5 places
                air_speed = round(line[6], 5)
                # round everything else to 2 places
                rounded = [floor_temp, air_temp, plant_temp, air_rh, plant_rh, vents, radiation, air_speed]
                rounded[:-1] = [round(ele, 2) if isinstance(ele, float) else ele for ele in rounded[:-1]]
                data[line[2]] = rounded

            # heading line
            elif line[0] == '(':
                # strip elements down to headings and remove quotes and blank spaces
                line = line[1:-2].strip().replace(" ", "").split('"')
                line = [ele for ele in line if ele.strip()]
                # reorder items
                line = [line[2], line[1], line[5], line[7], line[4], line[8], line[9], line[3], line[6]]
                headers = line

    # convert to dataframe
    if args.tenminute:
        data_10 = {}
        for time in data.keys():
            if time % 600 == 0:
                data_10[time] = data[time]
        df = pd.DataFrame.from_dict(data_10, orient='index', columns=headers[1:])
    else:
        df = pd.DataFrame.from_dict(data, orient='index', columns=headers[1:])
    df.index.name = headers[0]
    # convert flow time from seconds to hh:mm
    df.index = pd.to_datetime(df.index, unit='s').strftime('%H:%M')
    # export that dataframe to excel if excel option given
    if args.excel:
        try:
            with pd.ExcelWriter(f'C:\\Users\\Rutgers\\Desktop\\David_Lewus_Research\\CFD\\Energy_Model_v3\\CFD_output.xlsx') as writer:
                filename = filename.replace("\\", "~")
                filename = filename.replace(" ", "")
                filename = filename.replace("/", "~")
                if len(filename) > 31:
                    filename = filename[-31:]
                df.to_excel(writer, sheet_name=f'{filename}')
                for column in df:
                    column_width = max(df[column].astype(str).map(len).max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    writer.sheets[f'{filename}'].set_column(col_idx + 1, col_idx + 1, column_width)
            logging.info('Output written to excel')
        except xlsxwriter.exceptions.FileCreateError:
            logging.error('CFD_output.xlsx must be closed before it can be overwritten')
    else:
        print("Time  | Temp(air) | Temp(floor) |  RH%  | Vent |  Rad  | Velocity")
        # iterate over last 10 rows
        for index, row in df[-10:].iterrows():
            print(f"{index} |{row[1]:^11.2f}|{row[0]:^13.2f}|{row[3]:^7.2f}|{row[5]:^6s}|{row[6]:^7.2f}|{row[7]:^9.5f}")  # ^ centers the number, 11.2f means ll spaces 2 reserved for after decimal
    logging.info('File closed')
except FileNotFoundError:
    logging.error('File not found.')

except Exception:
    logging.error("Unknown Error:", exc_info=True)
