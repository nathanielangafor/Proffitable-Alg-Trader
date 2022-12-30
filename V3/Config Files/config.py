# Required modules
import datetime
import robin_stocks.robinhood as r

# Trade settings
# Percentage of profit to take when closing a trade
take_profit_percents = {
    'crypto': 0.3,
    'stock': 3
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
    'BTC': {
        'asset_type': 'crypto',
        'gate_bypass': [],
    },
    'BNB': {
        'asset_type': 'crypto',
        'gate_bypass': [],
    },
    'JPM': {
        'asset_type': 'stock',
        'gate_bypass': ['momentum_gate'],
    },
    'APRN': {
        'asset_type': 'stock',
        'gate_bypass': ['momentum_gate'],
    },
    'BLK': {
        'asset_type': 'stock',
        'gate_bypass': ['momentum_gate'],
    },
    'ICPT': {
        'asset_type': 'stock',
        'gate_bypass': ['momentum_gate'],
    },
    'RETA': {
        'asset_type': 'stock',
        'gate_bypass': ['momentum_gate']
    }
}

# API keys
api_keys = {
    # Key for Twelve Data API
    'twelveData.com': '',
}

# File paths
csv_files_path = '/Users/appleid/Desktop/Other Files/V3/Program Files/CSV Files/'
loggingFile = '/Users/appleid/Desktop/Other Files/V3/Program Files/signals.txt'

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
    # Broker login
    'username': '',
    'password': '',
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

def authenticateRobinhood():
    r.login(stocks['username'], stocks['password'])

# authenticate robinhood
authenticateRobinhood()

# useful variables
historicalLenth = 5000
