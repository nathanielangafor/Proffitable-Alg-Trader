import time
import sys
from datetime import datetime
from multiprocessing import active_children, Process

# Append the 'Analysis/Technical' folder to path and import the needed module
sys.path.append('Analysis/Technical')
import indicators
# Append the 'Config Files' folder to path and import the needed module
sys.path.append('Config Files')
import config
# Append the 'Database' folder to path and import the needed module
sys.path.append('Database')
import database

def iterate(asset):
    """
    Update the data for the given asset.

    Parameters:
    asset (dict): A dictionary containing the asset data.
    """
    # Get the current time
    now = datetime.now() 
    # Set the start and end times for the stock market
    market_open = datetime(now.year, now.month, now.day, config.stock_market_hours['open_hour'], config.stock_market_hours['open_minute'])
    market_close = datetime(now.year, now.month, now.day, config.stock_market_hours['close_hour'], config.stock_market_hours['close_minute'])
    # Check if the current time is within the stock market hours or the asset is a cryptocurrency
    if (((market_open <= now <= market_close) and now.weekday() not in [5, 6]) and (asset['asset_type'] == 'stock')) or (asset['asset_type'] == 'crypto'):
        # Get the current price of the asset
        asset_price = indicators.price(asset['asset_name'], asset['asset_type'])['data']
        update = indicators.update(asset['initialized_asset'], asset['asset_name'], asset['asset_type'], asset_price, asset['timeframe'])
        if update['msg'] == 'success':
            # Update the asset price in the database
            database.update_by_value('assets', 'asset_id', f'{asset["asset_name"]}{asset["timeframe"]}', ['asset_price'], [str(asset_price)])
        if update['msg'] == 'success' and asset['initialized_asset'] == 'false':
            # Update the asset's initialization status in the database
            database.update_by_value('assets', 'asset_id', f'{asset["asset_name"]}{asset["timeframe"]}', ['initialized_asset'], ['true'])
        print(update, asset['initialized_asset'])

def main():
    while True:
        # Get all assets
        asset_list = config.get_assets()['data']
        # Get list of unfinished processes
        running_processes = [process for process in active_children()]
        # Get list of cancelled processes
        cancelled_processes = [process for process in running_processes if process.name not in [asset_list[asset]['asset_id'] for asset in asset_list]]
        # Cancel cancelled processes
        for process in cancelled_processes:
            process.terminate()
            config.delete_csv_file(process.name)
        # Isolate assets to be iterated over
        active_assets = [asset_list[asset] for asset in asset_list if asset_list[asset]['asset_id'] not in [process.name for process in running_processes]]
        # Iterate over the assets, once
        seen = []
        for active_asset in active_assets:
            # Check if asset is already being watched
            if f"{active_asset['asset_name']}{active_asset['timeframe']}" not in seen:
                # Append asset to the seen list
                seen.append(f"{active_asset['asset_name']}{active_asset['timeframe']}")
                # Create a new Process object
                queued_process = Process(target=iterate, name=active_asset['asset_id'], args=(active_asset,))
                # Start the process
                queued_process.start()
        # Wait before running next batch
        time.sleep(5)

if __name__ == '__main__': 
    main()