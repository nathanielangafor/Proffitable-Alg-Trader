import pandas as pd
from pandas import concat
import requests
import csv
import datetime
import time
import robin_stocks.robinhood as r
import numpy as np
import sys

# append the config file path to sys.path
sys.path.append('/Users/appleid/Desktop/Other Files/V3/Config Files')
import config

def price(asset, asset_type):
    """
    Get the current price of the asset.

    Returns:
    float: The current price of the asset.
    """
    while True:
        try:
            if asset_type == 'crypto':
                # get the list of assets from the API using the Session object
                assets = requests.get(config.crypto['price_url']).json()['assets']
                # find the asset with the desired symbol
                for item in assets:
                    if item['symbol'] == asset:
                        # return the price of the asset
                        return float(item['price'])

            if asset_type == 'stock':
                return float(r.stocks.get_latest_price(asset, includeExtendedHours=True)[0])
        except:
            # print an error message and try again in 3 seconds
            print('Price fetch error...')
            time.sleep(3)

def strToEpoch(timeInput):
    """
    Convert a time string in '%Y-%m-%d %H:%M:%S' format to epoch time.

    Parameters:
    timeInput (str): Time string in '%Y-%m-%d %H:%M:%S' format.

    Returns:
    int: Epoch time.
    """
    # convert the time string to a datetime object
    dt = datetime.datetime.strptime(timeInput, '%Y-%m-%d %H:%M:%S')
    # convert the datetime object to epoch time
    epoch_time = dt.timestamp()
    # return the epoch time
    return epoch_time  

def read_dataframe(filename):
    # Try to read the DataFrame
    try:
        df = pd.read_csv(filename)
        return df
    except:
        # If reading the DataFrame fails, try again
        print("Error reading DataFrame. Trying again...")
        return read_dataframe(filename)
        
def createLargerCandlesticks(df, output, timeframe):
    # Convert time column to datetime type
    df['datetime'] = pd.to_datetime(df['datetime'])
    # Group by Minute
    groups = df.groupby(pd.Grouper(key='datetime', freq=timeframe))
    # Calculate New Open
    new_open = groups['open'].first()
    # Calculate New Close
    new_close = groups['close'].last()
    # Calculate New High
    new_high = groups['high'].max()
    # Calculate New Low
    new_low = groups['low'].min()
    # Create DataFrame with new data 
    new_time = groups['datetime'].last().dt.strftime('%Y-%m-%d %H:%M:%S')
    new_df = pd.DataFrame(data={'datetime':new_time, 'open':new_open, 'close':new_close, 'high':new_high, 'low':new_low})
    df_cleaned = new_df.dropna()
    df_cleaned.to_csv(output, index=False)
    return new_df

def update(onStartup, asset, asset_type, asset_price):
    """
    Update the asset data stored in a CSV file.
    """
    columns = ['datetime', 'high', 'low', 'open', 'close']
    if onStartup:
        # get the asset data from the API
        data = requests.get(config.generate_historical_url(asset, asset_type))
        data = data.json()['values']
        # open the CSV file for writing
        with open(config.generate_file_name(asset), 'w') as f:
            # create a CSV writer
            writer = csv.writer(f)
            # write the columns to the CSV file
            writer.writerow(columns)
            # write the values to the CSV file
            for row in data:
                # convert the time value to a time string
                date_time = datetime.datetime.fromisoformat(row['datetime'])
                date_formatted = date_time.strftime('%Y-%m-%d %H:%M:%S')
                row['datetime'] = date_formatted
                # create a list of values for the specified columns
                values = [row[col] for col in columns]
                # write the values to the CSV file
                writer.writerow(values)
    
    asset_price = price(asset, asset_type)
    # Get the current time in Rochester, NY
    now = datetime.datetime.now()
    # Format the time as a string in the desired format
    time_str = now.strftime('%Y-%m-%d %H:%M:%S')
    row = {
        'datetime': time_str, 
        'high': asset_price, 
        'low': asset_price, 
        'open': asset_price, 
        'close': asset_price
    }
    with open(config.generate_file_name(asset), 'a') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writerow(row)
    df = read_dataframe(config.generate_file_name(asset))
    createLargerCandlesticks(df, config.generate_file_name(asset), config.ticker_frequency)

