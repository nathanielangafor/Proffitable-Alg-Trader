from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import sys
import uvicorn
import cloudscraper
import subprocess
import os

# Append the 'Config Files' folder to path and import the needed module
sys.path.append('Config Files')
import config
# Append the 'Analysis/Technical' folder to path and import the needed module
sys.path.append('Analysis/Technical')
import indicators
# Append the 'Database' folder to path and import the needed module
sys.path.append('Database')
import recommendations

scraper = cloudscraper.create_scraper()

description = """
    Backend server for the VAM Network. 
    Bug bounty program coming soon.
"""

tags_metadata = [
    {"name": "Asset Management"},
    {"name": "Signal Management"},
    {"name": "Global Request"},
    {"name": "System Health Check"},
    {"name": "User Management"}
]

app = FastAPI(
    title="VAM Network API",
    description=description,
    version="0.1",
    terms_of_service="",
    contact={
        "name": "Nathaniel Angafor",
        "url": "https://github.com/nathanielangafor",
        "email": "nangafor@u.rochester.edu",
    },
    openapi_url = "/Data-Schema",
    openapi_tags=tags_metadata
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["System Health Check"])
def read_root():
    """
    The root endpoint of the API. Returns a simple "Hello World" message.
    """
    return {"Hello": "World"}

@app.get("/system_diagnostic/{api_key}", tags=["System Health Check", "Administrator Only"])
def system_query(api_key):
    """
    Performs a diagnostic check of the system.

    Parameters:
    api_key (str): API key used to authenticate the request.

    Returns:
    A dictionary with two keys: "data" and "msg". "data" is a list containing
        the results of the diagnostic check. "msg" is a string indicating the status
        of the request ("success" or "error").
    """
    if api_key in config.get_all_admin_api_keys():
        return config.success_message(True)
    else:
        return config.error_message('Authentication error.')

@app.post("/run_command", tags=["System Health Check", "Administrator Only"])
def system_query(
        command: str = Form(...),
        api_key: str = Form(...)
    ):
    """
    Runs a command in the system shell.

    Parameters:
    command (str): The command to be run in the system shell.
    api_key (str): API key used to authenticate the request.

    Returns:
    A dictionary with two keys: "data" and "msg". "data" is a list containing
        the output of the command. "msg" is a string indicating the status
        of the request ("success" or "error").
    """
    if api_key in config.get_all_admin_api_keys():
        try:
            return config.success_message(subprocess.getoutput(command))
        except  Exception as e:
            return config.error_message(str(e))
    else:
        return config.error_message('Authentication error.')

