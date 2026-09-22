import numpy as np
import pandas as pd
import ta
import lightgbm as lgb
from sklearn.linear_model import LinearRegression
from data_fetcher import get_historical_data
from confidence import calculate_confidence

def create_features(df):
    df = df.copy()
    df['SMA_10'] = ta.trend.sma_indicator(df['Close'], window=10)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
    df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['BB_Upper'] = ta.volatility.bollinger_hband(df['Close'])
    df['BB_Lower'] = ta.volatility.bollinger_lband(df['Close'])
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
    df['ROC'] = ta.momentum.roc(df['Close'], window=10)
    df['Volume_Change'] = df['Volume'].pct_change()
    df['Price_Change'] = df['Close'].pct_change()
    df['High_Low_Pct'] = (df['High'] - df['Low']) / df['Close']
    for lag in [1, 2, 3, 5]:
        df[f'Close_Lag_{lag}'] = df['Close'].shift(lag)
        df[f'Volume_Lag_{lag}'] = df['Volume'].shift(lag)
    return df

features_list = ['Open', 'High', 'Low', 'Close', 'Volume',
                 'SMA_10', 'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26',
                 'RSI', 'MACD', 'MACD_Signal',
                 'BB_Upper', 'BB_Lower', 'ATR', 'ROC',
                 'Volume_Change', 'Price_Change', 'High_Low_Pct',
                 'Close_Lag_1', 'Close_Lag_2', 'Close_Lag_3', 'Close_Lag_5',
                 'Volume_Lag_1', 'Volume_Lag_2', 'Volume_Lag_3', 'Volume_Lag_5']

def train_lgb_model(df, target_col='Target_Change'):
    df_feat = create_features(df)
    df_feat[target_col] = df_feat['Close'].shift(-1) - df_feat['Close']
    df_feat = df_feat.dropna()
    X = df_feat[features_list].values
    y = df_feat[target_col].values
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    model = lgb.LGBMRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.03,
        num_leaves=25, random_state=42, verbose=-1
    )
    model.fit(X_train, y_train)
    return model, features_list, df_feat, X_val, y_val

def predict_future(model, features, df_feat, days):
    last_row = df_feat[features].iloc[-1:].values
    prices = [df_feat['Close'].iloc[-1]]
    current_row = last_row.copy()
    for i in range(days):
        if i < 7:
            change_pred = model.predict(current_row)[0]
            next_price = prices[-1] + change_pred
            prices.append(next_price)
            new_row = current_row[0].copy()
            new_row[3] = next_price
            price_change = (next_price - new_row[2]) / new_row[2] if new_row[2] != 0 else 0
            new_row[18] = price_change
            new_row[19] = (new_row[1] - new_row[2]) / next_price
            for li, lag in enumerate([1, 2, 3, 5]):
                idx = 20 + li
                if lag <= len(prices):
                    new_row[idx] = prices[-lag]
            new_row[17] = 0.0
            current_row = new_row.reshape(1, -1)
        else:
            x = np.arange(len(prices))
            y = np.array(prices)
            coeffs = np.polyfit(x, y, 1)
            trend = np.poly1d(coeffs)
            resid = np.std(y - trend(x)) if len(y) > 2 else 0.01
            noise = np.random.normal(0, max(resid * 0.05, 0.005))
            next_price = trend(i) + noise
            prices.append(next_price)
    return prices[1:]

class DailyModel:
    def predict(self, symbol):
        df = get_historical_data(symbol, period="2y", interval="1d")
        if df is None or len(df) < 30:
            return None
        model, feats, df_feat, X_val, y_val = train_lgb_model(df)
        preds = predict_future(model, feats, df_feat, days=30)
        last_price = float(df_feat['Close'].iloc[-1])
        confidence = calculate_confidence(model, X_val, y_val, preds)
        return {
            "predictions": [round(p, 2) for p in preds],
            "last_price": round(last_price, 2),
            "confidence": confidence
        }

class WeeklyModel:
    def predict(self, symbol):
        df = get_historical_data(symbol, period="5y", interval="1wk")
        if df is None or len(df) < 20:
            return None
        df_resampled = df.resample('W').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min',
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
        if len(df_resampled) < 20:
            return None
        model, feats, df_feat, X_val, y_val = train_lgb_model(df_resampled)
        preds = predict_future(model, feats, df_feat, days=4)
        last_price = float(df_feat['Close'].iloc[-1])
        confidence = calculate_confidence(model, X_val, y_val, preds)
        return {
            "predictions": [round(p, 2) for p in preds],
            "last_price": round(last_price, 2),
            "confidence": confidence
        }

class MonthlyModel:
    def predict(self, symbol):
        df = get_historical_data(symbol, period="10y", interval="1mo")
        if df is None or len(df) < 15:
            df = get_historical_data(symbol, period="5y", interval="1mo")
        if df is None or len(df) < 12:
            return None
        model, feats, df_feat, X_val, y_val = train_lgb_model(df)
        preds = predict_future(model, feats, df_feat, days=6)
        last_price = float(df_feat['Close'].iloc[-1])
        confidence = calculate_confidence(model, X_val, y_val, preds)
        return {
            "predictions": [round(p, 2) for p in preds],
            "last_price": round(last_price, 2),
            "confidence": confidence
        }

class YearlyModel:
    def predict(self, symbol):
        df = get_historical_data(symbol, period="10y", interval="1mo")
        if df is None or len(df) < 12:
            return None
        yearly = df.resample('YE').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min',
            'Close': 'last', 'Volume': 'sum'
        }).dropna()
        if len(yearly) < 3:
            return None
        years_elapsed = np.array([(d.year + d.month/12) for d in yearly.index]).reshape(-1, 1)
        prices_yearly = yearly['Close'].values
        lr = LinearRegression()
        lr.fit(years_elapsed, prices_yearly)
        last_year = years_elapsed[-1][0]
        next_years = np.array([last_year + i for i in range(1, 3)]).reshape(-1, 1)
        preds = lr.predict(next_years)
        residuals = prices_yearly - lr.predict(years_elapsed)
        mae = np.mean(np.abs(residuals))
        noise = np.random.normal(0, mae * 0.5, size=len(preds))
        preds = preds + noise
        last_price = float(prices_yearly[-1])
        r2 = lr.score(years_elapsed, prices_yearly)
        confidence = max(30, min(80, (r2 * 60 + 30)))
        return {
            "predictions": [round(p, 2) for p in preds],
            "last_price": round(last_price, 2),
            "confidence": round(confidence, 1)
        }
