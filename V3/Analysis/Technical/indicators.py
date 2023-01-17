import pandas as pd
import cloudscraper
import csv
import datetime
import time
import numpy as np
import sys
import json

# append the config file path to sys.path
sys.path.append('Config Files')
import config

scraper = cloudscraper.create_scraper()

def price(asset, asset_type):
    """
    Get the current price of the asset.

    Parameters:
    asset (str): The name of the asset.
    asset_type (str): The type of the asset (e.g. stock, crypto).

    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        for x in range(5):
            try:
                # Get price for leveraged crypto asset
                if asset_type == 'crypto' and asset in config.leveragable_crypto:
                    # Get the list of assets from the API
                    assets = scraper.get(config.crypto['price_url']).json()['assets']
                    # Find the asset with the desired symbol
                    for item in assets:
                        if item['symbol'] == asset:
                            price = float(item['price'])
                # Get price for normal crypto asset
                if asset_type == 'crypto' and asset in config.non_leveragable_crypto:
                    coins = scraper.get('https://api.coinlore.net/api/tickers/?limit=10000').json()['data']
                    for coin in coins:
                        if coin['symbol'] == asset:
                            markets = scraper.get('https://api.coinlore.net/api/coin/markets/?id=' + coin['id']).json()
                            for market in markets:
                                if market['name'] == 'Binance' and market['quote'] == 'USDT':
                                    price = float(market['price'])
                # Get price for stock asset
                if asset_type == 'stock':
                    price = float(scraper.get(f'https://api.wsj.net/api/dylan/quotes/v2/comp/quoteByDialect?dialect=official&needed=CompositeTrading|BluegrassChannels&MaxInstrumentMatches=1&accept=application/json&EntitlementToken=cecc4267a0194af89ca343805a3e57af&ckey=cecc4267a0&dialects=Charting&id=Stock-US-{asset}%2CStock-US-LIVE%2CStock-US-ADIL%2CCryptoCurrency-US-BTCUSD%2CStock-US-KALA').json()['InstrumentResponses'][0]['Matches'][0]['CompositeTrading']['Last']['Price']['Value'])
                return {
                    'data': price,
                    'msg': 'success'
                }
            except:
                time.sleep(3)
        raise TimeoutError(f'Failed to fetch price for {asset}')
    except Exception as e:
        error = {
            'data': {
                'file': 'indicators.py',
                'function': 'price',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error
        
def db_price(asset):
    """
    Get the current price of the asset.

    Parameters:
    asset (str): The name of the asset.
    asset_type (str): The type of the asset (e.g. stock, crypto).

    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    while True:
        try:
            return float(config.get_asset_price(asset)[0]['asset_price'])
        except:
            time.sleep(3)
            pass