def calculateMACD(df):
    """
    Calculate the MACD for the given DataFrame.

    Args:
    df (pandas.DataFrame): The DataFrame to calculate the MACD for.

    Returns:
    dict: A dictionary containing the MACD, MACD signal, MACD histogram, MACD direction, 
          turn time, period since turn, cross count, and values.
    """
    # get the number of rows in the DataFrame
    num_rows = df.shape[0]
    # Calculate the MACD
    df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    # Calculate the MACD signal
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    # Calculate the MACD histogram
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # Initialize variables to track the MACD direction and turn time
    turned = ''
    final_dir = ''
    values = []
    # Iterate through the rows of the DataFrame
    for _, row in df.iterrows():
        # If the MACD is greater than or equal to the MACD signal
        if row['macd'] >= row['macd_signal']:
            # If the final direction is not positive
            if final_dir != 'long':
                # Reset the values and update the turned and final direction variables
                values = []
                turned = row['datetime']
                final_dir = 'long'
            else:
                # Append the MACD value to the values list
                values.append(row['macd'])
        # If the MACD is less than the MACD signal
        if row['macd'] < row['macd_signal']:
            # If the final direction is not negative
            if final_dir != 'short':
                # Reset the values and update the turned and final direction variables
                values = []
                turned = row['datetime']
                final_dir = 'short'
            else:
                # Append the MACD value to the values list
                values.append(row['macd'])

    # Initialize arrays for counting crosses
    arr1 = []
    arr2 = []
    # Iterate through the rows of the DataFrame in reverse
    for _, row in df.iloc[::-1].iterrows():
        # If the final MACD value is positive
        if (df['macd'][num_rows - 1] > 0):
            # If the MACD and MACD signal are both positive
            if (row['macd'] > 0 and row['macd_signal'] > 0):
                # Append the MACD and MACD signal values to the arrays
                arr1.append(row['macd'])
                arr2.append(row['macd_signal'])
            else:
                # Break the loop
                break
        # If the final MACD value is negative
        if (df['macd'][num_rows - 1] < 0):
            # If the MACD and MACD signal are both negative
            if (row['macd'] < 0 and row['macd_signal'] < 0):
                # Append the MACD and MACD signal values to the arrays
                arr1.append(row['macd'])
                arr2.append(row['macd_signal'])
            else:
                # Break the loop
                break

    # Initialize a list to track the number of crosses
    cross_count = []
    # Iterate through the crosstab of the arr1 and arr2 arrays
    for i in pd.crosstab(arr1, arr2): 
        # If the rounded value is not in the cross_count list and is greater than or equal to 5
        if round(i) not in cross_count and round(i) >= 5:
            # If there is at least one value in the cross_count list
            if len(cross_count) > 0:
                # If the rounded value is not equal to the previous value + 1 or - 1
                if round(i) + 1 != cross_count[-1] and round(i) - 1 != cross_count[-1]:
                    # Append the rounded value to the cross_count list
                    cross_count.append(round(i))
            # If there are no values in the cross_count list
            else:
                # Append the rounded value to the cross_count list
                cross_count.append(round(i))
    # Return the final MACD value, MACD signal, MACD histogram, direction of the MACD, time of the last turn, the period since the last turn, the number of crosses, and the values of the MACD
    return {
        'macd': df['macd'][num_rows - 1], 
        'macdSignal': df['macd_signal'][num_rows - 1], 
        'histogram': df['macd_hist'][num_rows - 1], 
        'macdDirection': final_dir, 
        'turnTime': turned, 
        'periodSinceTurn': strToEpoch(turned), 
        'crossCount': len(cross_count), 
        'values': values, 
        'df': df
    }

def calculateEMAandDEMA(df):
    """
    Calculate the Exponential Moving Average (EMA) and Double Exponential Moving Average (DEMA) for the given DataFrame.

    Args:
    df (pandas.DataFrame): The DataFrame to calculate the EMA and DEMA for.

    Returns:
    dict: A dictionary containing the EMA and DEMA values.
    """
    # get the number of rows in the DataFrame
    num_rows = df.shape[0]
    # Calculate the EMA for the closing price
    df['ema'] = df['open'].ewm(span=200).mean()
    # Calculate the DEMA for the closing price
    df['ema1'] = df['open'].ewm(span=200).mean()
    df['ema2'] = df['ema1'].ewm(span=200).mean()
    df['dema'] = 2 * df['ema1'] - df['ema2']
    return {
        'ema': float(df['ema'][num_rows - 1]), 
        'dema': float(df['dema'][num_rows - 1]), 
        'df': df
    }

