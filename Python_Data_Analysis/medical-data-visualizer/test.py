import matplotlib.pyplot as plt
import seaborn as sns


#plt.show()

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

df_cat = pd.melt(df, value_vars=['cholesterol', 'gluc', 'smoke', 'alco', 'active', 'overweight'], id_vars=['cardio'])
df_cat['value'] = df_cat['value'].astype('int64')

df.drop(df[df['ap_lo'] > df['ap_hi']].index, inplace=True)
df.drop(df[df['height'] < df['height'].quantile(0.025)].index, inplace=True)
df.drop(df[df['height'] > df['height'].quantile(0.975)].index, inplace=True)
df.drop(df[df['weight'] < df['weight'].quantile(0.025)].index, inplace=True)
df.drop(df[df['weight'] > df['weight'].quantile(0.975)].index, inplace=True)

corr = df.corr().round(1)
mask = np.zeros_like(corr)
mask[np.triu_indices_from(mask)] = True

g = sns.heatmap(corr, mask=mask, annot=True, vmin=-0.16, vmax=0.32, center=0, linewidths=0.5)
plt.show()

#fig, ax = plt.subplots(figsize=(15,7))
# g = sns.catplot(
#     x='variable',
#     hue='value',
#     kind='count',
#     data=df_cat,
#     col='cardio',
#     order=['active','alco','cholesterol','gluc','overweight','smoke'])
# g.set_axis_labels("", "total")
#plt.show()

