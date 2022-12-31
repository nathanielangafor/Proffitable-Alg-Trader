-- Log Data Structure --

{
    "asset": "Name of traded asset : string",
    "asset_type": {
        "asset_type": "Type of traded asset : string",
        "gate_bypass": "Gates to be skipped by asset : Array"
    },
    "asset_price": "Price of asset upon iteration : float",
    "order_type": "Type of order : string",
    "check_time": "Time of iteration : string",
    "market_sentiment": {
        "Sentiment of market upon iteration : dictionary"
    },
    "gates": {
        "macd_gate": {
            "output": "Output of MACD gate : Boolean",
            "data": {
                "macd": "float",
                "histogram": "float",
                "avgMACD": "float",
                "avgHist": "float"
            }
        },
        "rsi_gate": {
            "output": "Output of RSI gate : Boolean",
            "data": {
                "rsi": "float"
            }
        },
        "cci_gate": {
            "output": "Output of CCI gate : Boolean",
            "data": {
                "cci": "float"
            }
        },
        "trend_gate": {
            "output": "Output of Trend gate : Boolean",
            "data": {
                "greaterCount": "int",
                "lessCount": "int"
            }
        },
        "momentum_gate": {
            "output": "Output of MACD gate : Boolean",
            "data": {
                "assetMomentum": "float"
            }
        },
        "ichimoku_gate": {
            "output": "Output of Ichimoku gate : Boolean",
            "data": {
                "current": {
                    "senkou_span_a": "float",
                    "senkou_span_b": "float"
                }
            }
        },
        "ema_gate": {
            "output": "Output of EMA gate : Boolean",
            "data": {
                "ema": "float",
                "dema": "float",
                "atr": "float"
            }
        },
        "bollinger_gate": {
            "output": "Output of Bollingeer gate : Boolean",
            "data": {
                "lower": "float",
                "upper": "float"
            }
        },
        "cloud_gate": {
            "output": "Output of Cloud gate : Boolean",
            "data": {
                "cloud_size": {
                    "current": "float"
                }
            }
        }
    },
    "decision": false
}