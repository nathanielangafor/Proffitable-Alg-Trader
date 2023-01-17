import sys
import requests
import pandas as pd
import time 
import finviz

# Append the 'Config Files' folder to path and import the needed module
sys.path.append('Config Files')
import config
# Append the 'Analysis' folder to path and import the needed module
sys.path.append('Analysis')
import indicators 

def pe_gate(pe, forward_pe, data):
    stocks_gate_data = data['fundamental_gate']['stocks']['field_data']
    return {
        'data': 
            pe < stocks_gate_data['pe'] and 
            forward_pe > stocks_gate_data['min_forward_pe'] and 
            forward_pe < stocks_gate_data['max_forward_pe']
    }

def eps_gate(eps_ttm, eps_this_y, eps_next_q, eps_next_y, eps_growth_next_y, eps_next_5y, eps_past_5y, eps_q_q, data):
    stocks_gate_data = data['fundamental_gate']['stocks']['field_data']
    return {
        'data': 
            eps_ttm > stocks_gate_data['eps_ttm'] and 
            eps_this_y > stocks_gate_data['eps_this_y'] and 
            eps_next_q > stocks_gate_data['eps_next_q'] and
            eps_next_y > stocks_gate_data['eps_next_y'] and 
            eps_growth_next_y > stocks_gate_data['eps_growth_next_y'] and 
            eps_next_5y > stocks_gate_data['eps_next_5y'] and
            eps_past_5y > stocks_gate_data['eps_past_5y'] and 
            eps_q_q > stocks_gate_data['eps_q_q']
        }

def sales_gate(sales_past_5y, sales, ps, data):
    stocks_gate_data = data['fundamental_gate']['stocks']['field_data']
    return {
        'data': 
            sales_past_5y > stocks_gate_data['sales_past_5y'] and 
            sales > stocks_gate_data['sales'] and
            ps < stocks_gate_data['ps']
    }

def book_gate(book_sh, pb, data):
    stocks_gate_data = data['fundamental_gate']['stocks']['field_data']
    return {
        'data': 
            book_sh > stocks_gate_data['book_sh'] and 
            pb > stocks_gate_data['pb_min'] and 
            pb < stocks_gate_data['pb_max']
    }

def return_gate(roa, roe, roi, data):
    stocks_gate_data = data['fundamental_gate']['stocks']['field_data']
    return {
        'data': 
            roa > stocks_gate_data['roa'] and 
            roe > stocks_gate_data['roe'] and 
            roi > stocks_gate_data['roi']
    }

def cash_gate(cash_sh, pc, pfcf, data):
    stocks_gate_data = data['fundamental_gate']['stocks']['field_data']
    return {
        'data': 
            cash_sh > stocks_gate_data['cash_sh'] and 
            pc < stocks_gate_data['pc'] and 
            pfcf < stocks_gate_data['pfcf']
    }

def qc_ratio_gate(quick_ratio, current_ratio, data):
    stocks_gate_data = data['fundamental_gate']['stocks']['field_data']
    return {
        'data': 
            quick_ratio > stocks_gate_data['quick_ratio'] and 
            current_ratio > stocks_gate_data['current_ratio']
    }

def margin_gate(operating_margin, profit_margin, gross_margin, data):
    stocks_gate_data = data['fundamental_gate']['stocks']['field_data']
    return {
        'data': 
            operating_margin > stocks_gate_data['operating_margin'] and 
            profit_margin > stocks_gate_data['profit_margin'] and 
            gross_margin > stocks_gate_data['gross_margin']
    }

def debt_gate(debt_eq, lt_debt_eq, data):
    stocks_gate_data = data['fundamental_gate']['stocks']['field_data']
    return {
        'data': 
            debt_eq < stocks_gate_data['debt_eq'] and 
            lt_debt_eq < stocks_gate_data['lt_debt_eq']
    }

required_fields = {
    'pe_gate': ['P/E', 'Forward P/E', 'PEG'],
    'eps_gate': ['EPS (ttm)', 'EPS next Y', 'EPS next Q', 'EPS this Y', 'EPS growth next Y', 'EPS next 5Y', 'EPS past 5Y', 'EPS Q/Q'],
    'sales_gate': ['Sales', 'Sales Q/Q', 'Sales past 5Y', 'P/S'],
    'book_gate': ['P/B', 'Book/sh'],
    'return_gate': ['ROI', 'ROA', 'ROI'],
    'cash_gate': ['P/C', 'Cash/sh', 'P/FCF'],
    'qc_ratio_gate': ['Quick Ratio', 'Current Ratio'],
    'margin_gate': ['Oper. Margin', 'Gross Margin', 'Profit Margin'],
    'debt_gate': ['Debt/Eq', 'LT Debt/Eq']
}

