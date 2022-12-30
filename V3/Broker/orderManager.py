import json
import websockets
import asyncio 
import pandas as pd
import sys
import time

# append the config file, utility and helper filepath to sys.path
sys.path.append('/Users/appleid/Desktop/Other Files/V3/Config Files')
sys.path.append('/Users/appleid/Desktop/Other Files/V3/Market Monitor')
sys.path.append('/Users/appleid/Desktop/Other Files/V3/Broker/Helper Functions')
import positionFunctions
import config
import indicators

async def place_order(asset, asset_type, flag, order_type, size, multiplier, price):
    """
    Send a request to place an order to the websocket server.
    
    Args:
    asset (str): The asset of the asset to place an order for.
    flag (int): The flag value to use for the order.
    order_type (str): The type of order to place, either 'long' or 'short'.
    size (int): The size of the order to place.
    multiplier (int): The multiplier to use for the order.
    price (float): The price to place the order at.
    
    Returns:
    str: The response from the websocket server.
    """
    if asset_type == 'crypto':
        async with websockets.connect('ws://localhost:8080/') as websocket:
            request = {
                "asset": asset,
                "flag": flag,
                "type": order_type,
                "tradeSize": size,
                'multiplier': multiplier,
                "price": price
            }
            # send request to websocket server to place order
            await websocket.send(json.dumps(request))
            # receive response
            response = await websocket.recv()
            return response

    if asset_type == 'stock':
        async with websockets.connect('ws://localhost:8080/') as websocket:
            request = {
                "asset": asset,
                "flag": flag,
                "type": order_type,
                "tradeSize": size,
                'multiplier': multiplier,
                "price": price
            }
            # send request to websocket server to place order
            await websocket.send(json.dumps(request))
            # receive response
            response = await websocket.recv()
            return response

async def handle_sell(asset, asset_type, flag, order_type, size, multiplier, price):
    # Initialize logs dictionary
    logs = {}

    # Continuously update data and calculate indicator values
    while True:
        # Read data from file and get number of rows
        df = indicators.read_dataframe(config.generate_file_name(asset))
        num_rows = df.shape[0]

        # Get current asset price and update data
        asset_price = indicators.price(asset, asset_type)
        indicators.update(False, asset, asset_type, asset_price)

        # Calculate ATR, EMA, and MACD direction
        assetATR = indicators.calculateATR(df)['atr']
        assetEMA = indicators.calculateEMAandDEMA(df)['ema'] + assetATR
        assetMACDDirection = indicators.calculateMACD(df)['macdDirection']

        # Check if the order type is short
        if order_type == 'short':
            # Calculate profit target
            profit_target = ((100 - config.take_profit_percents[asset_type]) * price) / 100.0
            logs['profit_target'] = profit_target

            # Check if the asset price has dropped below the profit target
            if asset_price < profit_target:
                # Wait for the most profitable price
                while assetMACDDirection == 'short' and profit_target:
                    df = indicators.read_dataframe(config.generate_file_name(asset))
                    num_rows = df.shape[0]
                    asset_price = indicators.price(asset, asset_type)
                    indicators.update(False, asset, asset_type, asset_price)
                    assetMACDDirection = indicators.calculateMACD(df)['macdDirection']

                # Update logs and exit loop
                logs['status'] = 0
                break

            # Check if the stop loss conditions are met
            if asset_price > assetEMA + (assetATR * 2):
                # Update logs and exit loop
                logs['status'] = 1
                break

        # Check if the order type is long
        if order_type == 'long':
            # Calculate profit target
            profit_target = ((100 + config.take_profit_percents[asset_type]) * price) / 100.0
            logs['profit_target'] = profit_target

            # Check if the asset price has increased above the profit target
            if asset_price > profit_target:
                # Wait for the most profitable price
                while assetMACDDirection == 'long' and asset_price > profit_target / 100.0:
                    df = indicators.read_dataframe(config.generate_file_name(asset))
                    num_rows = df.shape[0]
                    asset_price = indicators.price(asset, asset_type)
                    indicators.update(False, asset, asset_type, asset_price)
                    assetMACDDirection = indicators.calculateMACD(df)['macdDirection']

                # Update logs and exit loop
                logs['status'] = 0
                break

            # Check if the stop loss conditions are met
            if asset_price < assetEMA - (assetATR * 2):
                # Update logs and exit loop
                logs['status'] = 1
                break

    # Update logs with current asset price
    logs['asset_price'] = asset_price

    # Place a sell order at the current asset price
    response = await place_order(asset, asset_type, flag, order_type, size, multiplier, asset_price)
    if response != 'SUCCESS':
        logs['status'] = 2
    return logs

async def handle_buy(asset, asset_type, flag, order_type, size, multiplier, price):
    # Place a buy order
    data = await place_order(asset, asset_type, flag, order_type, size, multiplier, price)
    # Set status based on response from place_order function
    if data == 'SUCCESS':
        status = 0
    else:
        status = 2

    # Return buy data as a dictionary
    return {
        'flag': flag,
        'price': price,
        'status': status
    }

async def handle_order(asset, asset_type, order_type, multiplier, size, price):
    print(asset, asset_type, order_type, multiplier, size, price)
    # Initialize logs dictionary
    logs = {}

    # Add asset and order type to logs
    logs['asset'] = asset
    logs['asset_type'] = config.assets[asset]
    logs['order_type'] = order_type
    logs['sell_data'] = {}

    # Get pending orders and position summary for wallet and asset
    if asset_type == 'crypto':
        pending_orders = positionFunctions.get_pending_mux_orders(config.crypto['my_wallet'], config.crypto['asset_ids'][asset]['id'])
        position_summary = positionFunctions.get_position_summary(config.crypto['my_wallet'], config.crypto['asset_ids'][asset]['id'])
        buy_flag = 128
        sell_flag = 32
    if asset_type == 'stock':
        pending_orders = []
        position_summary = {'Long': {'remaining_position': 0}}
        buy_flag = 'buy'
        sell_flag = 'sell'

    # Check if the order should be placed
    if len(pending_orders) == 0:
        if (
            (asset_type == 'crypto' and order_type == 'short' and position_summary['Shorts']['remaining_position'] == 0)
            or  
            (asset_type == 'crypto' and order_type == 'long' and position_summary['Long']['remaining_position'] == 0)
            or 
            (asset_type == 'stock' and order_type == 'long' and position_summary['Long']['remaining_position'] == 0)
            ):
            # Place a buy order and check if it was successful
            buy_response = await handle_buy(asset, asset_type, buy_flag, order_type, size, multiplier, price)
            logs['buy_data'] = buy_response
            if buy_response['status'] == 0:
                # Place a sell order if the buy order was successful
                sell_response = await handle_sell(asset, asset_type, sell_flag, order_type, size, multiplier, price)
                logs['sell_data'] = sell_response

    with open(config.loggingFile, 'a') as f:
        f.write(str(logs) + '\n')
    return logs

# 0 - success
# 1 - success but not as planned
# 2 - failed