def calculateTrend(df):
    """
    Calculate the personal values for the given DataFrame.

    Args:
    df (pandas.DataFrame): The DataFrame to calculate the personal values for.

    Returns:
    dict: A dictionary containing the personal values.
    """
    # Calculate the EMA for the closing price
    df['ema'] = df['open'].ewm(span=200).mean()
    greater_count = 0
    less_count = 0
    dft = 0
    for x in range(1, len(df)):
        dft = df.tail(x)
        greater_count = dft.loc[dft['close'] > dft['ema']].shape[0]
        less_count = dft.loc[dft['close'] < dft['ema']].shape[0]
        if greater_count > 0 and less_count > 0:
            if (abs(greater_count - less_count) / greater_count) * 100.0 >= 50 and x >= 200:
                break
    return {
        'dftLen': len(dft), 
        'greaterCount': greater_count, 
        'lessCount': less_count,
        'df': df
    }

def calculateCCI(df):
    """
    Calculate the Commodity Channel Index (CCI) for the given DataFrame.

    Args:
    df (pandas.DataFrame): The DataFrame to calculate the CCI for.

    Returns:
    dict: A dictionary containing the CCI value.
    """
    # get the number of rows in the DataFrame
    num_rows = df.shape[0]
    # calculate the simple moving average and CCI
    df['sma'] = df['close'].rolling(window=20).mean()
    df['cci'] = (df['close'] - df['sma']) / (0.015 * df['close'].rolling(window=20).apply(lambda x: np.std(x, ddof=1), raw=True))
    return {
        'cci': float(df['cci'][num_rows - 1]),
        'df': df
    }

def calculateATR(df):
    """
    Calculate the Average True Range (ATR) for the given DataFrame.

    Args:
    df (pandas.DataFrame): The DataFrame to calculate the ATR for.

    Returns:
    dict: A dictionary containing the ATR value.
    """
    # get the number of rows in the DataFrame
    num_rows = df.shape[0]
    # Calculate the true range of each row
    df['true_range'] = df[['high', 'low', 'close']].apply(lambda x: max(x) - min(x), axis=1)
    # Calculate the average true range using the specified window
    df['avg_true_range'] = df['true_range'].rolling(window=12).mean().iloc[-1]
    return {
        'atr': float(df['avg_true_range'][num_rows - 1]),
        'df': df
    }

def calculateICHIMOKU(df):
    """
    Calculate Ichimoku values for an asset.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    pandas.DataFrame: The input DataFrame with additional columns for the Ichimoku values.
    """
    # Calculate the nine-day and 26-day SMAs for the high and low prices
    df['sma_9_high'] = df['high'].rolling(9).mean()
    df['sma_9_low'] = df['low'].rolling(9).mean()
    df['sma_26_high'] = df['high'].rolling(26).mean()
    df['sma_26_low'] = df['low'].rolling(26).mean()
    df['sma_52_high'] = df['high'].rolling(52).mean()
    df['sma_52_low'] = df['low'].rolling(52).mean()
    # Calculate the conversion line (tenkan sen)
    df['conversion_line'] = (df['sma_9_high'] + df['sma_9_low']) / 2
    # Calculate the base line (kijun sen)
    df['base_line'] = (df['sma_26_high'] + df['sma_26_low']) / 2
    # Calculate leading span A (senkou span A)
    df['senkou_span_a'] = ((df['conversion_line'] + df['base_line']) / 2).shift(26)
    # Calculate leading span B (senkou span B)
    df['senkou_span_b'] = ((df['sma_52_high'] + df['sma_52_low']) / 2).shift(26)
    # Calculate lagging span (chikou span)
    df['lagging_span'] = df['close'].shift(-26)
    # get df size
    num_rows = df.shape[0]
    return {
        'current': {
            'senkou_span_b': df['senkou_span_b'][num_rows - 1], 
            'senkou_span_a': df['senkou_span_a'][num_rows - 1],
            'cloud_size': abs( df['senkou_span_a'][num_rows - 1] - df['senkou_span_b'][num_rows - 1])
        }, 
        'df': df
    }

def calculateRSI(df):
    """
    Calculate the relative strength index (RSI) and its simple moving average (SMA) for the given DataFrame.
    
    Args:
    df (pandas.DataFrame): The DataFrame to calculate the RSI and its SMA for.
    rsi_length (int): The length of the RSI calculation.
    ma_length (int): The length of the RSI SMA calculation.
    
    Returns:
    dict: A dictionary containing the RSI and RSI-based SMA.
    """
    rsi_length = 14
    ma_length = 14
    # Calculate the RSI
    df['up'] = df['close'].diff().clip(lower=0).rolling(window=rsi_length).mean()
    df['down'] = -df['close'].diff().clip(upper=0).rolling(window=rsi_length).mean()
    df['rsi'] = 100 - (100 / (1 + df['up'] / df['down']))
    df['rsi_ma'] = df['rsi'].rolling(window=ma_length).mean()
    return {
        'rsi': df['rsi'][df.shape[0] - 1],
        'rsi_ma': df['rsi_ma'][df.shape[0] - 1]
}

