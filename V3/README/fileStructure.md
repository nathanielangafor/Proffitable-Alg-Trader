-- File Structure --

root
├── Analysis
│   ├── Fundamental
│   │   └── quantitative.py
│   ├── Technical
│   │   └── indicators.py
│   └── gates.py
├── Brokers
│   ├── Mux
│   │   ├── muxBroker.js
│   │   ├── muxBroker.py
│   │   └── muxServer.js
│   ├── Robinhood
│   │   └── rhBroker.py
│   └── orderManager.py
├── Config Files
│   ├── config.js
│   └── config.py
├── Database
│   ├── database.py
│   ├── dataManager.py
│   └── recommendations.py
├── Market Monitor
│   ├── buySide.py
│   └── sellSide.py
├── Program Files
│   ├── CSV Files
│   │   └── *.csv
│   ├── node_modules
│   │   └── @*
│   ├── database.db
│   ├── package-lock.json
│   └── package.json
├── README
│   ├── fileStructure.md - YOU ARE HERE
│   └── discordNotifier.py 
├── Reporter
│   └── discordNotifier.py 
└── api.py

* Any files not listed in this directory tree can be deleted. This excludes files in the directories listed below *
- root/Program Files/CSV Files
- root/Program Files/node_modules