@app.post("/add_asset", tags=["Asset Management"])
def database_modification(
        api_key: str = Form(...), 
        asset_name: str = Form(...), 
        asset_type: str = Form(...), 
        amount: float = Form(...),
        multiplier: float = Form(...),
        timeframe: str = Form(...),
        slippage_percent: float = Form(...),
        take_profit_percent: float = Form(...),
        broker_direction: str = Form(...),
        gate_bypass: str = Form(None),
    ):
    """
    Adds an asset to the database.

    Parameters:
    api_key (str): The api_key of the user adding the asset.
    asset_name (str): The name of the asset.
    asset_type (str): The type of the asset (e.g. "stock", "crypto").
    amount (float): The amount of the asset to be added.
    multiplier (float): The multiplier for the asset.
    timeframe (str): The timeframe for the asset.
    slippage_percent (float): The slippage percent for the asset.
    take_profit_percent (float): The take profit percent for the asset.
    gate_bypass (str): A flag indicating whether to bypass the gate.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        a dictionary with the asset name as the key and a string as the value.
        "status" is a string indicating the status of the request ("success" or "error").
    """
    # Check if inputs are valid
    sanitizer_result = config.sanitize_inputs(asset_name=asset_name, asset_type=asset_type, amount=amount, multiplier=multiplier, slippage_percent=slippage_percent, take_profit_percent=take_profit_percent, timeframe=timeframe, broker_direction=broker_direction, gate_bypass=gate_bypass)
    if sanitizer_result['msg'] == 'success':
        # Check if the asset's price is less than the definition of a penny stock
        asset_price = indicators.price(sanitizer_result['data']['asset_name'], sanitizer_result['data']['asset_type'])
        if asset_price['msg'] == 'success':
            if indicators.price(sanitizer_result['data']['asset_name'], sanitizer_result['data']['asset_type'])['data'] < config.penny_stock_definition:
                return config.error_message(f"{sanitizer_result['data']['asset_name']} is less than the system classification of a penny stock / crypto ({config.penny_stock_definition}). Please add a different asset.") 
            else:  
                # Check if multiplier is greater tha nor equal to 1
                if sanitizer_result['data']['multiplier'] >= 1:
                    # Check if asset is tradable
                    if (sanitizer_result['data']['multiplier'] == 1 and sanitizer_result['data']['asset_name'] in config.leveragable_crypto + config.non_leveragable_crypto + config.get_all_stocks()) or (sanitizer_result['data']['multiplier'] > 1 and sanitizer_result['data']['asset_name'] in config.leveragable_crypto):
                        data = config.add_asset(api_key, sanitizer_result['data']['asset_name'], sanitizer_result['data']['asset_type'], sanitizer_result['data']['amount'], sanitizer_result['data']['multiplier'], sanitizer_result['data']['timeframe'], sanitizer_result['data']['slippage_percent'], sanitizer_result['data']['take_profit_percent'], sanitizer_result['data']['gate_bypass'])
                        if data['msg'] == 'success': 
                            return config.success_message(f"{sanitizer_result['data']['asset_name']} added")
                        else:
                            return config.error_message(data['data'])
                    else:
                        return config.error_message('Asset is not tradable.')
                else:
                    return config.error_message('Can not have a multiplier less than 1.')
        else:
            return config.error_message('Unable to fetch asset price.')
    else:
        return config.error_message("Inputs. did not pass the sanitizer check. Please check all fields before submitting.")

@app.post("/remove_asset", tags=["Asset Management"])
def database_modification(
        api_key: str = Form(...),
        asset_name: str = Form(...),
        timeframe: str = Form(...),
    ):
    """
    Removes an asset from the database.

    Parameters:
    api_key: (str): the api key of the user who owns the asset entry.
    asset_name (str): The name of the asset to be removed.
    timeframe (str): The timeframe for the asset.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        a dictionary with the asset name as the key and a string as the value.
        "status" is a string indicating the status of the request ("success" or "error").
    """
        # Check if inputs are valid
    sanitizer_result = config.sanitize_inputs(asset_name=asset_name, timeframe=timeframe)
    if sanitizer_result['msg'] == 'success':
        data = config.remove_asset(api_key, sanitizer_result['data']['asset_name'], sanitizer_result['data']['timeframe'])
        if data['msg'] == 'success': 
            return config.success_message(f'{asset_name} removed')
        else:
            return config.error_message(data['data'])
    else:
        return config.error_message("Inputs. did not pass the sanitizer check. Please check all fields before submitting.")

@app.get("/get_all_assets/{api_key}", tags=["Asset Management", "Administrator Only"])
def database_query(api_key):
    """
    Retrieves a list of all assets in the database.

    Parameters:
    api_key (str): API key used to authenticate the request.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        dictionaries with the asset names and their associated data. "status" is a
        string indicating the status of the request ("success" or "error").
    """
    if api_key in config.get_all_admin_api_keys():
        data = config.get_assets()
        if data['msg'] == 'success': 
            return config.success_message(data['data'])
        else:
            return config.error_message(data['data'])
    else:
        return config.error_message('Authentication error.')

@app.get("/get_asset/{api_key}", tags=["Asset Management"])
def database_query(api_key):
    """
    Retrieves a list of all assets in the database.

    Parameters:
    api_key (str): API key used to authenticate the request.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        dictionaries with the asset names and their associated data. "status" is a
        string indicating the status of the request ("success" or "error").
    """
    data = config.get_asset(api_key)
    if data['msg'] == 'success': 
        return config.success_message(data['data'])
    else:
        return config.error_message(data['data'])