def createLargerCandlesticks(df, output, timeframe):
    # convert timeframe to correct format
    timeframe = config.timeframe_converter[timeframe]
    # Convert time column to datetime type
    df['datetime'] = pd.to_datetime(df['datetime'])
    # Group by desired timeframe
    groups = df.groupby(pd.Grouper(key='datetime', freq=timeframe))
    # Calculate new open, close, high, and low
    new_open = groups['open'].first()
    new_close = groups['close'].last()
    new_high = groups['high'].max()
    new_low = groups['low'].min()
    # Create new dataframe with new data
    new_df = pd.DataFrame({'open':new_open, 'close':new_close, 'high':new_high, 'low':new_low})
    new_df = new_df.reset_index()
    new_df["datetime"] = new_df["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')
    new_df = new_df.dropna()
    new_df.to_csv(output, index=False)
    return new_df

def update(initialized_asset, asset, asset_type, asset_price, timeframe):
    """
    Update the asset data stored in a CSV file.
    
    Parameters:
    initialized_asset (str): Indicate if an asset is being initialized for the first time.
    asset (str): The asset being tracked.
    asset_type (str): The type of the asset (e.g. 'currency', 'commodity', 'stock').
    asset_price (float): The current price of the asset.
    timeframe (str): The time frame for the data (e.g. '1d', '1h').
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        file_name = config.generate_file_name(asset, timeframe)['data']
        columns = ['datetime', 'high', 'low', 'open', 'close']
        if initialized_asset == 'false':
            while True:
                try:
                    # Get the asset data from the API
                    data = scraper.get(config.generate_historical_url(asset, asset_type, timeframe)['data'])
                    data = data.json()['values']
                    break
                except:
                    time.sleep(30)
            # Open the CSV file for writing
            with open(file_name, 'w') as f:
                # Create a CSV writer
                writer = csv.writer(f)
                # Write the columns to the CSV file
                writer.writerow(columns)
                # Write the values to the CSV file
                for row in reversed(data):
                    # Convert the time value to a time string
                    date_time = datetime.datetime.fromisoformat(row['datetime'])
                    date_formatted = date_time.strftime('%Y-%m-%d %H:%M:%S')
                    row['datetime'] = date_formatted
                    # Create a list of values for the specified columns
                    values = [row[col] for col in columns]
                    # Write the values to the CSV file
                    writer.writerow(values)
        # Get the current time in Rochester, NY
        now = datetime.datetime.now()
        # Format the time as a string in the desired format
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        # Create a row of data for the current asset price
        row = {
            'datetime': time_str, 
            'high': asset_price, 
            'low': asset_price, 
            'open': asset_price, 
            'close': asset_price
        }
        # Open the CSV file for appending
        with open(file_name, 'a') as f:
            # Create a CSV writer for dictionaries
            writer = csv.DictWriter(f, fieldnames=columns)
            # Write the row to the CSV file
            writer.writerow(row)
        # Read the CSV file into a Pandas dataframe
        df = config.read_dataframe(file_name)['data']
        # Check if all the columns exist
        if all(col in df.columns for col in row.keys()):
            # Create larger candlesticks from the dataframe
            createLargerCandlesticks(df, file_name, timeframe)
        else:
            raise AttributeError(f'The CSV file for {asset} on timeframe {timeframe} does not have all its columns')
        return {
            'data': f'The CSV file for {asset} on timeframe {timeframe} has been updated.',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'indicators.py',
                'function': 'update',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error
    

def calculate_macd(df):
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
    # Return the final MACD value, MACD signal, MACD histogram, direction of the MACD, time of the last turn, the period since the last turn, the number of crosses, and the values of the MACD
    return {
        'macd': df['macd'][num_rows - 1], 
        'macdSignal': df['macd_signal'][num_rows - 1], 
        'histogram': df['macd_hist'][num_rows - 1], 
        'macdDirection': final_dir, 
        'turnTime': turned, 
        'periodSinceTurn': config.string_to_epoch(turned), 
        'values': values, 
        'df': df
    }

def calculate_ema_dema(df):
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

def calculate_trend(df):
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

def calculate_cci(df):
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

def calculate_atr(df):
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

def calculate_ichimoku(df):
    nine_period_high = df['high'].rolling(window= 9).max()
    nine_period_low = df['low'].rolling(window= 9).min()
    df['tenkan_sen'] = (nine_period_high + nine_period_low) /2
    # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
    period26_high = df['high'].rolling(window=26).max()
    period26_low = df['low'].rolling(window=26).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2
    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2))
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
    period52_high = df['high'].rolling(window=52).max()
    period52_low = df['low'].rolling(window=52).min()
    df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)
    # The most current closing price plotted 26 time periods behind (optional)
    df['chikou_span'] = df['close'].shift(-26)
    num_rows = df.shape[0]
    data = {
        'current': {
            'senkou_span_a': df['senkou_span_a'][num_rows - 1], 
            'senkou_span_b': df['senkou_span_b'][num_rows - 1],
            'cloud_size': abs(df['senkou_span_a'][num_rows - 1] - df['senkou_span_b'][num_rows - 1]),
        }
    }

    return data

def calculate_rsi(df):
    """
    Calculate the relative strength index (RSI) and its simple moving average (SMA) for the given DataFrame.
    
    Args:
    df (pandas.DataFrame): The DataFrame to calculate the RSI and its SMA for.
    rsi_length (int): The length of the RSI calculation.
    ma_length (int): The length of the RSI SMA calculation.
    
    Returns:
    dict: A dictionary containing the RSI and RSI-based SMA.
    """
    # Set vars
    rsi_length = 14
    source_column = 'close' 
    ma_length = 14
    # Calculate the RSI
    df['change'] = df[source_column].diff()
    df['gain'] = df['change'].mask(df['change'] < 0, 0)
    df['loss'] = df['change'].mask(df['change'] > 0, 0).abs()
    df['avg_gain'] = df['gain'].rolling(window=rsi_length).mean()
    df['avg_loss'] = df['loss'].rolling(window=rsi_length).mean()
    df['rs'] = df['avg_gain'] / df['avg_loss']
    df['rsi'] = 100 - (100 / (1 + df['rs']))
    # Calculate the SMA for the RSI
    df['rsi_ma'] = df['rsi'].rolling(window=ma_length).mean()
    return {
        'rsi': df['rsi'][df.shape[0] - 1],
    }

def calculate_bollinger_bands(df):
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

def calculate_fear_and_greed(asset_type):
    """
    Get the current Fear and Greed index from the API.

    Returns:
    list: A list of dictionaries containing the Fear and Greed data.
    """
    while True:
        try:
            if asset_type == 'crypto':
                # get the Fear and Greed data from the API
                data = scraper.get('https://api.alternative.me/fng/?limit=1').json()['data'][0]
            else:
                now = datetime.datetime.now()
                # Get the current date as a datetime.date object
                today = now.date()
                # Format the date as YYYY-MM-DD
                date_string = today.strftime("%Y-%m-%d")
                data = scraper.get(f'https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{date_string}').json()['fear_and_greed']
            return {
                'data': data,
                'msg': 'success'
            }
        except Exception as e:
            error = {
                'data': {
                    'file': 'indicators.py',
                    'function': 'calculate_fear_and_greed',
                    'raise_exception': str(e)
                },
                'msg': 'error'
            }
            config.log_error(json.dumps(error))
            return error

def calculate_adx(df):
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

def calculate_momentum(df):
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

def calculate_vortex(df):
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