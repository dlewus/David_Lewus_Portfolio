'''
Functions to backtest trading signals
'''

from tqdm.notebook import tqdm_notebook
from datetime import timedelta


def predicted_return(
        df,
        start,
        tp,
        sl,
        trade_risk,
        buy_target,
        sell_target,
        hold_target,
        N=0,
        fee=0.04,
        leverage=20,
        balance=10000,
        print_balance=False,
        print_order=False,
        print_summary=True):
    '''
    Determines final balance and win % from predicted labels

    returns dictionary containing
       balance - float of final balance
       moves - int of number of moves taken
       win_percent - float of percentage of moves that were wins (i.e. balance increases)
       sl_count - int of number of times stop loss was triggered
       tp_count - int of number of times take profit was triggered
       signal_exit_count - int of number of time signal was exited using predicted labels
       sl - float of stop loss passed to function
       tp - float of take profit passed to function
       trade_risk - float of trade risk passed to function
       start - datetime object of start time passed to function

    df - DataFrame with timeseries index, candlestick data, and predicted labels
    start - datetime object of start time
    tp - float of take profit multiplier
    sl - float of stop loss multiplier
    trade_risk - float of trade risk multiplier
    buy_target - int of uptrend label
    sell_target - int of downtrend label
    hold_target - int of no trend label
    N - int of sequence lookback
    fee - float of trading platform fee
    leverage - float of leverage multiplier
    balance - float of starting balance
    print_balance - bool, if True balance will print for each trade
    print_order - bool, if True order time and price will print for each trade
    print_summary - bool, if True a summary of the trading period will print at end
    '''

    prev_price = df.close.loc[start]
    prev_timestamp = start
    prev_target = df.target.loc[start]

    total = 0
    signal_total = 0
    win_count = 0
    tp_count = 0
    sl_count = 0
    signal_exit_count = 0
    time_total = timedelta(minutes=0)

    if print_summary:
        print()
        print(f'TP: {tp*100:.00f}%')
        print(prev_timestamp)

    for i in df[df.action == True].loc[start:].iterrows():
        target = i[1].target

        first_sl = df.index[-1]
        first_tp = df.index[-1]
        timestamp = i[0]

        # skip first
        if timestamp == prev_timestamp:
            continue

        # add an amount of time equal to sequence lookback period
        try:
            price = df.close.loc[timestamp + timedelta(minutes=N)]
        except KeyError:
            continue

        # Only execute if prev_target was a sell or buy, not hold
        if prev_target != hold_target:

            # Don't trade more than trade_risk
            trade_value = (balance * trade_risk)
            balance *= (1 - trade_risk)

            # Look at all closing prices between last move and current move
            trade_window = df.loc[prev_timestamp:timestamp]
            trade_window = trade_window[1:]

            # If at any time the price was lower than the stop loss
            # or higher than take profit, exit trade
            if prev_target == buy_target:
                sl_check = trade_window.low < ((1 - (sl / leverage)) * prev_price)
                tp_check = trade_window.high > ((1 + (tp / leverage)) * prev_price)

            elif prev_target == sell_target:
                sl_check = trade_window.high > ((1 + (sl / leverage)) * prev_price)
                tp_check = trade_window.low < ((1 - (tp / leverage)) * prev_price)

            # Check if there are any stop loss or take profit bars
            if sl_check.any():
                first_sl = sl_check.index[sl_check == True][0]

            if tp_check.any():
                first_tp = tp_check.index[tp_check == True][0]

            # If take profit happens before stop loss, apply take profit
            if first_tp < first_sl:
                total += (tp - fee)
                trade_value *= (1 + (tp - fee))
                balance += trade_value
                tp_count += 1
                time_total += first_tp - prev_timestamp
                win_count += 1

            # If stop loss happens before take profit, apply stop loss
            elif first_sl < first_tp:
                total -= (sl + fee)
                trade_value *= (1 - (sl + fee))
                balance += trade_value
                sl_count += 1
                time_total += first_sl - prev_timestamp
                if print_order:
                    print('ORDER STOPPED')

            # If stop loss and take profit never happen, trade the move
            elif not sl_check.any() and not tp_check.any():
                if prev_target == buy_target:
                    move = ((price - prev_price) / prev_price) * leverage
                elif prev_target == sell_target:
                    move = ((prev_price - price) / prev_price) * leverage

                total += (move - fee)
                signal_total += (move - fee)
                trade_value *= (1 + (move - fee))
                balance += trade_value

                signal_exit_count += 1

                time_total += timestamp - prev_timestamp

                if (move - fee) > 0:
                    win_count += 1

            # This only happens if stop loss and take profit are in same bar
            else:
                total += (tp - fee)
                trade_value *= (1 + (tp - fee))
                balance += trade_value
                tp_count += 1
                win_count += 1
                time_total += first_tp - prev_timestamp
            if print_order:
                print(f'ORDER CLOSED: {timestamp} {price}')

        if print_order and target != hold_target:
            print(f'ORDER OPEN:{timestamp} {price} {target}')

        # Get ready for next iteration
        prev_timestamp = timestamp
        prev_price = price
        prev_target = target

    # Print info to track individual moves
        if print_balance:
            print(round(balance, 2), timestamp, target)
    total_moves = sl_count + tp_count + signal_exit_count
    if total_moves == 0:
        total_moves = 1
    # Print summary info
    if print_summary:
        print(f'Balance        : ${balance:.03f}')
        print(f'Percent profit : {total*100:.03f}%')
        print(f'Number of moves: {sl_count + tp_count + signal_exit_count}')
        print(f'Average time: {time_total/(total_moves)}')
        print(f'Win %          : {round(win_count/(total_moves)*100,2)}%')
        print(f'Stop loss      : {sl_count}')
        print(f'Take profit    : {tp_count}')
        print(f'Signal exit    : {signal_exit_count}')
        if signal_exit_count > 0:
            print(f'Signal average : {signal_total*100/signal_exit_count:.03f}%')

        # Return dictionary with input information and resulting balance
    return_dict = {'balance': round(balance, 2),
                   'moves': sl_count + tp_count + signal_exit_count,
                   'win_percent': round(win_count / (total_moves) * 100, 2),
                   'sl_count': sl_count,
                   'tp_count': tp_count,
                   'signal_exit_count': signal_exit_count,
                   'sl': sl,
                   'tp': tp,
                   'trade_risk': trade_risk,
                   'start': start}

    return return_dict


