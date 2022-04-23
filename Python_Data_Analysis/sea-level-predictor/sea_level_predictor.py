import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

def draw_plot():
    # Read data from file
    df = pd.read_csv('epa-sea-level.csv')

    # Create scatter plot
    fig, ax = plt.subplots(figsize=(7,5))
    plt.scatter(df['Year'], df['CSIRO Adjusted Sea Level'], c='blue', label='data')

    # Create first line of best fit
    res1 = linregress(df['Year'], df['CSIRO Adjusted Sea Level'])
    x1 = np.arange(1880, 2051)
    plt.plot(x1, res1.intercept + res1.slope*x1, c='red', label='fitted to all data')


    # Create second line of best fit
    res2 = linregress(df['Year'].iloc[-14:], df['CSIRO Adjusted Sea Level'].iloc[-14:])
    x2 = np.arange(2000, 2051)
    plt.plot(x2, res2.intercept + res2.slope*x2, c='orange', label='fitted to data after 2000')

    # Add labels and title
    ax.set_xlabel('Year')
    ax.set_ylabel('Sea Level (inches)')
    ax.set_title('Rise in Sea Level')
    plt.legend()

    # Save plot and return data for testing (DO NOT MODIFY)
    plt.savefig('sea_level_plot.png')
    return plt.gca()
