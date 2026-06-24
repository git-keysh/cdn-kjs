"""
Configuration file for XAUUSD AI Trading Partner
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── App Settings ────────────────────────────────────────────────
APP_TITLE = "🥇 XAUUSD AI Trading Partner"
APP_VERSION = "1.0.0"

# ── Chart Settings ──────────────────────────────────────────────
CHART_THEME = "plotly_dark"
CANDLE_UP_COLOR = "#26a69a"    # Green
CANDLE_DOWN_COLOR = "#ef5350"  # Red

# ── Trading Settings ────────────────────────────────────────────
DEFAULT_ACCOUNT_BALANCE = 10000.0
DEFAULT_RISK_PERCENT = 1.0  # 1% risk per trade
MAX_DAILY_LOSS_PERCENT = 5.0  # 5% max daily loss
MIN_RR_RATIO = 1.5  # Minimum risk-reward ratio
SIGNAL_CONFIDENCE_THRESHOLD = 0.6  # 60% minimum confidence

# ── Data Settings ───────────────────────────────────────────────
REFRESH_SECONDS = 60  # Auto-refresh interval
DEFAULT_TIMEFRAME = "1h"
MAX_CANDLES = 500

# ── ML Settings ─────────────────────────────────────────────────
ML_RETRAIN_EVERY_N_SIGNALS = 20
ML_MIN_SIGNALS_TO_TRAIN = 10

# ── Database ────────────────────────────────────────────────────
DB_PATH = "trading_data.db"

# ── Asset Symbols ──────────────────────────────────────────────
XAUUSD_SYMBOL = "GC=F"  # Yahoo Finance symbol for Gold Futures
DXY_SYMBOL = "DX-Y.NYB"
US10Y_SYMBOL = "^TNX"

# ── Correlated Assets ──────────────────────────────────────────
CORRELATED_ASSETS = {
    "DXY": DXY_SYMBOL,
    "US10Y": US10Y_SYMBOL,
}

# ── Kill Zones (UTC Times) ─────────────────────────────────────
KILL_ZONES = {
    "London": {"start": 7, "end": 9},      # 7-9 AM UTC
    "New York": {"start": 13, "end": 15},  # 1-3 PM UTC
    "Asian": {"start": 23, "end": 1},      # 11 PM - 1 AM UTC
}