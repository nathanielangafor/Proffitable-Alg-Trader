import asyncio
import time
import pandas as pd
import concurrent.futures
import json
from datetime import datetime

# import custom modules
import indicators
import gates

# append path to sys.path to allow import from these directories
import sys
sys.path.append('/Users/appleid/Desktop/Other Files/V3/Broker')
import orderManager
sys.path.append('/Users/appleid/Desktop/Other Files/V3/Config Files')
import config

def makeDecision(asset, asset_type):
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
    logs['asset_type'] = config.assets[asset]
    logs['asset_price'] = asset_price
    logs['order_type'] = order_type
    logs['check_time'] = human_readable_time
    logs['market_sentiment'] = gates.fear_and_greed_gate(asset_type)
    gates_dictionary = {}

    if order_type == 'long':
        # check if any of the gate functions return false for long trade
        for gate in gate_set1:
            if gate.__name__ not in config.assets[asset]['gate_bypass']:
                gate_data = gate(df)
                buy = False if gate_data['long'] == False else buy
                gates_dictionary[gate.__name__] = {
                    'output': gate_data['long'],
                    'data': gate_data['data']
                }

        for gate in gate_set2:
            if gate.__name__ not in config.assets[asset]['gate_bypass']:
                gate_data = gate(df, asset_price)
                buy = False if gate_data['long'] == False else buy
                gates_dictionary[gate.__name__] = {
                    'output': gate_data['long'],
                    'data': gate_data['data']
                }

    if order_type == 'short':
        # check if any of the gate functions return false for short trade
        for gate in gate_set1:
            if gate.__name__ not in config.assets[asset]['gate_bypass']:
                gate_data = gate(df)
                buy = False if gate_data['short'] == False else buy
                gates_dictionary[gate.__name__] = {
                    'output': gate_data['short'],
                    'data': gate_data['data']
                }

        for gate in gate_set2:
            if gate.__name__ not in config.assets[asset]['gate_bypass']:
                gate_data = gate(df, asset_price)
                buy = False if gate_data['short'] == False else buy
                gates_dictionary[gate.__name__] = {
                    'output': gate_data['short'],
                    'data': gate_data['data']
                }

    logs['gates'] = gates_dictionary
    logs['decision'] = buy

    # confirm position can be opened. (long crypto, short crypto, long stock)
    if buy and not (logs['order_type'] == 'short' and logs['asset_type'] == 'stock'):
        # print data to logging file
        if logs['decision'] == True:
            with open(config.loggingFile, 'a') as f:
                f.write(str(logs) + '\n')
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

def run(asset):
    """
    Continuously check the asset price and make a decision based on the updated data.

    Parameters:
    asset (str): The asset to be monitored.
    """
    # Initialize the asset price
    price = 0
    
    while True:
        # Get the current time
        now = datetime.now()

        # Set the start and end times for the stock market
        market_open = datetime(now.year, now.month, now.day, 9, 30)
        market_close = datetime(now.year, now.month, now.day, 16)

        # Check if the current time is within the stock market hours or the asset is a cryptocurrency
        if ((market_open <= now <= market_close) and (config.assets[asset]['asset_type'] == 'stock')) or (config.assets[asset]['asset_type'] == 'crypto'):
            # Get the current asset price
            asset_price = indicators.price(asset, config.assets[asset]['asset_type'])
            
            # Check if the asset price has changed
            if price != asset_price:
                # Update the asset data and make a decision based on the updated data
                indicators.update(price == 0, asset, config.assets[asset]['asset_type'], asset_price)
                logs = makeDecision(asset, config.assets[asset]['asset_type'])
                print(json.dumps(logs, indent=4))
                
                # Update the asset price
                price = asset_price

# We can use a with statement to ensure threads are cleaned up promptly
with concurrent.futures.ThreadPoolExecutor(max_workers=len(config.assets.keys())) as executor:
    # Start the load operations and mark each future with its URL
    runner = {executor.submit(run, asset): asset for asset in config.assets.keys()}
    for future in concurrent.futures.as_completed(runner):
        data = future.result()