@app.get("/get_all_signals/{api_key}", tags=["Signal Management", "Administrator Only"])
def database_query(api_key):
    """
    Retrieves a list of all signals in the database.

    Parameters:
    api_key (str): API key used to authenticate the request.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        dictionaries with the signal data. "status" is a string indicating the status
        of the request ("success" or "error").
    """
    if api_key in config.get_all_admin_api_keys():
        data = config.get_signals()
        if data['msg'] == 'success': 
            return config.success_message(data['data'])
        else:
            return config.error_message(data['data'])
    else:
        return config.error_message('Authentication error.')

@app.get("/get_signal/{api_key}", tags=["Signal Management"])
def database_query(api_key):
    """
    Retrieves a list of slect signals in the database.

    Parameters:
    api_key (str): API key used to authenticate the request.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        dictionaries with the signal data. "status" is a string indicating the status
        of the request ("success" or "error").
    """
    data = config.get_signal(api_key)
    if data['msg'] == 'success': 
        return config.success_message(data['data'])
    else:
        return config.error_message(data['data'])

@app.get("/crypto_recommendations", tags=["Global Request"])
def information_query():
    """
    Retrieves a list of cryptocurrency recommendations.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        the recommended cryptocurrencies. "status" is a string indicating the status
        of the request ("success" or "error").
    """
    data = recommendations.get_cryptos()
    if data['msg'] == 'success': 
        return config.success_message(data['data'])
    else:
        return config.error_message(data['data'])

@app.get("/stock_recommendations/{data}", tags=["Global Request"])
def information_query(data):
    """
    Retrieves a list of stock recommendations based on given filters.

    Parameters:
    data (str): A string containing the filters for the recommendations. The string should be formatted as follows:
        "min_volume=X&min_price=Y&min_sector_average=Z&marketcap_min=A&marketcap_max=B", where X, Y, Z, A, and B
        are values for the respective filters.

    Returns:
    A dictionary with two keys: "data" and "msg". "data" is a list containing
        the recommended stocks. "msg" is a string indicating the status
        of the request ("success" or "error").
    """
    data = data.lower()
    try:
        min_volume = float(data.split('min_volume=')[1].split('&')[0])
        min_price = float(data.split('min_price=')[1].split('&')[0])
        min_sector_average = float(data.split('min_sector_average=')[1].split('&')[0])
        marketcap_min = float(data.split('marketcap_min=')[1].split('&')[0])
        marketcap_max = float(data.split('marketcap_max=')[1].split('&')[0])
    except  Exception as e:
        return config.error_message(str(e))
    data = recommendations.get_stocks(min_volume, min_price, min_sector_average, marketcap_min, marketcap_max)
    if data['msg'] == 'success': 
        return config.success_message(data['data'])
    else:
        return config.error_message(data['data'])

@app.post("/add_user", tags=["User Management"])
def database_modification(
        email: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
    ):
    """
    Adds a new user to the system.

    Parameters:
    email (str): Email address of the new user.
    username (str): Desired username of the new user.
    password (str): Desired password of the new user.

    Returns:
    A dictionary with two keys: "data" and "msg". "data" is a string containing
        a message indicating the result of the operation. "msg" is a string indicating
        the status of the request ("success" or "error").
    """
    sanitizer_result = config.sanitize_inputs(email=email, username=username)
    priviledge = '1'
    data = config.add_user(sanitizer_result['data']['email'], sanitizer_result['data']['username'], password, priviledge)
    if data['msg'] == 'success': 
        return config.success_message(data['data'])
    else:
        return config.error_message(data['data'])

@app.post("/remove_user", tags=["User Management"])
def database_modification(
        api_key: str = Form(...),
    ):
    """
    Removes a user from the system.

    Parameters:
    api_key (str): API key of the user to be removed.

    Returns:
    A dictionary with two keys: "data" and "msg". "data" is a string containing
        a message indicating the result of the operation. "msg" is a string indicating
        the status of the request ("success" or "error").
    """
    data = config.remove_user(api_key)
    if data['msg'] == 'success': 
        return config.success_message(data['data'])
    else:
        return config.error_message(data['data'])

@app.get("/get_all_users/{api_key}", tags=["User Management", "Administrator Only"])
def database_query(api_key):
    """
    Retrieves a list of all users in the database.
    
    Parameters:
    api_key (str): API key used to authenticate the request.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        dictionaries with the asset names and their associated data. "status" is a
        string indicating the status of the request ("success" or "error").
    """
    if api_key in config.get_all_admin_api_keys():
        data = config.get_users()
        if data['msg'] == 'success': 
            return config.success_message(data['data'])
        else:
            return config.error_message(data['data'])
    else:
        return config.error_message('Authentication error.')

