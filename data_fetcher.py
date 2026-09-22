import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

price_cache = {}
history_cache = {}
CACHE_TTL = 60

def get_live_price(symbol):
    try:
        now = time.time()
        if symbol in price_cache and (now - price_cache[symbol]["time"]) < 30:
            return price_cache[symbol]["price"]
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if data.empty:
            data = ticker.history(period="5d", interval="1d")
        if data.empty:
            return None
        price = float(data['Close'].iloc[-1])
        price_cache[symbol] = {"price": price, "time": now}
        return price
    except Exception as e:
        return None

def get_historical_data(symbol, period="2y", interval="1d"):
    cache_key = f"{symbol}_{period}_{interval}"
    now = time.time()
    if cache_key in history_cache and (now - history_cache[cache_key]["time"]) < CACHE_TTL * 10:
        return history_cache[cache_key]["data"]
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        df = df.dropna()
        if len(df) < 20:
            return None
        history_cache[cache_key] = {"data": df, "time": now}
        return df
    except Exception as e:
        return None

def get_all_live_prices(symbols):
    result = {}
    for sym in symbols:
        price = get_live_price(sym)
        if price:
            result[sym] = price
    return result