def bestRisk(
        df,
        start,
        fee,
        leverage,
        buy_target,
        sell_target,
        hold_target,
        N=0,
        progress_bar=True,
        sl_range=range(1, 11),
        sl_range_divider=10,
        trade_risk_range=range(1, 11),
        trade_risk_range_divider=10,
        tp_range=range(1, 11),
        tp_range_divider=10):
    '''
    Determines best risk parameters to use with predicted_return()

    returns dictionary of highest balance found, same parameters as predicted_return()

    df - DataFrame with timeseries index, candlestick data, and predicted labels
    start - datetime object of start time
    fee - float of trading platform fee
    leverage - float of leverage multiplier
    buy_target - int of uptrend label
    sell_target - int of downtrend label
    hold_target - int of no trend label
    N - int of sequence lookback
    progress_bar - bool, if True tqdm progress bar will display in notebook
    sl_range - iter of stop losses to check
    sl_range_divider - float of divider to use on sl_range
    trade_risk_range - iter of trade risks to check
    trade_risk_range_divider - float of divider to use on trade_risk_range
    tp_range - iter of take profits to check
    tp_range_divider - float of divider to use on tp_range
    '''

    df = df.copy()
    balances = {}
    if progress_bar:
        for tp in tqdm_notebook(tp_range):
            tp /= tp_range_divider
            for sl in sl_range:
                sl /= sl_range_divider
                for trade_risk in trade_risk_range:
                    trade_risk /= trade_risk_range_divider
                    return_dict = predicted_return(
                        df=df,
                        start=start,
                        tp=tp,
                        sl=sl,
                        trade_risk=trade_risk,
                        N=N,
                        buy_target=buy_target,
                        sell_target=sell_target,
                        hold_target=hold_target,
                        leverage=leverage,
                        fee=fee,
                        print_summary=False)
                    balances[return_dict['balance']] = return_dict
    else:
        for tp in tp_range:
            tp /= tp_range_divider
            for sl in sl_range:
                sl /= sl_range_divider
                for trade_risk in trade_risk_range:
                    trade_risk /= trade_risk_range_divider
                    return_dict = predicted_return(
                        df=df,
                        start=start,
                        tp=tp,
                        sl=sl,
                        trade_risk=trade_risk,
                        N=N,
                        buy_target=buy_target,
                        sell_target=sell_target,
                        hold_target=hold_target,
                        leverage=leverage,
                        fee=fee,
                        print_summary=False)
                    balances[return_dict['balance']] = return_dict
    return balances[max(balances.keys())]
