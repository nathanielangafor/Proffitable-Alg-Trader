import sys
import json

# append the config file path to sys.path
sys.path.append('Config Files')
import config

def limit_buy(r, asset, asset_type, quantity, limit_price):
    """Place a limit buy order.

    Parameters:
    r (Robinhood instance): The instance of the Robinhood class to be used.
    asset (str): The symbol of the asset to be bought.
    asset_type (str): The type of asset being traded (stock or crypto).
    quantity (float): The quantity of the asset to be bought.
    limit_price (float): The limit price of the order.
    """
    try:
        # Place a crypto limit buy order or stock limit buy order based on the asset_type
        data = (
            r.order_buy_crypto_limit(symbol=asset, quantity=quantity, limitPrice=limit_price, timeInForce='gtc', jsonify=True) if asset_type == 'crypto' else 
            r.order_buy_limit(symbol=asset, quantity=quantity, limitPrice=limit_price, timeInForce='gtc', jsonify=True)
        )['id']
        return {
            'data': data,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'orderManager.py',
                'function': 'limit_buy',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error

def limit_sell(r, asset, asset_type, quantity, limit_price):
    """Place a limit sell order.

    Parameters:
    r (Robinhood instance): The instance of the Robinhood class to be used.
    asset (str): The symbol of the asset to be sold.
    asset_type (str): The type of asset being traded (stock or crypto).
    quantity (float): The quantity of the asset to be sold.
    limit_price (float): The limit price of the order.
    """
    try:
        # Place a crypto limit sell order or stock limit sell order based on the asset_type
        data = (
            r.order_sell_crypto_limit(symbol=asset, quantity=quantity, limitPrice=limit_price, timeInForce='gtc', jsonify=True) if asset_type == 'crypto' else 
            r.order_sell_limit(symbol=asset, quantity=quantity, limitPrice=limit_price, timeInForce='gtc', extendedHours=False, jsonify=True)
        )['id']
        return {
            'data': data,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'orderManager.py',
                'function': 'limit_sell',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error

def cancel_order(r, asset_type, order_id):
    """Cancel an order.

    Parameters:
    r (Robinhood instance): The instance of the Robinhood class to be used.
    asset_type (str): The type of asset being traded (stock or crypto).
    order_id (str): The ID of the order.
    """
    try:
        # Cancel the crypto order or stock order based on the asset_type
        data = r.cancel_crypto_order(orderID=order_id) if asset_type == 'crypto' else r.cancel_stock_order(orderID=order_id)
        return {
            'data': data,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'orderManager.py',
                'function': 'cancel_order',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error

def check_status(r, asset_type, order_id):
    """Check the status of an order.

    Parameters:
    r (Robinhood instance): The instance of the Robinhood class to be used.
    asset_type (str): The type of asset being traded (stock or crypto).
    order_id (str): The ID of the order.
    """
    try:
        # Get the status of the crypto order or stock order based on the asset_type
        data = (r.get_crypto_order_info(orderID=order_id) if asset_type == 'crypto' else r.get_stock_order_info(orderID=order_id))['state']
        return {
            'data': data,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'orderManager.py',
                'function': 'check_status',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error

def day_trade_list(r):
    """Get a list of the user's day trades.

    Parameters:
    r (Robinhood instance): The instance of the Robinhood class to be used.
    """
    try:
        data = r.get_day_trades()['equity_day_trades']
        return {
            'data': data,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'orderManager.py',
                'function': 'day_trade_list',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error

def authenticate_robinhood(r, username, password):
    """Authenticate a user on the Robinhood platform.
    
    Parameters:
    r (Robinhood instance): The instance of the Robinhood class to be used.
    username (str): The username of the Robinhood account.
    password (str): The password of the Robinhood account.
    """
    try:
        data = r.login(username, password)
        return {
            'data': data,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'orderManager.py',
                'function': 'authenticate_robinhood',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error