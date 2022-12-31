import indicators
import datetime
import requests
import cloudscraper

# append path to sys.path to allow import from this directory
import sys
sys.path.append('../Config Files')
import config

scraper = cloudscraper.create_scraper()

def ema_gate(df, asset_price, data):
    """
    Check if conditions for long or short trade based on EMA and DEMA are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # Check if atr should be included
    if data['long_criteria']:
        # get current asset price and ATR
        longATR = indicators.calculateATR(df)['atr']
    else:
        longATR = 0
    # Check if atr should be included
    if data['short_criteria']:
        # get current asset price and ATR
        shortATR = indicators.calculateATR(df)['atr']
    else:
        shortATR = 0
    # calculate EMA and DEMA
    assetEMA = indicators.calculateEMAandDEMA(df)
    # assume that conditions for long and short trades are not met
    emaLong = False
    emaShort = False
    # check if conditions for long trade are met
    if asset_price > assetEMA['ema'] + longATR:
        emaLong = True
    # check if conditions for short trade are met
    if asset_price < assetEMA['ema'] - shortATR:
        emaShort = True
    df['EMA Long'] = emaLong
    df['EMA Short'] = emaShort
    # return results as a dictionary
    return {
        'long': emaLong, 
        'short': emaShort, 
        'data': {
            'ema': assetEMA['ema'],
            'dema': assetEMA['dema'],
            'longATR': longATR,
            'shortATR': shortATR
        }
    }


def ichimoku_gate(df, asset_price, data=None):
    """
    Check if conditions for long or short trade based on Ichimoku Cloud are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # calculate Ichimoku Cloud values
    assetICHIMOKU = indicators.calculateICHIMOKU(df)
    # assume that conditions for long and short trades are not met
    ichimokuLong = False
    ichimokuShort = False
    # check if conditions for long trade are met
    if asset_price > assetICHIMOKU['current']['senkou_span_a'] and asset_price > assetICHIMOKU['current']['senkou_span_b']:
        ichimokuLong = True
    # check if conditions for short trade are met
    if asset_price < assetICHIMOKU['current']['senkou_span_a'] and asset_price < assetICHIMOKU['current']['senkou_span_b']:
        ichimokuShort = True
    df['ICHIMOKU Long'] = ichimokuLong
    df['ICHIMOKU Short'] = ichimokuShort
    # return results as a dictionary
    return {
        'long': ichimokuLong, 
        'short': ichimokuShort,
        'data': {
            'current': {
                'senkou_span_a': assetICHIMOKU['current']['senkou_span_a'],
                'senkou_span_b': assetICHIMOKU['current']['senkou_span_b']
            }
        }
    }


def cci_gate(df, data):
    """
    Check if conditions for long or short trade based on CCI are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # calculate CCI
    assetCCI = indicators.calculateCCI(df)
    # assume that conditions for long and short trades are not met
    cciShort = False
    cciLong = False
    # check if conditions for long and short trades are met
    if assetCCI['cci'] < data['short_criteria']:
        cciShort = True
    if assetCCI['cci'] > data['long_criteria']:
        cciLong = True
    df['CCI Long'] = cciLong
    df['CCI Short'] = cciShort
    # return results as a dictionary
    return {
        'long': cciLong, 
        'short': cciShort,
        'data': {
            'cci': assetCCI['cci']
        }
    }

def rsi_gate(df, data):
    """
    Check if conditions for long or short trade based on RSI are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # calculate RSI
    assetRSI = indicators.calculateRSI(df)
    # assume that conditions for long and short trades are not met
    rsiLong = False
    rsiShort = False
    # check if conditions for long trade are met
    if assetRSI['rsi'] > data['long_criteria']:
        rsiLong = True
    # check if conditions for short trade are met
    if assetRSI['rsi'] < data['short_criteria']:
        rsiShort = True
    df['RSI Long'] = rsiLong
    df['RSI Short'] = rsiShort
    # return results as a dictionary
    return {
        'long': rsiLong, 
        'short': rsiShort,
        'data': {
            'rsi': assetRSI['rsi']
        }
    }


