# Required modules
import datetime
import json
import random
import os
import hashlib
import pandas as pd
import time
import sys
import requests
from eth_utils import to_checksum_address

# Import custom modules
sys.path.append('Database')
import database
import recommendations
# Append the 'Analysis' folder to path and import the needed module
sys.path.append('Analysis')
import gates
import indicators 

# Trade settings
timeframe_converter = {
    '1m': '1min',
    '1h': '1h',
    '1d': '1day'
}

# Stock market hours
stock_market_hours = {
    'open_hour': 9,
    'open_minute': 30,
    'close_hour': 16,
    'close_minute': 0
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
    'fundamental_gate': {
        'crypto': {
            'allowed_fear_and_greed': ['Fear', 'Extreme Fear', 'Neutral']
        }, 
        'stocks': {
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
    'fundamental_gate': {
        'crypto': {
            'allowed_fear_and_greed': ['Fear', 'Extreme Fear', 'Neutral']
        }, 
        'stocks': {
            'required_fields': {
                'pe_gate': ['P/E', 'Forward P/E'],
                'eps_gate': ['EPS (ttm)', 'EPS next Y', 'EPS next Q', 'EPS this Y', 'EPS growth next Y', 'EPS next 5Y', 'EPS past 5Y', 'EPS Q/Q'],
                'sales_gate': ['Sales', 'Sales past 5Y', 'P/S'],
                'book_gate': ['P/B', 'Book/sh'],
                'return_gate': ['ROI', 'ROA', 'ROE'],
                'cash_gate': ['P/C', 'Cash/sh', 'P/FCF'],
                'qc_ratio_gate': ['Quick Ratio', 'Current Ratio'],
                'margin_gate': ['Oper. Margin', 'Gross Margin', 'Profit Margin'],
                'debt_gate': ['Debt/Eq', 'LT Debt/Eq']
            },
            'field_data': {
                'pe': 20,
                'min_forward_pe': 10,
                'max_forward_pe': 20,
                'eps_ttm': 0,
                'eps_this_y': 0,
                'eps_next_q': 0,
                'eps_next_y': 0,
                'eps_growth_next_y': 0,
                'eps_next_5y': 0,
                'eps_past_5y': 0,
                'eps_q_q': 0,
                'sales_past_5y': 0,
                'sales': 0,
                'ps': 4,
                'book_sh': 0,
                'pb_max': 3,
                'pb_min': 0,
                'roa': 5,
                'roe': 15,
                'roi': 10,
                'cash_sh': 1,
                'pc': 10,
                'pfcf': 15,
                'quick_ratio': 1,
                'current_ratio': 1,
                'operating_margin': 0,
                'profit_margin': 0,
                'gross_margin': 0,
                'debt_eq': 1,
                'lt_debt_eq': 1   
            }      
        }
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

# Asset type settings
crypto = {
    # Asset IDs on mux.network
    'asset_ids': {
        # BTC ID on mux.network
        'BTC': {
            'id': 4
        },
        # ETH ID on mux.network
        'ETH': {
            'id': 3
        },
        # BNB ID on mux.network
        'BNB': {
            'id': 6
        },
        # AVAX ID on mux.network
        'AVAX': {
            'id': 5
        },
    },
    # Price endpoint
    'price_url': 'https://app.mux.network/api/liquidityAsset'
}

# Useful variables
fastapi_port = 9000
js_server_port = 8080
historicalLenth = 500
penny_stock_definition = 7
csv_file_directory = 'Program Files/CSV Files/'
api_keys = {
    'twelveData.com': [
        '8e9316fa13c04f9299c2a676869192d4', # Johnnydoe@1secmail.com:Johnnydoe@1
    ],
    'discord': ''
}
leveragable_crypto = ['BTC', 'ETH', 'AVAX', 'BNB']
non_leveragable_crypto = ['AAVE', 'COMP', 'BCH', 'LINK', 'ETC', 'LTC', 'SOL']
brokers = ['mux', 'robinhood']

def generate_historical_url(asset, asset_type, timeframe):
    """
    This function takes in an asset name, asset type, and time frame and generates a historical data URL using the TwelveData API.
    The generated URL can be used to retrieve historical data for the specified asset, asset type, and time frame.
    
    Parameters:
    asset (str): The name of the asset for which historical data is to be retrieved.
    asset_type (str): The type of asset for which historical data is to be retrieved. Can be 'crypto' or 'stock'.
    timeframe (str): The time frame for which historical data is to be retrieved. Can be '1min', '5min', '15min', '1hour', '1day', '1week'
    """
    now = datetime.datetime.now()
    end_date = now.strftime('%Y-%m-%d %H:%M:%S')
    # Define base URL
    base_url = 'https://api.twelvedata.com/time_series?apikey={}&interval={}&symbol={}&format=JSON&outputsize={}&end_date={}'
    
    try:
        # Check if asset type is crypto or stock
        if asset_type == 'crypto':
            url = base_url.format(random.choice(api_keys["twelveData.com"]), timeframe_converter[timeframe], asset+'/USD', historicalLenth, end_date)
            url += '&exchange=Binance'
        elif asset_type == 'stock':
            url = base_url.format(random.choice(api_keys["twelveData.com"]), timeframe_converter[timeframe], asset, historicalLenth, end_date)
        return {
            'data': url,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'generate_historical_url',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))   
        return error

def generate_file_name(asset, timeframe):
    """
    Generate the file name for storing data for the given asset.
    
    Parameters:
    asset (str): The name of the asset.
    timeframe (str): The timeframe for the asset (e.g. 1m, 1h, 1d).

    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        file_name = f'{csv_file_directory}{asset}{timeframe}.csv'
        return {
            'data': file_name,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'generate_file_name',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))   
        return error

def update_discord_channel(api_key, discord_channel):
    """
    Update the Discord channel for a user in the database.

    Parameters:
    api_key (str): The API key of the user to update.
    discord_channel (str): The new Discord channel for the user.
    """
    try:
        # Update the Discord channel for the user with the given API key
        database.update_by_value('users', 'api_key', api_key, ['discord_channels'], [discord_channel])
        return {
            'data': f'Discord channel for user {api_key} has been changed to {discord_channel}',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'update_discord_channel',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def update_defi_config(api_key, wss_node, mnemonic, wallet_address):
    """
    Update the DeFi configuration for a user in the database.

    Parameters:
    api_key (str): The API key of the user to update.
    wss_node (str): The new WebSocket node URL for the user.
    mnemonic (str): The new mnemonic phrase for the user.
    wallet_address (str): The new wallet address for the user.
    """
    try:
        # Convert to checksum address
        wallet_address = to_checksum_address(wallet_address)
        # Build the data structure
        defi_config = {
            'wss_node': wss_node,
            'mnemonic': mnemonic,
            'wallet_address': wallet_address
        }
        defi_config = json.dumps(defi_config)
        # Update the DeFi configuration for the user with the given API key
        database.update_by_value('users', 'api_key', api_key, ['defi_config'], [defi_config])
        return {
            'data': f'DeFi configs for user {api_key} has been updated to\n{defi_config}',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'update_defi_config',
                'error': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def update_robinhood_config(api_key, robinhood_username, robinhood_password):
    """
    Update the robinhood credentials for a user in the database.

    Parameters:
    api_key (str): The API key of the user to update.
    robinhood_username (str): The new robinhood username for the user.
    robinhood_password (str): The new robinhood password for the user.
    """
    try:
        # Build the data structure
        robinhood_config = {
            'username': robinhood_username,
            'password': robinhood_password
        }
        robinhood_config = json.dumps(robinhood_config)
        # Update the robinhood credentials for the user with the given API key
        database.update_by_value('users', 'api_key', api_key, ['robinhood_config'], [robinhood_config])
        return {
            'data': f'Robinhood configs for user {api_key} has been changed to\n{robinhood_config}',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'update_robinhood_config',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def get_assets():
    """
    Retrieve all assets from the database.
    """
    try:
        return_dict = {}
        # get list of asset ids
        asset_ids = [asset['id'] for asset in database.select_all('assets')]
        # iterate over asset ids and retrieve asset data for each id
        for asset_id in asset_ids:
            asset = database.select_by_value('assets', 'id', asset_id)[0]
            return_dict[asset_id] = {
                'asset_name': asset['asset'],
                'asset_price': 0 if asset['asset_price'] == '' else float(asset['asset_price']),
                'asset_side': asset['asset_side'],
                'initialized_asset': asset['initialized_asset'],
                'asset_id': asset['asset_id'],
                'id': asset_id,
                'asset_type': asset['asset_type'],
                'amount': float(asset['amount']),
                'multiplier': float(asset['multiplier']),
                'timeframe': asset['timeframe'],
                'slippage_percent': float(asset['slippage_percent']),
                'take_profit_percent': float(asset['take_profit_percent']),
                'gate_bypass': asset['gate_bypass'].split(','),
                'last_iteration': asset['last_iteration'],
                'last_action_order_type': asset['last_action_order_type'],
                'last_action_price': 0 if asset['last_action_price'] == 'None' else float(asset['last_action_price']),
                'fundamental_gate': asset['fundamental_gate'],
                'broker_direction': asset['broker_direction']
            }
        return {
            'data': return_dict,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'get_assets',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def get_asset_price(asset):
    """
    Returns the price of an asset from the databse.

    Parameters:
    asset (str): asset whose price will be retrieved.
    """
    return database.select_by_value('assets', 'asset', asset)

def get_asset(api_key):
    """
    Returns a dictionary containing all assets in the database.

    Parameters:
    api_key (str): the API key of the user.
    """
    try:
        return_dict = {}
        # Get a list of all asset names in the database
        asset_names = [data['asset'] for data in database.select_all('assets')]
        # Iterate over each asset name
        for asset_name in asset_names:
            # Select all data for the current asset
            assets = database.select_by_value('assets', 'asset', asset_name)
            # Iterate over each asset data record
            for asset in assets:
                if api_key in asset['id']:
                    # Add the asset data to the return dictionary
                    return_dict[asset_name] = {
                        'asset_name': asset_name,
                        'asset_price': 0 if asset['asset_price'] == '' else float(asset['asset_price']),
                        'initialized_asset': asset['initialized_asset'],
                        'asset_id': asset['asset_id'],
                        'id': asset['id'],
                        'asset_type': asset['asset_type'],
                        'amount': float(asset['amount']),
                        'multiplier': float(asset['multiplier']),
                        'timeframe': asset['timeframe'],
                        'slippage_percent': float(asset['slippage_percent']),
                        'take_profit_percent': float(asset['take_profit_percent']),
                        'gate_bypass': asset['gate_bypass'].split(','),
                        'last_iteration': asset['last_iteration'],
                        'last_action_order_type': asset['last_action_order_type'],
                        'last_action_price': 0 if asset['last_action_price'] == 'None' else float(asset['last_action_price']),
                        'fundamental_gate': asset['fundamental_gate'],
                        'broker_direction': asset['broker_direction']
                    }
        return {
            'data': return_dict,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'get_asset',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def add_asset(api_key, asset, asset_type, amount, multiplier, timeframe, slippage_percent, take_profit_percent, gate_bypass, broker_direction):
    """
    Add an asset to the assets table in the database.

    Parameters:
    asset (str): The name of the asset.
    asset_type (str): The type of the asset (e.g. stock, crypto).
    amount (float): The amount of the asset to be purchased.
    multiplier (float): The multiplier to be applied to the amount.
    timeframe (str): The timeframe for the asset (e.g. 1m, 1h, 1d).
    slippage_percent (float): The acceptable slippage as a percentage.
    take_profit_percent (float): The percentage at which to take profit.
    gate_bypass (str): A list of gate functions to bypass, separated by commas.
    """
    try:
        # Check if the asset already exists for the user
        existing_asset_entries = database.select_by_value('assets', 'id', f'{asset}{timeframe}-{api_key}')
        if len(existing_asset_entries) > 0:
            raise ValueError(f'Asset {asset} on timeframe {timeframe} already exists for user {api_key}.')
        # Check if the user exists
        does_user_exist = database.select_by_value('users', 'api_key', api_key)
        if len(does_user_exist) == 0:
            raise ValueError(f'User with api_key {api_key} does not exist.')
        # Create the asset ID
        asset_id = asset + timeframe
        # Check if the fundamental gate is in the gate bypass list
        if 'fundamental_gate' not in gate_bypass.split(','):
            # Get the data from the fundamental gate
            gate_data = gates.fundamental_gate(asset_type, gate_settings)
            # Check if the gate returned success
            if gate_data['msg'] == 'success':
                fundamental_gate = gate_data['data']
            else:
                fundamental_gate = 'false'
        # Create the values for the asset
        values = [f'{asset}{timeframe}-{api_key}', asset, '', 'buy', 'false', asset_id, asset_type, str(amount), str(multiplier), timeframe, str(slippage_percent), str(take_profit_percent), gate_bypass, 'None', 'None', 'None', fundamental_gate, broker_direction]
        # Insert the asset into the database
        database.insert_record('assets', values)
        return {
            'data': f'Asset {asset} on timeframe {timeframe} added for user {api_key}.',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'add_asset',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def remove_asset(api_key, asset, timeframe):
    """Removes an asset from the assets table in the database.
    
    Parameters:
    api_key (str): the API key of the user.
    asset (str): the name of the asset.
    timeframe (str): the timeframe for the asset (e.g. 1m, 1h, 1d).
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Delete the record from the assets table with the matching asset and timeframe and API key
        database.delete_record_by_value('assets', 'id', f'{asset}{timeframe}-{api_key}')
        return {
            'data': f'Asset {asset} on timeframe {timeframe} removed for user {api_key}.',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'remove_asset',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def add_user(email, username, password, priviledge, discord_channel='', wss_node='', mnemonic='', wallet_address='', robinhood_username='', robinhood_password=''):
    """Adds a new user to the database.
    
    Parameters:
    email (str): the email of the user.
    username (str): the username of the user.
    password (str): the password of the user.
    priviledge (str): the privilege level of the user.
    discord_channel (str): the Discord channel of the user. Default is an empty string.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Hash the password and generate an API key
        password = hash(password)['data']
        api_key = hash(username + password)['data']
        # Check if the user already exists in the database
        existing_user_entries = database.select_by_value('users', 'username', username)
        if len(existing_user_entries) > 0:
                raise ValueError(f'User {username} already exists.')
        else:
            # Build broker data
            defi_config = {
                'wss_node': wss_node,
                'mnemonic': mnemonic,
                'wallet_address': wallet_address
            }
            robinhood_config = {
                'username': robinhood_username,
                'password': robinhood_password
            }
            # Add the user to the database
            values = [email, username, password, discord_channel, api_key, priviledge, json.dumps(defi_config), json.dumps(robinhood_config)]
            database.insert_record('users', values)
        return {
            'data': {
                'username': username,
                'password': password,
                'api_key': api_key
            },
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'add_user',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def remove_user(api_key):
    """Removes a user from the database.
    
    Parameters:
    api_key (str): the API key of the user to be removed.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Check if the user already exists in the database
        existing_asset_entries = database.select_by_value('users', 'api_key', api_key)
        if len(existing_asset_entries) == 0:
            raise ValueError(f'User with api_key {api_key} already does not exist.')
        else:
            # Remove the user from the database
            database.delete_record_by_value('users', 'api_key', api_key)
            return {
                'data': f'User with api_key {api_key} has been removed.',
                'msg': 'success'
            }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'remove_user',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def get_users():
    """Retrieves all users from the database.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Initialize the return dictionary
        return_dict = {}
        # Get a list of all user API keys
        users_api_keys = [user['api_key'] for user in database.select_all('users')]
        # Iterate over the API keys and retrieve the user data for each key
        for users_api_key in users_api_keys:
            user = database.select_by_value('users', 'api_key', users_api_key)
            return_dict[users_api_key] = user
        return {
            'data': return_dict,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'get_users',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def get_user(api_key):
    """Retrieves a users from the database.

    Parameters:
    api_key (str): the API key of the user to be removed.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Initialize the return dictionary
        return_dict = {}
        # Get a list of all user API keys
        users_api_keys = [user['api_key'] for user in database.select_all('users')]
        # Iterate over the API keys and retrieve the user data for each key
        for users_api_key in users_api_keys:
            if users_api_key == api_key:
                user = database.select_by_value('users', 'api_key', users_api_key)
                return_dict[users_api_key] = user
                break
        if len(return_dict) == 0:
            raise ValueError('User does not exist.')
        return {
            'data': return_dict,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'get_user',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def get_errors():
    """Retrieves all errors from the database.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Initialize the return dictionary
        return_dict = {}
        # Get a list of all user API keys
        error_datetimes = [error['datetime'] for error in database.select_all('errors')]
        # Iterate over the API keys and retrieve the user data for each key
        for error_datetime in error_datetimes:
            error = database.select_by_value('errors', 'datetime', error_datetime)
            return_dict[error_datetime] = error
        return {
            'data': return_dict,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'get_errors',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def get_signals():
    """Retrieves all signals from the database.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Initialize the return dictionary
        return_dict = {}
        # Get a list of all signal IDs
        signal_ids = [signal['id'] for signal in database.select_all('signals')]
        # Iterate over the signal IDs and retrieve the signal data for each ID
        for signal_id in signal_ids:
            signal = database.select_by_value('signals', 'id', signal_id)
            return_dict[signal_id] = signal
        return {
            'data': return_dict,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'get_signals',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def get_signal(api_key):
    """Retrieves all signals from the database for the given API key.
    
    Parameters:
    api_key (str): the API key.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Initialize the return dictionary
        return_dict = {}
        # Get a list of all signal IDs
        signal_ids = [signal['id'] for signal in database.select_all('signals')]
        # Iterate over the signal IDs and retrieve the signal data for each ID
        for signal_id in signal_ids:
            signal = database.select_by_value('signals', 'id', signal_id)
            # If the API key matches the signal's API key, add the signal to the return dictionary
            if api_key in signal[0]['api_key']:
                return_dict[signal_id] = signal
        return {
            'data': return_dict,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'get_signal',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def initialize_assets_table():
    """Initializes the 'assets' table in the database.

    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Set the name and columns of the table
        table = "assets"
        columns = ["id TEXT", 'asset TEXT', 'asset_price TEXT', 'asset_side', 'initialized_asset TEXT', 'asset_id TEXT', "asset_type TEXT", 'amount TEXT', 'multiplier TEXT', 'timeframe TEXT', 'slippage_percent TEXT', 'take_profit_percent TEXT', "gate_bypass TEXT", "last_iteration TEXT", 'last_action_order_type TEXT', 'last_action_price TEXT', 'fundamental_gate TEXT', 'broker_direction TEXT']
        # Create the table if it does not exist or if hard_reset is True
        try:
            database.delete_table(table)
        except:
            pass
        database.create_table(table, columns)
        return {
            'data': f'Table {table} initialized.',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'initialize_assets_table',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error
    
def initialize_errors_table():
    """Initializes the 'errors' table in the database.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Set the name and columns of the table
        table = "errors"
        columns = ["datetime TEXT", 'log TEXT']
        # Create the table if it does not exist or if hard_reset is True
        try:
            database.delete_table(table)
        except:
            pass
        database.create_table(table, columns)
        return {
            'data': f'Table {table} initialized.',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'initialize_errors_table',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def initialize_signals_table():
    """Initializes the 'signals' table in the database.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Set the name and columns of the table
        table = "signals"
        columns = ["id INTEGER PRIMARY KEY", 'api_key TEXT', 'signal TEXT']
        # Create the table if it does not exist or if hard_reset is True
        try:
            database.delete_table(table)
        except:
            pass
        database.create_table(table, columns)
        return {
            'data': f'Table {table} initialized.',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'initialize_signals_table',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def initialize_users_table():
    """Initializes the 'users' table in the database.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Set the name and columns of the table
        table = "users"
        columns = ['email TEXT', 'username TEXT', 'password TEXT', 'discord_channels TEXT', 'api_key TEXT', 'priviledge TEXT', 'defi_config TEXT', 'robinhood_config TEXT']
        # Create the table if it does not exist or if hard_reset is True
        try:
            database.delete_table(table)
        except:
            pass
        database.create_table(table, columns)
        return {
            'data': f'Table {table} initialized.',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'initialize_users_table',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def hash(text):
    """Hashes the given text using SHA-256.
    
    Parameters:
    text (str): the text to hash.
    
    Returns:
    dict: a dictionary containing the hashed text and the status of the operation.
        The dictionary has the following keys:
            'data': the hashed text.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Hash the text using SHA-256
        hashed_text = hashlib.sha256(text.encode()).hexdigest()
        return {
            'data': hashed_text,
            'msg': 'success'
        }     
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'hash',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def string_to_json(string):
    """Converts a string to a JSON object.
    
    Parameters:
    string (str): the string to convert.
    
    Returns:
    dict: a dictionary containing the JSON object and the status of the operation.
        The dictionary has the following keys:
            'data': the JSON object.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # convert the string to a JSON object
        obj = json.loads(string.replace("'", '"').replace('True', 'true').replace('False', 'false'))
        return {
            'data': obj,
            'msg': 'success'
        } 
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'string_to_json',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def string_to_epoch(timeInput):
    """Converts a time string in '%Y-%m-%d %H:%M:%S' format to epoch time.
    
    Parameters:
    timeInput (str): Time string in '%Y-%m-%d %H:%M:%S' format.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # convert the time string to a datetime object
        dt = datetime.datetime.strptime(timeInput, '%Y-%m-%d %H:%M:%S')
        # convert the datetime object to epoch time
        epoch_time = dt.timestamp()        
        return {
                'data': epoch_time,
                'msg': 'success'
            } 
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'string_to_epoch',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def read_dataframe(filename):
    """Reads a CSV file and returns the contents as a Pandas DataFrame.
    
    Parameters:
    filename (str): the name of the CSV file to read.
    
    Returns:
    dict: a dictionary containing the DataFrame and the status of the operation.
        The dictionary has the following keys:
            'data': the DataFrame.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    # Try to read the DataFrame
    try:
        for x in range(30):
            try:
                df = pd.read_csv(filename)
                return {
                    'data': df,
                    'msg': 'success'
                }
            except:
                time.sleep(1)
        raise ValueError('Error retrieving CSV file information.')
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'read_dataframe',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def delete_csv_file(file):
    """Deletes the specified file from the 'CSV Files' directory.

    Parameters:
    file (str): the name of the file to delete.

    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Set the directory you want to delete the files from
        directory = 'Program Files/CSV Files'
        # Get the full path of the file
        file_path = os.path.join(directory, file)
        # If the file is a regular file (not a directory), delete it
        if os.path.isfile(file_path):
            os.unlink(file_path)
        return {
            'data': f'File {file} has been deleted.',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'delete_csv_file',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def error_message(error):
    """
    Create a dictionary for an error message.
    
    Parameters:
    error (str): The error message.
    
    Returns:
    dict: A dictionary with the error message and a 'status' of 'error'.
    """
    return {
        'data': error,
        'status': 'error'
    }

def success_message(success):
    """
    Create a dictionary for a success message.
    
    Parameters:
    success (str): The success message.
    
    Returns:
    dict: A dictionary with the success message and a 'status' of 'success'.
    """
    return {
        'data': success,
        'status': 'success'
    }

def get_all_admin_api_keys():
    """
    Get the API keys of all users with 'admin' priviledge.

    Returns:
    list: A list of API keys for users with 'admin' priviledge.
    """
    try:
        admin_keys = []
        users = get_users()['data']
        for user in users:
            if users[user][0]['priviledge'] == '0':
                admin_keys.append(user)
        return admin_keys
    except Exception as e:
        error = {
            'data': {
                'file': 'config.py',
                'function': 'get_all_admin_api_keys',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error

def sanitize_inputs(
        email=None,
        username=None,
        asset_name=None, 
        asset_type=None, 
        amount=None, 
        multiplier=None, 
        slippage_percent=None, 
        take_profit_percent=None, 
        timeframe=None, 
        broker_direction=None,
        gate_bypass=None
    ):
    """
    Sanitize and validate user input parameters.
    
    Parameters:
    asset_name (str, optional): The name of the asset.
    asset_type (str, optional): The type of the asset (e.g. 'currency', 'commodity', 'stock').
    amount (float, optional): The amount of the asset being traded.
    multiplier (float, optional): The multiplier for the trade.
    slippage_percent (float, optional): The slippage percentage for the trade.
    take_profit_percent (float, optional): The take profit percentage for the trade.
    timeframe (str, optional): The time frame for the data (e.g. '1d', '1h', '1m').
    broker_direction (str, optional): The broker executing the order.
    gate_bypass (str, optional): Comma-separated list of gates to bypass.
    
    Returns:
    dict: A dictionary with the sanitized and validated input parameters, and a 'msg' field with a value of 'success' or 'error'.
    """
    return_dictionary = {}
    return_dictionary['data'] = {}
    return_dictionary['msg'] = 'success'
    # Sanitize and validate 'email' parameter
    if email:
        return_dictionary['data']['email'] = email.lower()
    # Sanitize and validate 'username' parameter
    if email:
        return_dictionary['data']['username'] = username.lower()
    # Sanitize and validate 'asset_name' parameter
    if asset_name:
        return_dictionary['data']['asset_name'] = asset_name.upper()
    # Sanitize and validate 'asset_type' parameter
    if asset_type:
        asset_type = asset_type.lower()
        if asset_type in ['stock', 'crypto']:
            return_dictionary['data']['asset_type'] = asset_type.lower()
        else:
            return_dictionary['msg'] = 'error'
    # Sanitize and validate 'amount' parameter
    if amount:
        amount = str(amount)
        if isfloat(amount):
            return_dictionary['data']['amount'] = float(amount)
        else:
            return_dictionary['msg'] = 'error'
    # Sanitize and validate 'multiplier' parameter
    if multiplier:
        multiplier = str(multiplier)
        if isfloat(multiplier):
            return_dictionary['data']['multiplier'] = float(multiplier)
        else:
            return_dictionary['msg'] = 'error'
    # Sanitize and validate 'slippage_percent' parameter
    if slippage_percent:
        slippage_percent = str(slippage_percent)
        if isfloat(slippage_percent):
            return_dictionary['data']['slippage_percent'] = float(slippage_percent)
        else:
            return_dictionary['msg'] = 'error'
    # Sanitize and validate 'take_profit_percent' parameter
    if take_profit_percent:
        take_profit_percent = str(take_profit_percent)
        if isfloat(take_profit_percent):
            return_dictionary['data']['take_profit_percent'] = float(take_profit_percent)
        else:
            return_dictionary['msg'] = 'error'
    # Sanitize and validate 'timeframe' parameter
    if timeframe:
        timeframe = timeframe.lower()
        if timeframe in ['1m', '1h', '1d']:
            return_dictionary['data']['timeframe'] = timeframe.lower()
        else:
            return_dictionary['msg'] = 'error'
    # Sanitize and validate 'broker_direction' parameter
    if broker_direction:
        broker_direction = broker_direction.lower()
        if timeframe in brokers:
            return_dictionary['data']['broker_direction'] = broker_direction.lower()
        else:
            return_dictionary['msg'] = 'error'
    # Sanitize and validate 'gate_bypass' parameter
    if gate_bypass:
        gates = gate_bypass.lower().split(',')
        for gate in gates:
            if gate in ['macd_gate', 'rsi_gate', 'cci_gate', 'trend_gate', 'momentum_gate', 'ichimoku_gate', 'ema_gate', 'bollinger_gate', 'cloud_gate']:
                return_dictionary['data']['gate_bypass'] = gate_bypass.lower()
            else:
                return_dictionary['msg'] = 'error'
    else:
        # Set the defult to an empty string
        return_dictionary['data']['gate_bypass'] = ''
    return return_dictionary

def log_error(error_message):
    """
    This function data_log an error message to the database.
    
    Parameters:
    error_message (str): The error message to be logged.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        database.insert_record('errors', [time.ctime(time.time()), error_message])
        return {
            'data': 'Error inserted.',
            'msg': 'success'
        }
    except Exception as e:
        return {
            'data': {
                'file': 'config.py',
                'function': 'log_error',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }

def isfloat(val):
    """
    This function determins if a string val can be a float.

    Parameters:
    val (str): The string to be checked.
    """
    return all([[any([i.isnumeric(), i in ['.','e']]) for i in val], len(val.split('.')) == 2])

def initialize_admins():
    api_keys = []
    # Shared chainstack wss node
    wss_node = ''
    api_keys.append(add_user('notanemail@email.com', 'nemail', 'izMeM@r10a', '0', '', wss_node, '', '', '', '')['data']['api_key'])
    # Add recommended stocks to user's assets
    for api_key in api_keys:
        asset_list = [asset[0] for asset in recommendations.get_stocks(1000000, penny_stock_definition, 2, 300000000, 2000000000)['data']]
        for asset in asset_list:
            add_asset(api_key, asset, 'stock', '100', '1', '1h', '.25', '1.25', 'momentum_gate', 'robinhood')
    # Add recommended leveraged cryptocurrencies to user's assets
        asset_list = recommendations.get_leveraged_cryptos()['data']
        for asset in asset_list:
            add_asset(api_key, asset, 'crypto', '100', '20', '1h', '.025', '.25', '', 'mux')
    # Add recommended cryptocurrencies to user's assets
        asset_list = recommendations.get_cryptos()['data']
        for asset in asset_list:
            add_asset(api_key, asset, 'crypto', '100', '20', '1h', '.025', '.25', '', 'robinhood')

def calculate_best_amount(asset_price, amount):
    """Calculate the best amount of the asset that can be purchased given the current price and a desired amount in USD.
    
    Parameters:
    asset_price (float): The current price of the asset.
    amount (float): The desired amount in USD to be spent on purchasing the asset.
    
    Returns:
    float: The best amount of the asset that can be purchased.
    """
    return round(amount / asset_price, 3)

def get_all_stocks():
    """
    This function gets a list of all stocks available on the Nasdaq stock exchange by sending a GET request to the Nasdaq API with certain headers and parameters.
    """
    try:
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
        stock_data = r.json()['data']['rows']
        stocks = [stock['symbol'] for stock in stock_data]
        return {
            'data': stocks,
            'msg': 'success'
        }
    except Exception as e:
        return {
            'data': {
                'file': 'config.py',
                'function': 'get_all_stocks',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }

def reset(df, order_type, asset, timeframe):
    """
    Reset the dataframe and indicators until the direction gate is not attempting the specified order type.

    Parameters:
    df (DataFrame): The dataframe to be reset.
    order_type (str): The order type to check against the direction gate.
    asset (str): The asset being traded.
    timeframe (str): The timeframe of the data in the dataframe.

    Returns:
    DataFrame: The reset dataframe.
    """
    try:
        if order_type == 'long':
            # Reset the dataframe and indicators until the direction gate is not attempting a long order
            while indicators.calculate_macd(df)['histogram'] > 0:
                df = read_dataframe(generate_file_name(asset, timeframe)['data'])
                # Check if the request was successful
                if df['msg'] == 'success':
                    df = df['data']
                time.sleep(3)
        if order_type == 'short':
            # Reset the dataframe and indicators until the direction gate is not attempting a short order
            while indicators.calculate_macd(df)['histogram'] < 0:            
                df = read_dataframe(generate_file_name(asset, timeframe)['data'])
                # Check if the request was successful
                if df['msg'] == 'success':
                    df = df['data']
                time.sleep(3)
        return df
    except Exception as e:
        error = {
            'data': {
                'file': 'main.py',
                'function': 'reset',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        log_error(json.dumps(error))
        return error