def calculateBollingerBands(df):
    """
    Calculate the Bollinger Bands for the given DataFrame.
    
    Args:
    df (pandas.DataFrame): The DataFrame to calculate the Bollinger Bands for.
    
    Returns:
    dict: A dictionary containing the Bollinger Bands.
    """
    length = 20
    mult = 2
    offset = 0
    # Calculate the Bollinger Bands
    df['basis'] = df['close'].rolling(window=length, min_periods=offset).mean()
    df['dev'] = df['close'].rolling(window=length, min_periods=offset).std()
    df['upper'] = df['basis'] + mult * df['dev']
    df['lower'] = df['basis'] - mult * df['dev']
    return {
        'basis': df['basis'][df.shape[0] - 1],
        'upper': df['upper'][df.shape[0] - 1],
        'lower': df['lower'][df.shape[0] - 1]
    }

def calculateFearAndGreed():
    """
    Get the current Fear and Greed index from the API.

    Returns:
    list: A list of dictionaries containing the Fear and Greed data.
    """
    while True:
        try:
            # get the Fear and Greed data from the API
            data = requests.get('https://api.alternative.me/fng/?limit=10').json()['data']
            # format the timestamp as a string
            for entry in data:
                date_time = datetime.datetime.fromtimestamp(int(entry['timestamp']))
                date_formatted = date_time.strftime('%Y-%m-%d %H:%M:%S')
                entry['timestamp'] = date_formatted
            return data
        except:
            # print the error message and try again in 3 seconds
            print('Fear + greed fetch error...')
            time.sleep(3)

def calculateADX(df):
    """
    Calculate the Average Directional Index (ADX) of a given asset.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    pandas.Series: Series containing the ADX values.
    """
    dilen=14 
    adxlen=14
    # get the number of rows in the DataFrame
    num_rows = df.shape[0]
    # calculate plus and minus directional indices
    df['up'] = df['high'].diff()
    df['down'] = df['low'].diff()
    df['plusDM'] = np.where((df['up'] > df['down']) & (df['up'] > 0), df['up'], 0)
    df['minusDM'] = np.where((df['down'] > df['up']) & (df['down'] > 0), df['down'], 0)
    df['truerange'] = df[['high', 'low', 'close']].apply(lambda x: x.max() - x.min(), axis=1)
    df['plus'] = 100 * df['plusDM'].rolling(dilen).mean() / df['truerange'].rolling(dilen).mean()
    df['minus'] = 100 * df['minusDM'].rolling(dilen).mean() / df['truerange'].rolling(dilen).mean()
    # calculate ADX
    df['sum'] = df['plus'] + df['minus']
    df['adx'] = 100 * np.abs(df['plus'] - df['minus']).rolling(adxlen).mean() / df['sum'].apply(lambda x: 1 if x == 0 else x).rolling(adxlen).mean()
    return df['adx'][num_rows - 1]

def calculateMomentum(df):
    """
    Calculate momentum for an asset.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'mom' and 'df' containing the calculated momentum 
          and the input DataFrame with an additional 'mom' column, respectively.
    """
    # get the number of rows in the DataFrame
    num_rows = df.shape[0]
    # Calculate the momentum as the difference between the current close price and the close price 10 days ago
    df['mom'] = df['close'].shift(10) - df['close']
    # return the calculated momentum and the modified DataFrame
    return {
        'mom': df['mom'][num_rows - 1],
        'df': df
    }

def calculateVortex(df):
    """
    Calculate the Vortex Indicator (VI) for the given DataFrame.

    Args:
    df (pandas.DataFrame): The DataFrame to calculate the VI for.

    Returns:
    dict: A dictionary containing the VI values and the modified DataFrame.
    """
    num_rows = df.shape[0]
    # Calculate the vortex indicator values
    df['VMP'] = df['high'].sub(df['low'].shift(1)).abs().rolling(7).sum()
    df['VMM'] = df['low'].sub(df['high'].shift(1)).abs().rolling(7).sum()
    df['STR'] = df['high'].sub(df['low']).abs().add(df['close'].sub(df['high'].shift(1)).abs(), fill_value=0).add(df['close'].sub(df['low'].shift(1)).abs(), fill_value=0).rolling(7).mean()
    df['VIP'] = df['VMP'].div(df['STR'])
    df['VIM'] = df['VMM'].div(df['STR'])
    # Return the VI values and the modified DataFrame
    return {
        'VIP': df['VIP'][num_rows - 1],
        'VIM': df['VIM'][num_rows - 1],
        'df': df
    }