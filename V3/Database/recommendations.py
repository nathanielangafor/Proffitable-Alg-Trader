import cloudscraper
import sys
import requests
import pandas as pd
import cloudscraper
import json

# Append the 'Analysis/Technical' folder to path and import the needed module
sys.path.append('Analysis/Technical')
import indicators
# append the config file path to sys.path
sys.path.append('Config Files')
import config

# Create scraper
scraper = cloudscraper.create_scraper()

def get_stocks(min_volume, min_price, min_sector_average, marketcap_min, marketcap_max):
    """
    This function uses the Nasdaq API to get a list of stocks that meet certain criteria.
    The criteria are as follows:
    1. The stock's volume must be greater than the provided min_volume
    2. The stock's last sale price must be greater than the provided min_price
    3. The stock's percentage change must be greater than the average percentage change for its sector
    4. The average percentage change for the stock's sector must be greater than the provided min_sector_average
    5. The stock's market cap must be between marketcap_min and marketcap_max
    
    Parameters:
    min_volume: The minimum volume a stock must have to be included in the list
    min_price: The minimum last sale price a stock must have to be included in the list
    min_sector_average: The minimum average percentage change a stock's sector must have to be included in the list
    marketcap_min: The minimum market cap a stock must have to be included in the list
    marketcap_max: The maximum market cap a stock can have to be included in the list
    
    Returns:
    A list of stocks that meet the above criteria
    """    
    try:
        # Set headers for the request
        headers = {
            'authority': 'api.nasdaq.com',
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
            'origin': 'https://www.nasdaq.com',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.nasdaq.com/',
            'accept-language': 'en-US,en;q=0.9',
        }
        # Set parameters for the request
        params = (
            ('tableonly', 'true'),
            ('download', 'true'),
        )
        # Send request and get the JSON data
        r = requests.get('https://api.nasdaq.com/api/screener/stocks', headers=headers, params=params)
        data = r.json()['data']
        # Convert data to a Pandas DataFrame
        df = pd.DataFrame(data['rows'], columns=data['headers'])
        # Convert volume, marketCap, lastsale, and pctchange columns to appropriate data types
        df['volume'] = df['volume'].apply(int)
        df['marketCap'] = df['marketCap'].apply(lambda x: float(x.replace('%', '')) if x != '' else float('nan'))
        df['lastsale'] = df['lastsale'].apply(lambda x: float(x.replace('$', '')))
        df['pctchange'] = df['pctchange'].apply(lambda x: float(x.replace('%', '')) if x != '' else float('nan'))
        # Calculate the average pctchange for each sector
        sector_averages = df.groupby('sector')['pctchange'].mean().to_dict()
        # Filter the DataFrame based on the specified conditions
        filtered_df = df.loc[
            (df['lastsale'] > min_price) & 
            (df['volume'] > min_volume)  & 
            (df['pctchange'] > df['sector'].map(sector_averages)) & 
            (df['sector'].map(sector_averages) > min_sector_average) &
            (df['marketCap'] > marketcap_min) & 
            (df['marketCap'] < marketcap_max)
        ]
        # Return the filtered DataFrame as a list
        asset_list = filtered_df.values.tolist()
        # Confirm assets are in our dbs
        parsed_asset_list = []
        for asset in asset_list:
            if indicators.price(asset[0], 'stock')['msg'] == 'success':
                parsed_asset_list.append(asset)
        return {
            'data': parsed_asset_list,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'recommendations.py',
                'function': 'get_stocks',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))

def get_cryptos():
    """
    This function returns a list of all available non-leveragable crypto assets.
    """
    try:
        asset_list = config.non_leveragable_crypto
        return {
            'data': asset_list,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'recommendations.py',
                'function': 'get_cryptos',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))

def get_leveraged_cryptos():
    """
    This function is used to get the list of leveragable crypto assets from the config file.
    """
    try:
        asset_list = config.leveragable_crypto
        return {
            'data': asset_list,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'recommendations.py',
                'function': 'get_stocks',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))