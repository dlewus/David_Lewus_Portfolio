import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Import data
df = pd.read_csv('medical_examination.csv', header=[0])

# Add 'overweight' column
df['overweight'] = df['weight']/((df['height']/100)**2)
df.loc[df['overweight'] <= 25, 'overweight'] = 0
df.loc[df['overweight'] > 25, 'overweight'] = 1


# Normalize data by making 0 always good and 1 always bad. If the value of 'cholesterol' or 'gluc' is 1, make the value 0. If the value is more than 1, make the value 1.
df.loc[df['cholesterol'] == 1, 'cholesterol'] = 0
df.loc[df['cholesterol'] > 1, 'cholesterol'] = 1
df.loc[df['gluc'] == 1, 'gluc'] = 0
df.loc[df['gluc'] > 1, 'gluc'] = 1


# Draw Categorical Plot
def draw_cat_plot():
    # Create DataFrame for cat plot using `pd.melt` using just the values from 'cholesterol', 'gluc', 'smoke', 'alco', 'active', and 'overweight'.
    df_cat = pd.melt(df, value_vars=['cholesterol', 'gluc', 'smoke', 'alco', 'active', 'overweight'], id_vars=['cardio'])
    df_cat['value'] = df_cat['value'].astype('int64')

    # Group and reformat the data to split it by 'cardio'. Show the counts of each feature. You will have to rename one of the columns for the catplot to work correctly.

    fig, ax = plt.subplots(figsize=(7, 5))
    # Draw the catplot with 'sns.catplot()'
    fig = sns.catplot(
        x='variable',
        hue='value',
        kind='count',
        data=df_cat,
        col='cardio',
        order=['active','alco','cholesterol','gluc','overweight','smoke']
                        )

    fig.set_axis_labels("", "total")


    # Do not modify the next two lines
    fig.savefig('catplot.png')
    return fig


# Draw Heat Map
def draw_heat_map():
    # Clean the data
    df.drop(df[df['ap_lo'] > df['ap_hi']].index, inplace=True)
    df.drop(df[df['height'] < df['height'].quantile(0.025)].index, inplace=True)
    df.drop(df[df['height'] > df['height'].quantile(0.975)].index, inplace=True)
    df.drop(df[df['weight'] < df['weight'].quantile(0.025)].index, inplace=True)
    df.drop(df[df['weight'] > df['weight'].quantile(0.975)].index, inplace=True)
    df_heat = df

    # Calculate the correlation matrix
    corr = df.corr()

    # Generate a mask for the upper triangle
    mask = np.zeros_like(corr)
    mask[np.triu_indices_from(mask)] = True



    # Set up the matplotlib figure
    fig, ax = plt.subplots(figsize=(7, 5))

    # Draw the heatmap with 'sns.heatmap()'
    ax = sns.heatmap(corr, mask=mask, annot=True, fmt='.1f',vmin=-0.16, vmax=0.32, center=0, linewidths=0.5)



    # Do not modify the next two lines
    fig.savefig('heatmap.png')
    return fig
