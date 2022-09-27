'''
Functions to create features and labels for neural network
'''
import pandas_ta as ta
import pandas as pd
from scipy.interpolate import interp1d
from scipy.misc import derivative


def targetTrend(
        price,
        df_dx_value=0.001,
        buy_target=2,
        sell_target=0,
        hold_target=1):
    '''
    NOTE: This is a simplified version of label generation algorithm.
          Complexity is omitted for intellectual property protection.

    Finds trend based on first order derivative of price
    returns a Series with index matching the input price index
    price - Series of close prices with evenly spaced timeseries index
    df_dx_value - float of minimum first derivative value that indicates trend
    buy_target - int of label used for uptrends
    sell_target - int of label used for downtrends
    hold_target - int of label used for no significant trend

    '''
    x = price.index.view('int64') / 1e9  # turn timestamp to seconds
    y = price
    f = interp1d(x, y, fill_value="extrapolate")  # interpolate 1d function from time and price
    df_dx = derivative(f, x, dx=1e-6)

    return_df = pd.DataFrame(index=price.index)
    return_df['price'] = price.copy()
    return_df['df_dx'] = df_dx.copy()

    return_df['trend'] = hold_target
    return_df.loc[return_df.df_dx < (df_dx_value * -1), 'trend'] = sell_target
    return_df.loc[return_df.df_dx > df_dx_value, 'trend'] = buy_target

    return return_df.trend


def add_features(
        input_df,
        SMA_range=[10, 20, 50],
        EMA_range=[8, 21, 55],
        ZLMA_range=[8, 21, 55],
        ma=False,
        below=False,
        price_cross=False,
        supertrend=False,
        percent_diff=False):
    '''
    NOTE: This is only a sample of features added.
          Most are omitted for intellectual property protection.

    returns DataFrame with features added
    input_df - DataFrame with candlestick data (timeseries index, open high low close columns)
    SMA_range/EMA_range/ZLMA_range - list of int, can be [None]
    ma - bool, True if ma feature should be added
    below - bool, True if below feature should be added
    price_cross - bool, True if price cross feature should be added
    supertrend - bool, True if supertrend feature should be added
    percent_diff - bool, True if percent difference feature should be added
    '''

    bars = input_df.copy()

    if ma:
        # Add a column for the % difference from the SMA or EMA
        for i in SMA_range:
            bars['SMA%i' % i] = (bars.close - ta.sma(bars.close, i)) / bars.close

        for i in EMA_range:
            bars['EMA%i' % i] = (bars.close - ta.ema(bars.close, i)) / bars.close

        for i in ZLMA_range:
            bars['ZLMA%i' % i] = (bars.close - ta.zlma(bars.close, length=i)) / bars.close

    if below:

        for n in SMA_range:
            if n is None:
                break
            sma = ta.sma(bars.close, n)
            bars[f'below_SMA{n}'] = ta.above(bars.close, sma)

        for n in EMA_range:
            if n is None:
                break
            ema = ta.ema(bars.close, n)
            bars[f'below_EMA{n}'] = ta.above(bars.close, ema)

        for n in ZLMA_range:
            if n is None:
                break
            zlma = ta.zlma(bars.close, n)
            bars[f'below_ZLMA{n}'] = ta.above(bars.close, zlma)

    if price_cross:

        for i, n in enumerate(SMA_range):
            if n is None:
                break
            sma1 = ta.sma(bars.close, n)
            bars[f'price_cross_SMA{n}'] = ta.cross(sma1, bars.close)

        for i, n in enumerate(EMA_range):
            if n is None:
                break
            sma1 = ta.ema(bars.close, n)
            bars[f'price_cross_EMA{n}'] = ta.cross(sma1, bars.close)

        for i, n in enumerate(ZLMA_range):
            if n is None:
                break
            sma1 = ta.zlma(bars.close, n)
            bars[f'price_cross_ZLMA{n}'] = ta.cross(sma1, bars.close)

    if supertrend:

        bars['supertrend_ratio'] = bars.close / ta.supertrend(bars.high, bars.low, bars.close, length=10)['SUPERT_10_3.0']
        bars['supertrend_direction'] = ta.supertrend(bars.high, bars.low, bars.close, length=10)['SUPERTd_10_3.0']

    if percent_diff:

        for i in range(1, 10):
            bars[f'percent_diff_{i}'] = ta.slope(bars.close, length=i)

    return bars