@app.get("/get_user/{api_key}", tags=["User Management"])
def database_query(api_key):
    """
    Retrieves a user from the database.
    
    Parameters:
    api_key (str): API key used to authenticate the request.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        dictionaries with the asset names and their associated data. "status" is a
        string indicating the status of the request ("success" or "error").
    """
    if api_key in config.get_all_admin_api_keys():
        data = config.get_user(api_key)
        if data['msg'] == 'success': 
            return config.success_message(data['data'])
        else:
            return config.error_message(data['data'])
    else:
        return config.error_message('Authentication error.')

@app.get("/get_all_errors/{api_key}", tags=["User Management", "Administrator Only"])
def database_query(api_key):
    """
    Retrieves a list of all errors in the database.
    
    Parameters:
    api_key (str): API key used to authenticate the request.

    Returns:
    A dictionary with two keys: "data" and "status". "data" contains
        dictionaries with the errors and their associated data. "status" is a
        string indicating the status of the request ("success" or "error").
    """
    if api_key in config.get_all_admin_api_keys():
        data = config.get_errors()
        if data['msg'] == 'success': 
            return config.success_message(data['data'])
        else:
            return config.error_message(data['data'])
    else:
        return config.error_message('Authentication error.')

@app.post("/set_discord_config", tags=["User Management"])
def database_modification(
        api_key: str = Form(...),
        discord_channel: str = Form(...),
    ):
    """
    Sets the Discord channel for system reports for a specific user.

    Parameters:
    api_key (str): API key of the user whose Discord channel is being set.
    discord_channel (str): The Discord channel to be set for system reports.

    Returns:
    A dictionary with two keys: "data" and "msg". "data" is a string containing
        a message indicating the result of the operation. "msg" is a string indicating
        the status of the request ("success" or "error").
    """
    data = config.update_discord_channel(api_key, discord_channel)
    if data['msg'] == 'success': 
        return config.success_message(data['data'])
    else:
        return config.error_message(data['data'])

@app.post("/set_defi_config", tags=["User Management"])
def database_modification(
        api_key: str = Form(...),
        wss_node: str = Form(...),
        mnemonic: str = Form(...),
        wallet_address: str = Form(...),
    ):
    """
    Sets the DeFi configuration for a specific user.

    Parameters:
    api_key (str): API key of the user whose DeFi configuration is being set.
    wss_node (str): WebSocket node used for connecting to the DeFi platform.
    mnemonic (str): Mnemonic phrase used for generating the user's DeFi wallet.
    wallet_address (str): Address of the user's DeFi wallet.

    Returns:
    A dictionary with two keys: "data" and "msg". "data" is a string containing
        a message indicating the result of the operation. "msg" is a string indicating
        the status of the request ("success" or "error").
    """
    data = config.update_defi_config(api_key, wss_node, mnemonic, wallet_address)
    if data['msg'] == 'success': 
        return config.success_message(data['data'])
    else:
        return config.error_message(data['data'])

@app.post("/set_robinhood_config", tags=["User Management"])
def database_modificationn(
        api_key: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
    ):
    """
    Sets the Robinhood configuration for a specific user.

    Parameters:
    api_key (str): API key of the user whose Robinhood configuration is being set.
    username (str): Robinhood username for the user.
    password (str): Robinhood password for the user.

    Returns:
    A dictionary with two keys: "data" and "msg". "data" is a string containing
        a message indicating the result of the operation. "msg" is a string indicating
        the status of the request ("success" or "error").
    """
    data = config.update_robinhood_config(api_key, username, password)
    if data['msg'] == 'success': 
        return config.success_message(data['data'])
    else:
        return config.error_message(data['data'])
        
if __name__ == '__main__': 
    os.system(f"kill -9 $(lsof -ti:{config.fastapi_port})")
    os.system(f"kill -9 $(lsof -ti:{config.js_server_port})")
    uvicorn.run('api:app', host="0.0.0.0", port=config.fastapi_port, reload=True)
