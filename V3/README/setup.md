Crypto Trading Project V3

Introduction:
    This project is an algorithmic trading program that allows users to automatically trade cryptocurrency and stock assets using a variety of indicators. The program is designed to make the trading process more efficient and convenient for users by automating the analysis and execution of trades based on user-specified criteria.

Features:
    - Support for multiple cryptocurrencies: Crypto Trading Project V3 supports a wide range of popular cryptocurrencies, including Bitcoin, Ethereum, Avalanch, Binanace Coin, Fantom Link, and Uni.
    - Support for any stock asset: In addition to supporting cryptocurrency trading, the program also allows users to trade any stock asset.
    - Auto trade aggregation: The program integrates with the mux.network and robinhood API to allow for automatic trade aggregation. 
    - Customizable indicator usage: The program allows users to toggle which indicators are used for each asset. 

Installation and Setup:
    1. Install the  dependencies below.
    2. Edit the config.py and config.js files (refer to the file structure for their location). These files contain important configuration information that is necessary for the program to run properly.
    3. Run the program. Once the dependencies have been installed and the config files have been edited, the program can be launched by running the appropriate command in the terminal.

# Node install statements
```cd Program\ files/node_modules & npm install ws```

# Python install statements
```
pip3 install asyncio
pip3 install datetime
pip3 install pandas
pip3 install numpy
pip3 install cloudscraper
pip3 install fastapi
pip3 install uvicorn
pip3 install websockets
pip3 install discord.py
pip3 install cryptography
pip3 install bs4
pip3 install python-multipart

python3 api.py
node Brokers/Mux/muxServer.js - required
python3 Reporter/discordNotifier.py
python3 Market\ Monitor/buySide.py - required
python3 Market\ Monitor/sellSide.py - required
python3 Database/dataManager.py - required
```
*Run these commands from the root directory (V3/)*