def trend_gate(df, data):
    """
    Check if conditions for long or short trade based on custom criteria are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # calculate custom criteria
    assetTrend = indicators.calculateTrend(df)
    # assume that conditions for long and short trades are not met
    trendLong = False
    trendShort = False
    # check if conditions for long trade are met
    if assetTrend['greaterCount'] * data['long_criteria'] / 10 >= assetTrend['lessCount']:
        trendLong = True
    # check if conditions for short trade are met
    if assetTrend['lessCount'] * data['short_criteria'] / 10 >= assetTrend['greaterCount']:
        trendShort = True
    df['TREND Long'] = trendLong
    df['TREND Short'] = trendShort
    # return results as a dictionary
    return {
        'long': trendLong, 
        'short': trendShort,
        'data': {
            'greaterCount': assetTrend['greaterCount'],
            'lessCount': assetTrend['lessCount']
        }
    }

def fear_and_greed_gate(asset_type):
    """
    Check market sentiment based on "fear and greed" index.

    Returns:
    dict: A dictionary containing information about the current market 
          classification based on the "fear and greed" index, the current 
          value of the index, the change in the index over the past 24 hours, 
          and the direction of the change over the past 24 hours.
    """
    if asset_type == 'crypto':
        # retrieve current and previous "fear and greed" index values
        fear_and_greed = indicators.calculateFearAndGreed()
        current_value = float(fear_and_greed[0]['value'])
        previous_value = float(fear_and_greed[1]['value'])
        # calculate 24h change in index value
        market_change = abs(current_value - previous_value)
        # determine direction of change
        if current_value > previous_value:
            market_change_direction = 'up'
        if current_value < previous_value:
            market_change_direction = 'down'
        if current_value == previous_value:
            market_change_direction = 'none'
        # return results as a dictionary
        return {
            'fearAndGreedData': {
                'marketClassificationString': fear_and_greed[0]['value_classification'],
                'marketClassification': current_value,
                '24hMarketChange': market_change,
                '24hMarketChangeDirection': market_change_direction
            }
        }
    else:
        now = datetime.datetime.now()
        # Get the current date as a datetime.date object
        today = now.date()
        # Format the date as YYYY-MM-DD
        date_string = today.strftime("%Y-%m-%d")
        return {
            'fearAndGreedData': scraper.get(f'https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{date_string}').json()['fear_and_greed']
        }

def direction_gate(df):
    """
    Determine the direction to trade based on MACD direction.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with key 'attempting' and value indicating the trade direction.
    """
    # calculate MACD
    assetMACD = indicators.calculateMACD(df)
    # determine the trade direction
    attempting = None
    if assetMACD['macdDirection'] == 'long':
        attempting = 'long'
    if assetMACD['macdDirection'] == 'short':
        attempting = 'short'
    df['attempting'] = attempting
    # return the trade direction
    return {'attempting': attempting}

def momentum_gate(df, data=None):
    """
    Check if conditions for long or short trades based on momentum are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # calculate momentum for the asset
    assetMomentum = indicators.calculateMomentum(df)
    avgMomentum = df['mom'].tail(200).abs().mean()

    # assume that conditions for long and short trades are not met
    momLong = False
    momShort = False
    # check if conditions for long and short trades are met
    if abs(assetMomentum['mom']) > avgMomentum:
        momLong = True
        momShort = True
    df['MOM Long'] = momLong
    df['MOM Short'] = momShort
    # return results as a dictionary
    return {
        'long': momLong,
        'short': momShort,
        'data': {
            'assetMomentum': abs(assetMomentum['mom'])
        }
    }

def macd_gate(df, data=None):
    """
    Check if conditions for long or short trade based on MACD are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # calculate MACD
    assetMACD = indicators.calculateMACD(df)
    avgMACD = df['macd'].tail(200).abs().mean()
    avgHist = df['macd_hist'].tail(200).abs().mean()
    # assume that conditions for long and short trades are not met
    macdLong = False
    macdShort = False
    # check if conditions for long trade are met
    if assetMACD['histogram'] > 0 and abs(assetMACD['histogram']) > avgHist and abs(assetMACD['macd']) >= avgMACD:
        macdLong = True
    # check if conditions for short trade are met
    if assetMACD['histogram'] < 0 and abs(assetMACD['histogram']) > avgHist and abs(assetMACD['macd']) >= avgMACD:
        macdShort = True
    # # check if the MACD values are at a local extrema
    # if (len(assetMACD['values']) > 0):
    #     if max(assetMACD['values']) != assetMACD['values'][-1]:
    #         macdLong = False
    #     if min(assetMACD['values']) != assetMACD['values'][-1]:
    #         macdShort = False
    df['AVG MACD'] = avgMACD
    df['AVG HIST'] = avgHist
    df['MACD Long'] = macdLong
    df['MACD Short'] = macdShort
    # return results as a dictionary
    return {
        'long': macdLong, 
        'short': macdShort,
        'data': {
            'macd': assetMACD['macd'],
            'histogram': assetMACD['histogram'],
            'avgMACD': avgMACD,
            'avgHist': avgHist,
        }
    }

def tradeSize_gate(side):
    """
    Determine the trade size based on market conditions and trade direction.

    Parameters:
    side (str): Trade direction, either 'long' for long or 'short' for short.

    Returns:
    int: The trade size.
    """
    # get the base trade size from config
    tradeSize = config.tradeSizes
    # check if conditions for increasing trade size are met
    if fear_and_greed_gate()['24hMarketChange'] >= 4 and fear_and_greed_gate()['24hMarketChangeDirection'] == 'long' and side == 'short':
        tradeSize *= 2
    if fear_and_greed_gate()['24hMarketChange'] >= 4 and fear_and_greed_gate()['24hMarketChangeDirection'] == 'short' and side == 'long':
        tradeSize *= 2
    # return the trade size
    return tradeSize

def extreme_gate(df, data=None):
    """
    Check if conditions for long or short trades based on recent extremum are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # get the most recent 30 days of data
    period = df.tail(30)
    # get the index of the minimum close price in the period
    minIndex = period['close'].idxmin()
    # get the index of the maximum close price in the period
    maxIndex = period['close'].idxmax()
    # get the most recent data point
    mostRecent = df.iloc[-1]

    # assume that conditions for long and short trades are not met
    extremeLong = False
    extremeShort = False
    # check if the most recent data point is a new low
    if minIndex == mostRecent.name:
        extremeShort = True
    # check if the most recent data point is a new high
    if maxIndex == mostRecent.name:
        extremeLong = True
    df['EXTREME Long'] = extremeLong
    df['EXTREME Short'] = extremeShort
    # return results as a dictionary
    return {
        'long': extremeLong,
        'short': extremeShort,
        'data': {
            'minIndex': minIndex,
            'maxIndex': maxIndex,
            'currentIndex': mostRecent.name
        }
    }

