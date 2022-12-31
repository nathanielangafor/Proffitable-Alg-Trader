import asyncio
from multiprocessing import Process
import time
import json
from datetime import datetime
from multiprocessing import active_children

# import custom modules
import indicators
import gates

# append path to sys.path to allow import from these directories
import sys
sys.path.append('../Broker')
import orderManager
sys.path.append('../Config Files')
import config
sys.path.append('../Database')
import database

def makeDecision(asset, asset_type, asset_data):
    """
    Determine whether or not to make a trade based on the output of various gate functions.
    """
    # read asset data from CSV file
    df = indicators.read_dataframe(config.generate_file_name(asset))
    num_rows = df.shape[0]
    # get time
    human_readable_time = df['datetime'][num_rows - 1]
    # get last asset price
    asset_price = indicators.price(asset, asset_type)
    # list of gate functions to check for trades
    gate_set1 = [gates.macd_gate, gates.rsi_gate, gates.cci_gate, gates.trend_gate, gates.momentum_gate]
    gate_set2 = [gates.ichimoku_gate, gates.ema_gate, gates.bollinger_gate, gates.cloud_gate]

    # get direction of trade attempt
    order_type = gates.direction_gate(df)['attempting']
    # get amount of trade
    size = config.default_trade_size
    # assume that buy is true until proven otherwise
    buy = True

    logs = {}
    logs['asset'] = asset
    logs['asset_type'] = config.get_assets()[asset]
    logs['asset_price'] = asset_price
    logs['order_type'] = order_type
    logs['check_time'] = human_readable_time
    try:
        logs['market_sentiment'] = gates.fear_and_greed_gate(asset_type)
    except:
        pass
    gates_dictionary = {}

    if order_type == 'long':
        # check if any of the gate functions return false for long trade
        for gate in gate_set1:
            if gate.__name__ not in config.get_assets()[asset]['gate_bypass']:
                gate_data = gate(df, asset_data[gate.__name__])
                buy = False if gate_data['long'] == False else buy
                gates_dictionary[gate.__name__] = {
                    'output': gate_data['long'],
                    'data': gate_data['data']
                }

        for gate in gate_set2:
            if gate.__name__ not in config.get_assets()[asset]['gate_bypass']:
                gate_data = gate(df, asset_price, asset_data[gate.__name__])
                buy = False if gate_data['long'] == False else buy
                gates_dictionary[gate.__name__] = {
                    'output': gate_data['long'],
                    'data': gate_data['data']
                }

    if order_type == 'short' and asset_type != 'stock':
        # check if any of the gate functions return false for short trade
        for gate in gate_set1:
            if gate.__name__ not in config.get_assets()[asset]['gate_bypass']:
                gate_data = gate(df, asset_data[gate.__name__])
                buy = False if gate_data['short'] == False else buy
                gates_dictionary[gate.__name__] = {
                    'output': gate_data['short'],
                    'data': gate_data['data']
                }

        for gate in gate_set2:
            if gate.__name__ not in config.get_assets()[asset]['gate_bypass']:
                gate_data = gate(df, asset_price, asset_data[gate.__name__])
                buy = False if gate_data['short'] == False else buy
                gates_dictionary[gate.__name__] = {
                    'output': gate_data['short'],
                    'data': gate_data['data']
                }
 
    df.to_csv(config.generate_file_name(asset), index=False)
    logs['gates'] = gates_dictionary
    logs['decision'] = buy

    # confirm position can be opened. (long crypto, short crypto, long stock)
    if buy and not (logs['order_type'] == 'short' and logs['asset_type'] == 'stock'):
        # print data to logging file
        if logs['decision'] == True:
            database.insert_record('signals', str(logs))
        # get current asset price
        asset_price = indicators.price(asset, asset_type)
        # run order handling function asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        coroutine = orderManager.handle_order(asset, asset_type, order_type, config.multiplier, size, asset_price)
        loop.run_until_complete(coroutine) 

        if order_type == 'long':
            while gates.direction_gate(df)['attempting'] == 'long':
                indicators.update(False, asset, asset_type, asset_price)
                df = indicators.read_dataframe(config.generate_file_name(asset))

        if order_type == 'short':
            while gates.direction_gate(df)['attempting'] == 'short':
                indicators.update(False, asset, asset_type, asset_price)
                df = indicators.read_dataframe(config.generate_file_name(asset))

    return logs

def run(asset, init):
    """
    Continuously check the asset price and make a decision based on the updated data.

    Parameters:
    asset (str): The asset to be monitored.
    """
    # Get the current time
    now = datetime.now()

    # Set the start and end times for the stock market
    market_open = datetime(now.year, now.month, now.day, 9, 30)
    market_close = datetime(now.year, now.month, now.day, 16)

    # Check if the current time is within the stock market hours or the asset is a cryptocurrency
    if ((market_open <= now <= market_close) and (config.get_assets()[asset]['asset_type'] == 'stock')) or (config.get_assets()[asset]['asset_type'] == 'crypto'):            # Get the current asset price
        asset_price = indicators.price(asset, config.get_assets()[asset]['asset_type'])
        
        # Update the asset data and make a decision based on the updated data
        indicators.update(init, asset, config.get_assets()[asset]['asset_type'], asset_price)
        logs = makeDecision(asset, config.get_assets()[asset]['asset_type'], config.gate_settings)
        print(json.dumps(logs, indent=4))

if __name__ == '__main__': 
    # Initialize the database
    config.initialize()   
    # Track which assets have been initialized
    initialized = []
   
    # Create loop to consistently check
    while True:
        # Get list of unfinished processes
        running_processes = [process for process in active_children()]
        # Get list of cancelled processes
        cancelled_processes = [process for process in running_processes if process.name not in config.get_assets()]
        # Cancel cancelled processes
        for process in cancelled_processes:
            process.terminate()
        # Isolate assets to be iterated over
        assets = [asset for asset in config.get_assets() if asset not in [process.name for process in running_processes]]
        # Iterate over the assets
        for asset in assets:
            # Check if asset asset data has been initialized, otherwise initialize and append to liist
            if asset in initialized:
                init = False
            else:
                initialized.append(asset)
                init = True
            # Create a new Process object
            queued_process = Process(target=run, name=asset, args=(asset, init,))
            # Start the process
            queued_process.start()

        # Wait before running next batch
        time.sleep(10)