import json
import sys
import time
from datetime import datetime
from multiprocessing import active_children, Process
import time

# Append the 'Analysis/Technical' folder to path and import the needed module
sys.path.append('Analysis/Technical')
import indicators
# Append the 'Config Files' folder to path and import the needed module
sys.path.append('Config Files')
import config
# Append the 'Database' folder to path and import the needed module
sys.path.append('Database')
import database
# Append the 'Brokers' folder to path and import the needed module
sys.path.append('Brokers')
import orderManager

def make_decision(asset_data):
    api_key = asset_data['id'].split('-')[1]
    # Get time
    now = datetime.now() 
    human_readable_time = now.strftime('%Y-%m-%d %H:%M:%S')      
    # Initialize data_log dictionary
    data_log = {}
    data_log['asset_data'] = asset_data
    data_log['flag'] = 'sell'
    data_log['order_type'] = asset_data['last_action_order_type']
    data_log['check_time'] = human_readable_time
    # Continuously update data and calculate indicator values
    while True:
        # Periodically wait to not overload the server
        time.sleep(3)
        # Read data from file and get number of rows
        df = config.read_dataframe(config.generate_file_name(asset_data['asset_name'], asset_data['timeframe'])['data'])['data']
        # Get time
        now = datetime.now() 
        human_readable_time = now.strftime('%Y-%m-%d %H:%M:%S')        
        data_log['check_time'] = human_readable_time
        # Get current asset price and update data
        asset_price = indicators.db_price(asset_data['asset_name'])
        # Calculate EMA, and MACD direction
        assetEMA = indicators.calculate_ema_dema(df)['ema']
        # Set variables
        slippage_percent = asset_data['slippage_percent'] if asset_data['last_action_order_type'] == 'short' else asset_data['slippage_percent'] - (asset_data['slippage_percent'] * 2)
        take_profit_percent = asset_data['take_profit_percent'] if asset_data['last_action_order_type'] == 'long' else asset_data['take_profit_percent'] - (asset_data['take_profit_percent'] * 2)
        profit_target = ((100 + take_profit_percent) * asset_data['last_action_price']) / 100.0
        data_log['profit_target'] = profit_target
        # Check if the order is a short or long order
        if asset_data['last_action_order_type'] == 'short' and asset_price < profit_target:
            # calculate the slippage target
            slippage_target = ((100 + slippage_percent) * profit_target) / 100.0
            # Wait for the most profitable price
            while asset_price <= slippage_target:
                # update the profit target
                if asset_price <= profit_target:
                    profit_target = asset_price
                # calculate the new slippage target
                slippage_target = ((100 + slippage_percent) * profit_target) / 100.0
                # read the dataframe
                df = config.read_dataframe(config.generate_file_name(asset_data['asset_name'], asset_data['timeframe'])['data'])['data']
                # get the current asset price
                asset_price = indicators.db_price(asset_data['asset_name'])
                # sleep for 3 seconds
                time.sleep(3)
            # Update data_log and exit loop
            data_log['status'] = 0
            break
        if asset_data['last_action_order_type'] == 'long' and asset_price > profit_target:
            # calculate the slippage target
            slippage_target = ((100 + slippage_percent) * profit_target) / 100.0
            # Wait for the most profitable price
            while asset_price >= slippage_target:
                # update the profit target
                if asset_price >= profit_target:
                    profit_target = asset_price
                # calculate the new slippage target
                slippage_target = ((100 + slippage_percent) * profit_target) / 100.0
                # read the dataframe
                df = config.read_dataframe(config.generate_file_name(asset_data['asset_name'], asset_data['timeframe'])['data'])['data']
                # get the current asset price
                asset_price = indicators.db_price(asset_data['asset_name'])
                # sleep for 3 seconds
                time.sleep(3)
            # Update data_log and exit loop
            data_log['status'] = 0
            break
        # Check if the stop loss conditions are met
        if (
            (asset_data['last_action_order_type'] == 'long' and asset_price < assetEMA and asset_data['fundamental_gate'] == 'false') or 
            (asset_data['last_action_order_type'] == 'short' and asset_price >= assetEMA and asset_data['fundamental_gate'] == 'true')
        ):
            break
    # Update data_log with current asset price
    data_log['asset_price'] = asset_price
    if orderManager.handle_order(data_log)['msg'] == 'success':
        # Update status to success (0)  
        data_log['status'] = 0
        # Update the side, type, and action_price of the asset
        database.update_by_value(
            'assets', 'id', asset_data['id'], 
            ['asset_side', 'last_action_order_type', 'last_action_price'], 
            ['sell', asset_data['last_action_order_type'], asset_price]
        )
    else:
        # Update status to fail (1)  
        data_log['status'] = 1
    # Print data to logging file
    database.insert_record('signals', [None, api_key, str(data_log)])
    # Change asset variables
    database.update_by_value('assets', 'id', asset_data['id'], ['asset_side'], ['reset'])
    config.reset(df, asset_data['last_action_order_type'], asset_data['asset_name'], asset_data['timeframe'])
    database.update_by_value('assets', 'id', asset_data['id'], ['asset_side'], ['buy'])
    return data_log

def run(asset_data):
    """Continuously check the asset price and make a decision based on the updated data.

    Parameters:
    asset_data (dict): The asset data containing the asset name, type, order type, amount, multiplier, timeframe, take profit percent, action price, id, and slippage percent.
    """
    # Get the current time
    now = datetime.now() 
    # Set the start and end times for the stock market
    market_open = datetime(now.year, now.month, now.day, config.stock_market_hours['open_hour'], config.stock_market_hours['open_minute'])
    market_close = datetime(now.year, now.month, now.day, config.stock_market_hours['close_hour'], config.stock_market_hours['close_minute'])
    # Get asset type 
    asset_type = asset_data['asset_type']
    # Check if the current time is within the stock market hours or the asset is a cryptocurrency
    if ((market_open <= now <= market_close) and (asset_type == 'stock')) or (asset_type == 'crypto'):
        # Make a decision based on the updated data
        make_decision(asset_data)

def main(): 
    # Create loop to consistently check
    while True:
        # Get all assets
        asset_list = config.get_assets()['data']
        # Get list of unfinished processes
        running_processes = [process for process in active_children()]
        # Get list of cancelled processes
        cancelled_processes = [process for process in running_processes if process.name not in [asset_list[asset]['id'] for asset in asset_list]]
        # Cancel cancelled processes
        for process in cancelled_processes:
            process.terminate()
        # Isolate assets to be iterated over
        active_assets = [asset_list[asset] for asset in asset_list if asset_list[asset]['id'] not in [process.name for process in running_processes]]
        # Iterate over the assets
        for active_asset in active_assets:
            # Check if asset has been initialized by csvUpdater
            if active_asset['initialized_asset'] == 'true' and active_asset['asset_side'] == 'sell':
                # Create a new Process object
                queued_process = Process(target=run, name=active_asset['id'], args=(active_asset,))
                # Start the process
                queued_process.start()
        # Wait before running next batch
        time.sleep(10)

if __name__ == '__main__': 
    main()