def get_stocks(min_volume, min_price, min_sector_average, marketcap_min, marketcap_max):
    """
    This function uses the Nasdaq API to get a list of stocks that meet certain criteria.
    The criteria are as follows:
    1. The stock's volume must be greater than the provided min_volume
    2. The stock's last sale price must be greater than the provided min_price
    3. The stock's percentage change must be greater than the average percentage change for its sector
    4. The average percentage change for the stock's sector must be greater than the provided min_sector_average
    5. The stock's market cap must be between marketcap_min and marketcap_max
    
    Parameters:
    min_volume: The minimum volume a stock must have to be included in the list
    min_price: The minimum last sale price a stock must have to be included in the list
    min_sector_average: The minimum average percentage change a stock's sector must have to be included in the list
    marketcap_min: The minimum market cap a stock must have to be included in the list
    marketcap_max: The maximum market cap a stock can have to be included in the list
    
    Returns:
    A list of stocks that meet the above criteria
    """    
    # Set headers for the request
    headers = {
        'authority': 'api.nasdaq.com',
        'accept': 'application/json, text/plain, */*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'origin': 'https://www.nasdaq.com',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.nasdaq.com/',
        'accept-language': 'en-US,en;q=0.9',
    }
    # Set parameters for the request
    params = (
        ('tableonly', 'true'),
        ('download', 'true'),
    )
    # Send request and get the JSON data
    r = requests.get('https://api.nasdaq.com/api/screener/stocks', headers=headers, params=params)
    data = r.json()['data']
    # Convert data to a Pandas DataFrame
    df = pd.DataFrame(data['rows'], columns=data['headers'])
    # Convert volume, marketCap, lastsale, and pctchange columns to appropriate data types
    df['volume'] = df['volume'].apply(int)
    df['marketCap'] = df['marketCap'].apply(lambda x: float(x.replace('%', '')) if x != '' else float('nan'))
    df['lastsale'] = df['lastsale'].apply(lambda x: float(x.replace('$', '')))
    df['pctchange'] = df['pctchange'].apply(lambda x: float(x.replace('%', '')) if x != '' else float('nan'))
    # Calculate the average pctchange for each sector
    sector_averages = df.groupby('sector')['pctchange'].mean().to_dict()
    # Filter the DataFrame based on the specified conditions
    filtered_df = df.loc[
        (df['lastsale'] > min_price) & 
        (df['volume'] > min_volume)  & 
        (df['pctchange'] > df['sector'].map(sector_averages)) & 
        (df['sector'].map(sector_averages) > min_sector_average) &
        (df['marketCap'] > marketcap_min) & 
        (df['marketCap'] < marketcap_max)
    ]
    # Return the filtered DataFrame as a list
    asset_list = filtered_df.values.tolist()
    # Confirm assets are in our dbs
    parsed_asset_list = []
    for asset in asset_list:
        parsed_asset_list.append(asset[0])
    return {
        'data': parsed_asset_list,
        'msg': 'success'
    }
    

for stock in ['MTB']: #get_stocks(1000000, config.penny_stock_definition, 0, 300000000, 2000000000)['data']:
    time.sleep(.5)
    data = finviz.get_stock(stock)
    for gate_name in config.gate_settings['fundamental_gate']['stocks']['required_fields'].keys():
        can_check = True
        for data_name in config.gate_settings['fundamental_gate']['stocks']['required_fields'][gate_name]:
            if config.sanitize_number(data[data_name])['msg'] == 'error':
                can_check = False
            else:
                data[data_name] = config.sanitize_number(data[data_name])['data']
        if can_check:
            if gate_name == 'pe_gate':
                pe_data = pe_gate(data['P/E'], data['Forward P/E'], config.gate_settings)['data']
                print(f'{stock} - pe_gate: {pe_data}')
            if gate_name == 'book_gate':
                book_data = book_gate(data['Book/sh'], data['P/B'], config.gate_settings)['data']
                print(f'{stock} - book_gate: {book_data}')
            if gate_name == 'return_gate':
                return_data = return_gate(data['ROI'], data['ROA'], data['ROE'], config.gate_settings)['data']
                print(f'{stock} - return_gate: {return_data}')
            if gate_name == 'cash_gate':
                cash_data = cash_gate(data['Cash/sh'], data['P/C'], data['P/FCF'], config.gate_settings)['data']
                print(f'{stock} - cash_gate: {cash_data}')
            if gate_name == 'sales_gate':
                sales_data = sales_gate(data['Sales past 5Y'], data['Sales'], data['P/S'], config.gate_settings)['data']
                print(f'{stock} - sales_gate: {sales_data}')
            if gate_name == 'debt_gate':
                debt_data = debt_gate(data['Debt/Eq'], data['LT Debt/Eq'], config.gate_settings)['data']
                print(f'{stock} - debt_gate: {debt_data}')
            if gate_name == 'margin_gate':
                margin_data = margin_gate(data['Oper. Margin'], data['Gross Margin'], data['Profit Margin'], config.gate_settings)['data']
                print(f'{stock} - margin_gate: {margin_data}')
    print()