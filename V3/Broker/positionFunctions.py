import time
import requests
import sys

# append the config file filepath to sys.path
sys.path.append('/Users/appleid/Desktop/Other Files/V3/Config Files')
import config

def get_pending_mux_orders(my_wallet, assetId):
    while True:
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
            data = {
                "variables": {
                    "userAddr": my_wallet.lower()
                },
                "query": "query ($userAddr: ID!) {\n  user: users(where: {id: $userAddr}) {\n    positionOrder(\n      where: {isFinish: false}\n      orderBy: createdAt\n      orderDirection: desc\n    ) {\n      id\n      subAccountId\n      collateralId\n      assetId\n      collateral\n      size\n      price\n      profitTokenId\n      flags\n      isLong\n      isOpen\n      isMarket\n      isTrigger\n      isFinish\n      isFilled\n      createdAt\n      finishedAt\n      __typename\n    }\n    __typename\n  }\n}\n"
            }
            response = requests.post(
                "https://api.thegraph.com/subgraphs/name/mux-world/mux-arb",
                headers=headers,
                json=data
            )
            json_response = response.json()
            position_orders = json_response["data"]["user"][0]["positionOrder"]
            return_orders = []
            for position_order in position_orders:
                if position_order["assetId"] == assetId:
                    return_orders.append(position_order)
            return return_orders
        except:
            print("getPendingMUXOrders fetch error...")
            time.sleep(3000)

def get_all_mux_orders(myWallet, assetId):
    while True:
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

            data = {
                "variables": {
                    "userAddr": myWallet.lower(),
                    "pageSize": 30,
                    "startTime": 0,
                    "endTime": int(time.time())
                },
                "query": "query ($userAddr: ID!, $pageSize: Int!, $startTime: Int!, $endTime: Int!) {\n  positionTrades: positionTrades(\n    where: {user: $userAddr, assetId: " + str(assetId) + ", createdAt_gt: $startTime, createdAt_lte: $endTime}\n    orderBy: blockNumber\n    orderDirection: desc\n    first: $pageSize\n  ) {\n    id\n    subAccountId\n    collateralId\n    assetId\n    amount\n    isLong\n    assetPrice\n    pnlUsd\n    feeUsd\n    isOpen\n    hasProfit\n    createdAt\n    collateralPrice\n    remainCollateral\n    txHash\n    isLiquidated\n    blockNumber\n    logIndex\n    remainPosition\n    entryPrice\n    __typename\n  }\n  _meta {\n    block {\n      number\n      __typename\n    }\n    __typename\n  }\n}\n"
            }

            response = requests.post("https://api.thegraph.com/subgraphs/name/mux-world/mux-arb", headers=headers, json=data)
            orders = response.json()['data']['positionTrades']

            returnOrders = []
            for order in orders:
                if order['assetId'] == assetId:
                    returnOrders.append(order)
            return returnOrders
        except:
            print('get_all_mux_orders fetch error...')
            time.sleep(3000)

def get_position_summary(wallet, assetId):
    orders = get_all_mux_orders(wallet, assetId)
    orders = orders[::-1]

    short_info = {
        "average_entry_price": 0,
        "remaining_position": 0,
        "remaining_collateral": 0,
        "multiplier": 0,
        "liquidation_price": 0,
        "transaction_count": 0,
        "fees": 0
    }

    long_info = {
        "average_entry_price": 0,
        "remaining_position": 0,
        "remaining_collateral": 0,
        "multiplier": 0,
        "liquidation_price": 0,
        "transaction_count": 0,
        "fees": 0
    }

    for order in orders:
        order['amount'] = float(order['amount'])
        order['assetPrice'] = float(order['assetPrice'])
        order['pnlUsd'] = float(order['pnlUsd'])
        order['feeUsd'] = float(order['feeUsd'])
        order['collateralPrice'] = float(order['collateralPrice'])
        order['remainCollateral'] = float(order['remainCollateral'])
        order['remainPosition'] = float(order['remainPosition'])
        order['entryPrice'] = float(order['entryPrice'])

        if order['assetId'] != assetId:
            continue

        info = short_info if not order['isLong'] else long_info
        if not order['isOpen']:
            info['transaction_count'] -= 1
            info['average_entry_price'] -= order['assetPrice'] * order['amount']
            info['fees'] -= order['feeUsd']
        elif order['isOpen']:
            info['transaction_count'] += 1
            info['average_entry_price'] += order['assetPrice'] * order['amount']
            info['fees'] += order['feeUsd']

        if order['remainPosition'] == '0':
            info['transaction_count'] = 0
            info['average_entry_price'] = 0
            info['remaining_collateral'] = 0
            info['remaining_position'] = 0
            info['fees'] = 0

        info['remaining_collateral'] = order['remainCollateral']
        info['remaining_position'] = order['remainPosition']

        if info['transaction_count'] > 0 and info['remaining_collateral'] > 0:
            info['average_entry_price'] /= info['remaining_position']
            info['multiplier'] = (
                info['average_entry_price'] * info['remaining_position']
            ) / info['remaining_collateral']
            funding_rate = .008 if order['isLong'] else .01
            info['liquidation_price'] = (
                (info['remaining_collateral'] - (info['remaining_collateral'] * 2))
                + (info['remaining_collateral'] / 100) * funding_rate
                + info['average_entry_price']
                * (-1 if not order['isLong'] else 1)
                * info['remaining_position']
            ) / (
                info['remaining_position'] * (
                    -1 if not order['isLong'] else 1
                    - 0.005
                    - 0.001
                )
            )

    return {
        "Shorts": short_info,
        "Longs": long_info
    }
