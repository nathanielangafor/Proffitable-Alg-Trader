import sys
import robin_stocks
import json
import time
import asyncio 

# Append the 'Brokers/Robinhood' folder to path and import the needed module
sys.path.append('Brokers/Robinhood')
import rhBroker
# Append the 'Brokers/Mux' folder to path and import the needed module
sys.path.append('Brokers/Mux')
import muxBroker
# Append the 'Config Files' folder to path and import the needed module
sys.path.append('Config Files')
import config

def handle_order(data_log):
    """
    Function that handles the processing of an order and routes it to either the Robinhood or Mux network based on the asset type and leverage.
    It also confirms that the order has been fulfilled within 60 seconds.
    
    Parameters:
    data_log (dict): a dictionary containing the order information such as asset name, type, amount, flag and price.
        
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        api_key = data_log['asset_data']['id'].split('-')[1]
        user = config.get_user(api_key)['data'][api_key][0]
        # Account for slippage in asset_price
        slippage_percent = data_log['asset_data']['slippage_percent'] if (data_log['order_type'] == 'long' and data_log['flag'] == 'buy') or (data_log['order_type'] == 'short' and data_log['flag'] == 'sell') else data_log['asset_data']['slippage_percent'] - (data_log['asset_data']['slippage_percent'] * 2)
        asset_price = round(((100 + slippage_percent) * data_log['asset_data']['asset_price']) / 100.0, 5)
        # Route leveraged crypto orders to the Mux network
        if data_log['asset_data']['broker_direction'] == 'mux':
            defi_config = json.loads(user['defi_config'])
            data = asyncio.run(muxBroker.place_mux_order(
                data_log['asset_data']['asset_name'], 
                data_log['order_type'],
                data_log['asset_data']['amount'],
                data_log['asset_data']['multiplier'],
                asset_price,
                data_log['flag'],
                defi_config['wss_node'],
                defi_config['mnemonic'],
                defi_config['wallet_address']
            ))
            if data['msg'] == 'error':
                raise TimeoutError(f'Asset could not be placed: {data_log}')
            else:
                # Confirm order has been fulfilled within 60 seconds
                time.sleep(15)
                iteration = 0
                while len(muxBroker.get_pending_mux_orders(defi_config['wallet_address'], data_log['asset_data']['asset_name']) > 0) and iteration <= 15:
                    iteration+=1
                    if iteration == 20:
                        # Cancel pending order if it iis a buy order
                        if data_log['flag'] == 'buy':
                            for order in muxBroker.get_pending_mux_orders(defi_config['wallet_address'], data_log['asset_data']['asset_name']):
                                asyncio.run(muxBroker.cancel_mux_order(
                                    order['orderId'], 
                                    defi_config['wss_node'],
                                    defi_config['mnemonic'],
                                    defi_config['wallet_address']
                                    )
                                )
                        raise TimeoutError(f'Asset could not be placed: {data_log}')
                    time.sleep(3)
        if data_log['asset_data']['broker_direction'] == 'robinhood':
            # Fetch robinhood credentials from DB
            robinhood_credentials = json.loads(user['robinhood_config'])
            # Authenticate robinhood
            r = robin_stocks.robinhood
            rhBroker.authenticate_robinhood(r, robinhood_credentials['username'], robinhood_credentials['password'])
            # Route non-leveraged crypto orders and stocks to Robinhood
            if data_log['flag'] == 'buy':
                transaction_id = rhBroker.limit_buy(r, data_log['asset_data']['asset_name'], data_log['asset_data']['asset_type'], config.calculate_best_amount(asset_price, data_log['asset_data']['amount']), asset_price)['data']
            if data_log['flag'] == 'sell':
                # Get the last action price + slippage to determine amount bought
                last_action_price_w_slippage = round(((100 - slippage_percent) * data_log['asset_data']['last_action_price']) / 100.0, 5)
                transaction_id = rhBroker.limit_sell(r, data_log['asset_data']['asset_name'], data_log['asset_data']['asset_type'], config.calculate_best_amount(last_action_price_w_slippage, data_log['asset_data']['amount']), asset_price)['data']
            # Confirm order has been fulfilled within 60 seconds
            iteration = 0
            while rhBroker.check_status(r, data_log['asset_data']['asset_type'], transaction_id)['data'] != 'fulfilled' and iteration <= 20:
                iteration+=1
                if iteration == 20:
                    # Cancel order if it is a buy order
                    if data_log['flag'] == 'buy':
                        rhBroker.cancel_order(r, data_log['asset_data']['asset_type'], transaction_id)
                    raise TimeoutError(f'Asset could not be placed: {data_log}')
                time.sleep(3)
        return {
            'data': f'{transaction_id} has been placed.',
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'orderManager.py',
                'function': 'handle_order',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error