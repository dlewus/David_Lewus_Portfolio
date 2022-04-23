import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pandas.plotting import register_matplotlib_converters
import calendar
register_matplotlib_converters()

# Import data (Make sure to parse dates. Consider setting index column to 'date'.)
df = pd.read_csv('fcc-forum-pageviews.csv',
        parse_dates = [0],
        index_col = [0])

# Clean data
df.drop(df[df['value'] < df['value'].quantile(0.025)].index, inplace=True)
df.drop(df[df['value'] > df['value'].quantile(0.975)].index, inplace=True)



def draw_line_plot():
    # Draw line plot
    fig, ax = plt.subplots(figsize=(15, 5))

    ax.plot(
        df.index, df.value, color='red')
    ax.set_xlabel('Date')
    ax.set_ylabel('Page Views')
    ax.set_title('Daily freeCodeCamp Forum Page Views 5/2016-12/2019')


    # Save image and return fig (don't change this part)
    fig.savefig('line_plot.png')
    return fig

def draw_bar_plot():
    # Copy and modify data for monthly bar plot
    df_bar = df
    df_bar['mm'] = df_bar.index.to_period('M')
    df_bar = df_bar.groupby(by=['mm']).mean()
    df_bar['Months'] = df_bar.index.month
    df_bar['Years'] = df_bar.index.year

    df_bar['Months'] = df_bar['Months'].apply(lambda x: calendar.month_abbr[x])



    # Draw bar plot
    fig, ax = plt.subplots(figsize=(10, 10))

    ax = sns.barplot(
        x='Years', y='value', hue='Months', data=df_bar, edgecolor='.2')

    ax.set_ylabel('Average Page Views')

    # Save image and return fig (don't change this part)
    fig.savefig('bar_plot.png')
    return fig

def draw_box_plot():
    # Prepare data for box plots (this part is done!)
    df_box = df.copy()
    df_box.reset_index(inplace=True)
    df_box['year'] = [d.year for d in df_box.date]
    df_box['month'] = [d.strftime('%b') for d in df_box.date]

    # Draw box plots (using Seaborn)
    fig, ax = plt.subplots(1, 2, figsize=(18, 5))

    sns.boxplot(
        ax=ax[0], x='year', y='value',
        data=df_box, fliersize=1.5, linewidth=.5)
    sns.boxplot(
        ax=ax[1], x='month', y='value',
        data=df_box, fliersize=1.5, linewidth=.5)

    ax[0].set_xlabel('Year')
    ax[1].set_xlabel('Month')
    ax[0].set_ylabel('Page Views')
    ax[1].set_ylabel('Page Views')
    ax[0].set_title('Year-wise Box Plot (Trend)')
    ax[1].set_title('Month-wise Box Plot (Seasonality)')

    ax[0].set_ylim([0,200000])
    ax[1].set_ylim([0,200000])

    # Save image and return fig (don't change this part)
    fig.savefig('box_plot.png')
    return fig
