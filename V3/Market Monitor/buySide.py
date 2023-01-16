import sys
import time
from datetime import datetime
from multiprocessing import active_children, Process
import time

# Append the 'Analysis' folder to path and import the needed module
sys.path.append('Analysis')
import gates
# Append the 'Config Files' folder to path and import the needed module
sys.path.append('Config Files')
import config
# Append the 'Database' folder to path and import the needed module
sys.path.append('Database')
import database
# Append the 'Brokers' folder to path and import the needed module
sys.path.append('Brokers')
import orderManager

def make_decision(asset_data, gate_criteria):
    """Determine whether or not to make a trade based on the output of various gate functions.
    
    Parameters:
    asset_data (str): The data of the asset being traded.
    gate_criteria (str): The criteria for the gate check.

    Returns:
    bool: A flag indicating whether or not to make the trade.
    """
    # Read asset data from CSV file
    df = config.read_dataframe(config.generate_file_name(asset_data['asset_name'], asset_data['timeframe'])['data'])['data']
    # Get time
    now = datetime.now() 
    human_readable_time = now.strftime('%Y-%m-%d %H:%M:%S')        
    # List of gate functions to check for trades
    gate_set1 = []
    gate_set2 = []
    # Get direction of trade attempt
    order_type = gates.direction_gate(df)['attempting']
    # Assume that buy is true until proven otherwise
    buy = True
    # Log data for the final report
    data_log = {}
    data_log['asset_data'] = asset_data
    data_log['flag'] = 'buy'
    data_log['order_type'] = order_type
    data_log['check_time'] = human_readable_time
    # Initialize the gates dictionary which will be filled with gate outputs
    gates_dictionary = {}
    # Check if any of the gate functions return false for the specified order type
    for gate in gate_set1:
        if gate.__name__ not in asset_data['gate_bypass']:
            gate_data = gate(df, gate_criteria[gate.__name__])
            buy = False if gate_data[order_type] == False else buy
            gates_dictionary[gate.__name__] = {
                'output': gate_data[order_type],
                'data': gate_data['data']
            }
    for gate in gate_set2:
        if gate.__name__ not in asset_data['gate_bypass']:
            gate_data = gate(df, asset_data['asset_price'], gate_criteria[gate.__name__])
            buy = False if gate_data[order_type] == False else buy
            gates_dictionary[gate.__name__] = {
                'output': gate_data[order_type],
                'data': gate_data['data']
            }
    # Update iteration data_log
    data_log['gates'] = gates_dictionary
    data_log['decision'] = buy
    # Confirm that position can be opened (long crypto, short crypto, long stock)
    if buy and not (order_type == 'short' and asset_data['asset_type'] == 'stock'):
        if orderManager.handle_order(data_log)['msg'] == 'success':
            # Update status to success (0)  
            data_log['status'] = 0
            # Update the side, type, and action_price of the asset
            database.update_by_value(
                'assets', 'id', asset_data['id'], 
                ['asset_side', 'last_action_order_type', 'last_action_price'], 
                ['sell', data_log['order_type'], str(asset_data['asset_price'])]
            )
        else:
            # Update status to fail (1)  
            data_log['status'] = 1
            # Update the side of the asset and reset
            database.update_by_value('assets', 'id', asset_data['id'], ['asset_side'], ['reset'])
            config.reset(df, asset_data['last_action_order_type'], asset_data['asset_name'], asset_data['timeframe'])
            database.update_by_value('assets', 'id', asset_data['id'], ['asset_side'], ['buy'])
        # Print data to logging file
        database.insert_record('signals', [None, asset_data['id'].split('-')[1], str(data_log)])
    # Update csv column to reflect latest iteration
    database.update_by_value('assets', 'id', asset_data['id'], ['last_iteration'], [time.ctime(time.time())])
    return data_log

def run(asset_data):
    """Continuously check the asset price and make a decision based on the updated data.

    Parameters:
    asset (str): The asset to be monitored.
    """
    # Get the current time
    now = datetime.now() 
    # Set the start and end times for the stock market
    market_open = datetime(now.year, now.month, now.day, config.stock_market_hours['open_hour'], config.stock_market_hours['open_minute'])
    market_close = datetime(now.year, now.month, now.day, config.stock_market_hours['close_hour'], config.stock_market_hours['close_minute'])
    # Check if the current time is within the stock market hours or the asset is a cryptocurrency
    if (((market_open <= now <= market_close) and now.weekday() not in [5, 6]) and (asset_data['asset_type'] == 'stock')) or (asset_data['asset_type'] == 'crypto'):
        # Update the asset data and make a decision based on the updated data
        make_decision(asset_data, config.gate_settings)

def db_initializer(assets, signals, users, errors, admins):
    """Initialize the specified database tables.
    
    Parameters:
    tradeable_assets: Initialize the tradable_assets table.
    assets: Initialize the assets table.
    signals: Initialize the signals table.
    users: Initialize the users table.
    errors: Initialize the errors table.
    admins: Initialize the admins table.
    """
    # Wipe tables if requested
    if assets:
        config.initialize_assets_table()
    if signals:
        config.initialize_signals_table()
    if users:
        config.initialize_users_table()
    if errors:
        config.initialize_errors_table()
    if admins:
        config.initialize_admins()

def main():
    # Purify the database
    db_initializer(True, True, True, True, True)
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
            if active_asset['initialized_asset'] == 'true' and active_asset['asset_side'] == 'buy':
                # Create a new Process object
                queued_process = Process(target=run, name=active_asset['id'], args=(active_asset,))
                # Start the process
                queued_process.start()
        # Wait before running next batch
        time.sleep(10)

if __name__ == '__main__': 
    main()