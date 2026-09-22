MARKET_SYMBOLS = {
    "US_Stocks": {
        "name": "الأسهم الأمريكية",
        "timezone": "America/New_York",
        "symbols": [
            "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META",
            "BRK-B", "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH",
            "HD", "DIS", "BAC", "ADBE", "NFLX", "CRM", "AMD", "INTC",
            "PYPL", "IBM", "BA", "GE", "CAT", "XOM", "CVX"
        ]
    },
    "EU_Stocks": {
        "name": "الأسهم الأوروبية",
        "timezone": "Europe/London",
        "symbols": [
            "SAP.DE", "ASML.AS", "MC.PA", "OR.PA", "RMS.PA",
            "AIR.PA", "DTE.DE", "ALV.DE", "BMW.DE", "VOW3.DE",
            "RACE.MI", "ENEL.MI", "ISP.MI", "UBSG.SW", "NESN.SW"
        ]
    },
    "Asia_Stocks": {
        "name": "الأسهم الآسيوية",
        "timezone": "Asia/Tokyo",
        "symbols": [
            "0700.HK", "BABA", "9988.HK", "TCEHY", "TSM",
            "SFTBY", "7203.T", "6758.T", "6861.T", "8035.T"
        ]
    },
    "Crypto": {
        "name": "العملات الرقمية",
        "timezone": "UTC",
        "symbols": [
            "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD",
            "DOGE-USD", "DOT-USD", "AVAX-USD", "LINK-USD", "MATIC-USD",
            "UNI7083-USD", "ATOM-USD", "LTC-USD", "BCH-USD", "XLM-USD"
        ]
    },
    "Forex": {
        "name": "الفوركس",
        "timezone": "UTC",
        "symbols": [
            "EURUSD=X", "GBPUSD=X", "JPYUSD=X", "CHFUSD=X",
            "AUDUSD=X", "CADUSD=X", "CNYUSD=X", "INRUSD=X",
            "MXNUSD=X", "BRLUSD=X"
        ]
    },
    "Commodities": {
        "name": "السلع",
        "timezone": "America/New_York",
        "symbols": [
            "GC=F", "CL=F", "SI=F", "HG=F", "NG=F",
            "ZW=F", "ZC=F", "ZS=F", "CC=F", "KC=F"
        ]
    }
}

def get_all_symbols():
    result = []
    for market in MARKET_SYMBOLS.values():
        result.extend(market["symbols"])
    return result

def get_market_for_symbol(symbol):
    for key, market in MARKET_SYMBOLS.items():
        if symbol in market["symbols"]:
            return key
    return "Unknown"
