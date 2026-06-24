"""
Data fetching module for XAUUSD AI Trading Partner
"""

import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta
import config
import time


def fetch_ohlcv(timeframe="1h", period="5d"):
    """
    Fetch OHLCV data for XAUUSD
    timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d
    """
    try:
        # Map timeframe to yfinance interval
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m",
            "30m": "30m", "1h": "1h", "4h": "1h",
            "1d": "1d"
        }

        # For 4h, we need to get 1h data and resample
        if timeframe == "4h":
            interval = "1h"
            period = "10d"
        else:
            interval = interval_map.get(timeframe, "1h")
            period = "5d"

        ticker = yf.Ticker("GC=F")  # Gold Futures
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            return pd.DataFrame()

        # Resample for 4h if needed
        if timeframe == "4h":
            df = df.resample('4H').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()

        # Keep only last MAX_CANDLES
        if len(df) > config.MAX_CANDLES:
            df = df.iloc[-config.MAX_CANDLES:]

        return df

    except Exception as e:
        print(f"Error fetching OHLCV: {e}")
        return pd.DataFrame()


def fetch_live_price():
    """Fetch live XAUUSD price"""
    try:
        ticker = yf.Ticker("GC=F")
        data = ticker.history(period="1d", interval="1m")

        if data.empty:
            return {"price": 0, "change": 0, "pct": 0, "time": "N/A"}

        latest = data.iloc[-1]
        price = latest['Close']

        # Get previous close for change calculation
        if len(data) > 1:
            prev = data.iloc[-2]['Close']
            change = price - prev
            pct = (change / prev) * 100
        else:
            change = 0
            pct = 0

        return {
            "price": price,
            "change": change,
            "pct": pct,
            "time": datetime.now().strftime("%H:%M:%S UTC")
        }

    except Exception as e:
        print(f"Error fetching live price: {e}")
        return {"price": 0, "change": 0, "pct": 0, "time": "N/A"}


def fetch_correlated_assets():
    """Fetch correlated asset prices (DXY, US10Y)"""
    try:
        assets = {}
        for name, symbol in config.CORRELATED_ASSETS.items():
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                assets[name] = data.iloc[-1]['Close']
            else:
                assets[name] = 0

        return assets

    except Exception as e:
        print(f"Error fetching correlated assets: {e}")
        return {"DXY": 0, "US10Y": 0}


def add_indicators(df):
    """Add technical indicators to DataFrame"""
    if df.empty:
        return df

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # EMAs
    df['ema_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['ema_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # ATR
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(14).mean()

    # Bollinger Bands
    df['sma_20'] = df['Close'].rolling(window=20).mean()
    df['std_20'] = df['Close'].rolling(window=20).std()
    df['bb_upper'] = df['sma_20'] + (df['std_20'] * 2)
    df['bb_lower'] = df['sma_20'] - (df['std_20'] * 2)

    # Volume moving average
    df['volume_sma'] = df['Volume'].rolling(window=20).mean()

    return df


def fetch_gold_news():
    """Fetch gold-related news with sentiment"""
    # Using free news API (replace with actual API key for production)
    try:
        # Mock news for demo - in production, use a news API
        mock_news = [
            {"headline": "Gold prices steady as dollar weakens", "source": "Reuters", "sentiment": 0.2, "timestamp": datetime.now().isoformat()},
            {"headline": "Central bank buying supports gold demand", "source": "Bloomberg", "sentiment": 0.3, "timestamp": datetime.now().isoformat()},
            {"headline": "Inflation data beats expectations, gold rallies", "source": "CNBC", "sentiment": 0.5, "timestamp": datetime.now().isoformat()},
            {"headline": "Fed signals rate cuts, gold surges", "source": "WSJ", "sentiment": 0.7, "timestamp": datetime.now().isoformat()},
            {"headline": "Geopolitical tensions boost safe-haven gold", "source": "FT", "sentiment": 0.6, "timestamp": datetime.now().isoformat()},
        ]
        return mock_news

    except Exception as e:
        print(f"Error fetching news: {e}")
        return []


def get_macro_bias(news_list):
    """Calculate macro bias from news sentiment"""
    if not news_list:
        return {"bias": "NEUTRAL", "label": "Neutral", "score": 0}

    sentiments = [n.get('sentiment', 0) for n in news_list if n.get('sentiment') is not None]
    if not sentiments:
        return {"bias": "NEUTRAL", "label": "Neutral", "score": 0}

    avg_sentiment = sum(sentiments) / len(sentiments)

    if avg_sentiment > 0.2:
        bias = "BULLISH"
        label = "Bullish"
    elif avg_sentiment < -0.2:
        bias = "BEARISH"
        label = "Bearish"
    else:
        bias = "NEUTRAL"
        label = "Neutral"

    return {"bias": bias, "label": label, "score": avg_sentiment}