import json
import websockets
import sys
import requests

# append the config file path to sys.path
sys.path.append('Config Files')
import config

async def place_mux_order(asset, order_type, trade_amount, multiplier, asset_price, flag, wss_node, mnemonic, wallet_address):
    """
    Place an order on the Mux Asset exchange.
    
    Parameters:
    asset (str): The asset name.
    order_type (str): The type of order.
    trade_amount (float): The amount of asset to trade.
    multiplier (int): The amount of leverage to use.
    asset_price (float): The price of the asset.
    slippage_percent (float): The amount of slippage allowed for the order.
    flag (str): The type of order. 'buy' or 'sell'.
    wss_node (str): The WebSocket node to connect to.
    mnemonic (str): The mnemonic used to derive the wallet address.
    wallet_address (str): The wallet address used to place the order.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        # Convert flag to int
        if flag == 'buy':
            flag = 128
        if flag == 'sell':
            flag = 32
        # Build the data structure
        data = {
            "type": "managePositionOrder",
            "asset": asset,
            "orderType": order_type,
            "tradeAmount": trade_amount,
            "multiplier": multiplier,
            "price": asset_price,
            "flag": flag,
            "wssNode": wss_node,
            "mnemonic": mnemonic,
            "walletAddress": wallet_address
        }
        # Connect to the WebSocket and send the order
        async with websockets.connect("ws://localhost:8080") as websocket:
            await websocket.send(json.dumps(data))
            response = await websocket.recv()
            # Raise an exception if the order could not be executed
            if response == 'error':
                raise Exception('Order could not be executed')
            return {
                'data': response,
                'msg': 'success'
            }
    except Exception as e:
        error = {
            'data': {
                'file': 'muxBroker.py',
                'function': 'place_mux_order',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error

async def cancel_mux_order(order_id, wss_node, mnemonic, wallet_address):
    """Cancel a previously placed order on Mux.
    
    Parameters:
    order_id (str): The id of the order to be canceled.
    wss_node (str): The websocket node for connecting to Mux.
    mnemonic (str): The mnemonic for the wallet.
    wallet_address (str): The wallet address to send the transaction from.
    
    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        data = {
            "type": "cancelPositionOrder",
            "orderId": order_id,
            "wssNode": wss_node,
            "mnemonic": mnemonic,
            "walletAddress": wallet_address
        }
        async with websockets.connect("ws://localhost:8080") as websocket:
            await websocket.send(json.dumps(data))
            response = await websocket.recv()
            if response == 'error':
                raise Exception('Order could not be canceled')
            return {
                'data': response,
                'msg': 'success'
            }
    except Exception as e:
        error = {
            'data': {
                'file': 'muxBroker.py',
                'function': 'candel_mux_order',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error

def get_pending_mux_orders(wallet_address, asset):
    """
    This function is used to get all pending orders for a specific asset and wallet address.
    It makes a POST request to the TheGraph API, which is a service that makes it easy to
    perform GraphQL queries on Ethereum data.
    The API returns all the positionOrder objects that have the isFinish field set to false.
    The function then filters the orders to only return the ones that match the specified asset
    using the assetId field and the config.crypto['asset_ids'][asset]['id'] value.

    Parameters:
    wallet_address (str): The wallet address to retrieve the pending orders for.
    asset (str): The asset to retrieve the pending orders for.

    Returns:
    dict: a dictionary containing the status of the operation and any relevant data.
        The dictionary has the following keys:
            'data': data returned from the function.
            'msg': a string indicating the status of the operation. It can be either 'success' or 'error'.
    """
    try:
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,enq=0.9",
            "content-type": "application/json",
            "sec-ch-ua": "\"Google Chrome\"v=\"107\", \"Chromium\"v=\"107\", \"Not=A?Brand\"v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site"
        }
        body = {
            "variables": {
                "userAddr": f"{wallet_address.lower()}"
            },
            "query": "query ($userAddr: ID!) {\n  user: users(where: {id: $userAddr}) {\n    positionOrder(\n      where: {isFinish: false}\n      orderBy: createdAt\n      orderDirection: desc\n    ) {\n      id\n      subAccountId\n      collateralId\n      assetId\n      collateral\n      size\n      price\n      profitTokenId\n      flags\n      isLong\n      isOpen\n      isMarket\n      isTrigger\n      isFinish\n      isFilled\n      createdAt\n      finishedAt\n      __typename\n    }\n    __typename\n  }\n}\n"
        }
        response = requests.post(
            "https://api.thegraph.com/subgraphs/name/mux-world/mux-arb",
            headers=headers,
            json=body
        ).json()['data']['user'][0]['positionOrder']
        response_list = []
        for order in response:
            if order['assetId'] == config.crypto['asset_ids'][asset]['id']:
                response_list.append(order)
        return {
            'data': response_list,
            'msg': 'success'
        }
    except Exception as e:
        error = {
            'data': {
                'file': 'muxBroker.py',
                'function': 'get_pending_mux_orders',
                'raise_exception': str(e)
            },
            'msg': 'error'
        }
        config.log_error(json.dumps(error))
        return error