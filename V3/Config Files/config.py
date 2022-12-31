# Required modules
import datetime
import robin_stocks.robinhood as r

import sys
sys.path.append('../Database')
import database

# Trade settings
# Percentage of profit to take when closing a trade
take_profit_percents = {
    'crypto': 0.3,
    'stock': 1
}
# Slippage when executing an order
slippage_percent = {
    'crypto': 0.025,
    'stock': .25
}
# Default trade size for new trades in dollars
default_trade_size = 1 
# Multiplier for calculating trade sizes
multiplier = 30
# Frequency of ticker data
ticker_frequency = '1h'

# Assets being monitored
assets = {
    'ETH': {
    'asset_type': 'crypto',
    'gate_bypass': [],
    },
    'BTC': {
    'asset_type': 'crypto',
    'gate_bypass': [],
    },
    'BNB': {
    'asset_type': 'crypto',
    'gate_bypass': [],
    },
    'DDOG': {
    'asset_type': 'stock',
    'gate_bypass': ['momentum_gate']
    },
    'ILMN': {
    'asset_type': 'stock',
    'gate_bypass': ['momentum_gate']
    },
    'DOCU': {
    'asset_type': 'stock',
    'gate_bypass': ['momentum_gate']
    },
    'SWKS': {
    'asset_type': 'stock',
    'gate_bypass': ['momentum_gate']
    },
    'EBAY': {
    'asset_type': 'stock',
    'gate_bypass': ['momentum_gate']
    },
    'CRWD': {
    'asset_type': 'stock',
    'gate_bypass': ['momentum_gate']
    },
    'PYPL': {
    'asset_type': 'stock',
    'gate_bypass': ['momentum_gate']
    },
    'MTCH': {
    'asset_type': 'stock',
    'gate_bypass': ['momentum_gate']
    },
}

# Gate settings
gate_settings = {
    'ema_gate': {
        # Determine if atr should be included
        'long_criteria': True,
        'short_criteria': True
    },
    'cci_gate': {
        # Values to compare CCI to
        'long_criteria': 100,
        'short_criteria': -100
    },
    'rsi_gate': {
        # Values to compare RSI to
        'long_criteria': 65,
        'short_criteria': 35
    },
    'trend_gate': {
        # Ratio minimum for long / shorts in last 200 periods
        'long_criteria': 30,
        'short_criteria': 30
    },
    'cloud_gate': {
        # Percent minimum for size of current ichimoku cloud
        'long_criteria': .1,
        'short_criteria': .1
    },
    'momentum_gate': {
        'long_criteria': 'No data is being passed',
        'short_criteria': 'No data is being passed'
    },
    'macd_gate': {
        'long_criteria': 'No data is being passed',
        'short_criteria': 'No data is being passed'
    },
    'extreme_gate': {
        'long_criteria': 'No data is being passed',
        'short_criteria': 'No data is being passed'
    },
    'adx_gate': {
        'long_criteria': 'No data is being passed',
        'short_criteria': 'No data is being passed'
    },
    'vortex_gate': {
        'long_criteria': 'No data is being passed',
        'short_criteria': 'No data is being passed'
    },
    'ichimoku_gate': {
        'long_criteria': 'No data is being passed',
        'short_criteria': 'No data is being passed'
    },
    'bollinger_gate': {
        'long_criteria': 'No data is being passed',
        'short_criteria': 'No data is being passed'
    },
}

# API keys
api_keys = {
    # Key for Twelve Data API
    'twelveData.com': '2842ddf2300641e99d10c1bfe7e47e84',
}

# File paths
csv_files_path = '../Program Files/CSV Files/'
webullCredentialsFile = '../Program Files/webull_credentials.json'

# Asset type settings
crypto = {
    # Asset IDs on mux.network
    'asset_ids': {
        # Bitcoin ID on mux.network
        'BTC': {
            'id': 4
        },
        # Ethereum ID on mux.network
        'ETH': {
            'id': 3
        },
        # Ethereum ID on mux.network
        'BNB': {
            'id': 6
        },
    },
    # Wallet address
    'my_wallet': '',
    # Price endpoint
    'price_url': 'https://app.mux.network/api/liquidityAsset'
}

stocks = {
    # Robinhood login
    'robinhoodUsername': '',
    'robinhoodPassword': '',
}

# Config functions
def generate_historical_url(asset, asset_type):
    """
    Generates the URL for retrieving historical data for the given asset and asset type.
    """
    now = datetime.datetime.now()
    end_date = now.strftime('%Y-%m-%d %H:%M:%S')
    if asset_type == 'crypto':
        return f'https://api.twelvedata.com/time_series?apikey={api_keys["twelveData.com"]}&interval={ticker_frequency}&symbol={asset}/USD&outputsize={historicalLenth}&format=JSON&end_date={end_date}'
    if asset_type == 'stock':
        return f'https://api.twelvedata.com/time_series?apikey={api_keys["twelveData.com"]}&interval={ticker_frequency}&symbol={asset}&format=JSON&outputsize={historicalLenth}&end_date={end_date}'

def generate_file_name(asset, isBacktesting=False):
    """
    Generates the file name for storing data for the given asset.
    """
    if not isBacktesting:
        return f'{csv_files_path}{asset}.csv'
    else:
        return f'{csv_files_path}{asset}Archive.csv'

# Asset management
def get_assets():
    returnDict = {}
    assets_names = [data['asset'] for data in database.select_all('assets')]
    for asset_name in assets_names:
        asset_datum = database.select_by_value('assets', 'asset', asset_name)
        for asset_data in asset_datum:
            returnDict[asset_name] = {
                'asset_type': asset_data['asset_type'],
                'gate_bypass': asset_data['gate_bypass'].split(',')
            }
    return returnDict

def add_asset(asset, asset_type, gate_bypass):
    if len(database.select_by_value('assets', 'asset', asset)) == 0:
        values = [None, asset, asset_type, gate_bypass]
        database.insert_record('assets', values)

def remove_asset(asset):
    database.delete_record_by_value('assets', 'asset', asset)

# Create tables 
def initialize():
    # Define the table and columns for asset
    table1 = "assets"
    columns1 = ["id INTEGER PRIMARY KEY", 'asset TEXT', "asset_type TEXT", "gate_bypass TEXT"]
    # Define the table and columns for signals
    table2 = "signals"
    columns2 = ["id INTEGER PRIMARY KEY", 'signal TEXT']
    # Create tables if not exist
    try:
        # Create table if not exists
        database.create_table(table1, columns1)
    except:
        pass
    try:
        database.create_table(table2, columns2)
    except:
        pass
    add_asset('BTC', 'crypto', '')

# authenticate robinhood
def authenticateRobinhood():
    r.login(stocks['robinhoodUsername'], stocks['robinhoodPassword'])
authenticateRobinhood()

# useful variables
historicalLenth = 5000