def adx_gate(df, data=None):
    """
    Check if conditions for long or short trades based on ADX are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # calculate ADX for the asset
    adx = indicators.calculateADX(df)
    # assume that conditions for long and short trades are not met
    adxLong = False
    adxShort = False
    # check if conditions for long and short trades are met
    if adx >= 25:
        adxLong = True
        adxShort = True
    df['ADX Long'] = adxLong
    df['ADX Short'] = adxShort
    # return results as a dictionary
    return {
        'long': adxLong, 
        'short': adxShort,
        'data': {
            'adx': adx
        }
    }

def bollinger_gate(df, asset_price, data=None):
    """
    Check if conditions for long or short trades based on Bollinger Bands are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.
    asset_price (float): Current price of the asset.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # calculate Bollinger Bands for the asset
    assetBollinger = indicators.calculateBollingerBands(df)
    # assume that conditions for long and short trades are not met
    bollingerLong = False
    bollingerShort = False
    # check if conditions for long and short trades are met
    if asset_price > assetBollinger['lower'] and asset_price > assetBollinger['upper']:
        bollingerLong = True
    if asset_price < assetBollinger['lower'] and asset_price < assetBollinger['upper']:
        bollingerShort = True    
    df['BOLLINGER Long'] = bollingerLong
    df['BOLLINGER Short'] = bollingerShort
    # return results as a dictionary
    return {
        'long': bollingerLong, 
        'short': bollingerShort,
        'data': {
            'lower': assetBollinger['lower'],
            'upper': assetBollinger['upper']
        }
    }

def vortex_gate(df, data=None):
    assetVortex = indicators.calculateVortex(df)
    # assume that conditions for long and short trades are not met
    vortexLong = False
    vortexShort = False
    if assetVortex['VIP'] > assetVortex['VIM']:
        vortexLong = True
    if assetVortex['VIP'] < assetVortex['VIM']:
        vortexShort = True
    df['VORTEX Long'] = vortexLong
    df['VORTEX Short'] = vortexShort
    # return results as a dictionary
    return {
        'long': vortexLong, 
        'short': vortexShort,
        'data': {
            'VIP': assetVortex['VIP'],
            'VIM': assetVortex['VIM']
        }
    }

def cloud_gate(df, asset_price, data):
    """
    Check if conditions for long or short trade based on Ichimoku Cloud size are met.

    Parameters:
    df (pandas.DataFrame): DataFrame containing asset data.
    asset_price (float): The current price of the asset.

    Returns:
    dict: A dictionary with keys 'long' and 'short' and values indicating 
          whether conditions for long and short trades, respectively, are met.
    """
    # Calculate Ichimoku Cloud values
    assetICHIMOKU = indicators.calculateICHIMOKU(df)
    # Assume that conditions for long and short trades are not met
    cloudLong = False
    cloudShort = False
    # Check if conditions for long trade are met
    if assetICHIMOKU['current']['cloud_size'] > (data['long_criteria'] * asset_price) / 100.0:
        cloudLong = True
    if assetICHIMOKU['current']['cloud_size'] > (data['short_criteria'] * asset_price) / 100.0:
        cloudShort = True
    df['CLOUD Long'] = cloudLong
    df['CLOUD Short'] = cloudShort
    # Return the results as a dictionary
    return {
        'long': cloudLong, 
        'short': cloudShort,
        'data': {
            'cloud_size': {
                'current': assetICHIMOKU['current']['cloud_size']
            }
        }
    }
