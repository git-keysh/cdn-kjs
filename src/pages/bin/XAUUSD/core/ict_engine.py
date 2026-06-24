"""
ICT (Inner Circle Trader) Analysis Engine
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config


def full_ict_analysis(df, timeframe):
    """Complete ICT analysis"""
    if df.empty:
        return {}

    result = {
        "current_price": df['Close'].iloc[-1],
        "timestamp": datetime.now().isoformat(),
        "timeframe": timeframe,
        "structure": analyze_market_structure(df),
        "order_blocks": find_order_blocks(df),
        "fair_value_gaps": find_fvg(df),
        "liquidity": find_liquidity_levels(df),
        "premium_discount": calculate_premium_discount(df),
        "kill_zone": check_kill_zones(),
        "power_of_3": analyze_power_of_3(df),
        "breaker_blocks": find_breaker_blocks(df),
        "displacement": find_displacement(df),
        "atr": df['atr'].iloc[-1] if 'atr' in df else 0,
        "bias": calculate_bias(df),
        "confluence_buy": 0,
        "confluence_sell": 0,
        "suggested_sl": 0,
        "suggested_tp": 0,
        "rr_ratio": 0,
    }

    # Calculate confluence
    result["confluence_buy"], result["confluence_sell"] = calculate_confluence(result)

    # Calculate suggested SL/TP
    result["suggested_sl"], result["suggested_tp"], result["rr_ratio"] = calculate_sl_tp(result, df)

    return result


def analyze_market_structure(df):
    """Analyze market structure: trend, BOS, CHoCH"""
    if len(df) < 20:
        return {"trend": "NEUTRAL", "bos_list": [], "choch_list": []}

    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values

    # Find swing highs and lows
    swing_highs = []
    swing_lows = []

    for i in range(5, len(df) - 5):
        if high[i] > max(high[i-5:i]) and high[i] > max(high[i+1:i+6]):
            swing_highs.append((i, high[i]))
        if low[i] < min(low[i-5:i]) and low[i] < min(low[i+1:i+6]):
            swing_lows.append((i, low[i]))

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {"trend": "NEUTRAL", "bos_list": [], "choch_list": []}

    # Determine trend
    last_high = swing_highs[-1][1] if swing_highs else 0
    prev_high = swing_highs[-2][1] if len(swing_highs) > 1 else 0
    last_low = swing_lows[-1][1] if swing_lows else 0
    prev_low = swing_lows[-2][1] if len(swing_lows) > 1 else 0

    if last_high > prev_high and last_low > prev_low:
        trend = "BULLISH"
    elif last_high < prev_high and last_low < prev_low:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"

    # Identify BOS and CHoCH
    bos_list = []
    choch_list = []

    if len(swing_highs) >= 3:
        # Check for BOS
        if swing_highs[-1][1] > swing_highs[-2][1] and swing_highs[-2][1] > swing_highs[-3][1]:
            bos_list.append({
                "type": "BOS",
                "direction": "BUY",
                "level": swing_highs[-1][1],
                "message": f"Break of structure to upside at {swing_highs[-1][1]:.2f}"
            })

        # Check for CHoCH
        if swing_highs[-1][1] < swing_highs[-2][1] and swing_lows[-1][1] < swing_lows[-2][1]:
            choch_list.append({
                "type": "CHoCH",
                "direction": "SELL",
                "level": swing_highs[-1][1],
                "message": f"Change of character at {swing_highs[-1][1]:.2f}"
            })

    return {
        "trend": trend,
        "last_hh": swing_highs[-1][1] if swing_highs else 0,
        "last_ll": swing_lows[-1][1] if swing_lows else 0,
        "last_hl": swing_lows[-1][1] if swing_lows and len(swing_lows) > 1 else 0,
        "bos_list": bos_list,
        "choch_list": choch_list,
    }


def find_order_blocks(df):
    """Identify order blocks"""
    if len(df) < 20:
        return []

    order_blocks = []
    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values

    # Look for bullish and bearish order blocks
    for i in range(3, len(df) - 1):
        # Bullish order block: strong up move after a down move
        if close[i] > close[i-1] and close[i-1] < close[i-2]:
            if close[i] > df['ema_21'].iloc[i]:
                order_blocks.append({
                    "pattern_type": "BULLISH_ORDER_BLOCK",
                    "direction": "BUY",
                    "timestamp": df.index[i].isoformat(),
                    "low": low[i-1],
                    "high": high[i-1],
                    "strength": 0.7,
                    "description": f"Bullish OB at {low[i-1]:.2f} - {high[i-1]:.2f}"
                })

        # Bearish order block: strong down move after an up move
        if close[i] < close[i-1] and close[i-1] > close[i-2]:
            if close[i] < df['ema_21'].iloc[i]:
                order_blocks.append({
                    "pattern_type": "BEARISH_ORDER_BLOCK",
                    "direction": "SELL",
                    "timestamp": df.index[i].isoformat(),
                    "low": low[i-1],
                    "high": high[i-1],
                    "strength": 0.7,
                    "description": f"Bearish OB at {low[i-1]:.2f} - {high[i-1]:.2f}"
                })

    # Return last 10 order blocks
    return order_blocks[-10:]


def find_fvg(df):
    """Find Fair Value Gaps"""
    if len(df) < 10:
        return []

    fvgs = []

    for i in range(2, len(df) - 1):
        # Bullish FVG: gap up
        if df['Low'].iloc[i] > df['High'].iloc[i-2]:
            fvgs.append({
                "pattern_type": "BULLISH_FVG",
                "direction": "BUY",
                "timestamp": df.index[i].isoformat(),
                "low": df['High'].iloc[i-2],
                "high": df['Low'].iloc[i],
                "size": df['Low'].iloc[i] - df['High'].iloc[i-2],
                "description": f"Bullish FVG from {df['High'].iloc[i-2]:.2f} to {df['Low'].iloc[i]:.2f}"
            })

        # Bearish FVG: gap down
        if df['High'].iloc[i] < df['Low'].iloc[i-2]:
            fvgs.append({
                "pattern_type": "BEARISH_FVG",
                "direction": "SELL",
                "timestamp": df.index[i].isoformat(),
                "low": df['High'].iloc[i],
                "high": df['Low'].iloc[i-2],
                "size": df['Low'].iloc[i-2] - df['High'].iloc[i],
                "description": f"Bearish FVG from {df['Low'].iloc[i-2]:.2f} to {df['High'].iloc[i]:.2f}"
            })

    return fvgs[-10:]


def find_liquidity_levels(df):
    """Find buy-side and sell-side liquidity levels"""
    if len(df) < 20:
        return {"bsl": [], "ssl": [], "equal_highs": [], "equal_lows": []}

    high = df['High'].values
    low = df['Low'].values

    # Find swing highs
    swing_highs = []
    for i in range(5, len(df) - 5):
        if high[i] > max(high[i-5:i]) and high[i] > max(high[i+1:i+6]):
            swing_highs.append(high[i])

    # Find swing lows
    swing_lows = []
    for i in range(5, len(df) - 5):
        if low[i] < min(low[i-5:i]) and low[i] < min(low[i+1:i+6]):
            swing_lows.append(low[i])

    # BSL: Buy-side liquidity (swing highs)
    bsl = [{"level": sh, "description": "BSL"} for sh in swing_highs[-5:]]

    # SSL: Sell-side liquidity (swing lows)
    ssl = [{"level": sl, "description": "SSL"} for sl in swing_lows[-5:]]

    # Equal highs/lows (within 0.5%)
    equal_highs = []
    equal_lows = []

    for i in range(len(swing_highs)):
        for j in range(i+1, len(swing_highs)):
            if abs(swing_highs[i] - swing_highs[j]) / swing_highs[i] < 0.005:
                equal_highs.append({
                    "level": swing_highs[i],
                    "description": "Equal Highs"
                })

    for i in range(len(swing_lows)):
        for j in range(i+1, len(swing_lows)):
            if abs(swing_lows[i] - swing_lows[j]) / swing_lows[i] < 0.005:
                equal_lows.append({
                    "level": swing_lows[i],
                    "description": "Equal Lows"
                })

    return {
        "bsl": bsl,
        "ssl": ssl,
        "equal_highs": equal_highs[:3],
        "equal_lows": equal_lows[:3],
    }


def calculate_premium_discount(df):
    """Calculate premium/discount zone"""
    if len(df) < 20:
        return {}

    high = df['High'].max()
    low = df['Low'].min()
    current = df['Close'].iloc[-1]

    range_size = high - low
    if range_size == 0:
        return {}

    position_pct = ((current - low) / range_size) * 100
    equilibrium = (high + low) / 2

    if position_pct > 70:
        zone = "PREMIUM"
        message = "Price in premium zone - Look for sell setups"
    elif position_pct < 30:
        zone = "DISCOUNT"
        message = "Price in discount zone - Look for buy setups"
    else:
        zone = "MIDRANGE"
        message = "Price in midrange - Wait for premium or discount"

    return {
        "zone": zone,
        "position_pct": position_pct,
        "equilibrium": equilibrium,
        "swing_high": high,
        "swing_low": low,
        "message": message,
    }


def check_kill_zones():
    """Check if current time is within kill zones"""
    current_hour = datetime.now().hour

    for zone_name, zone_times in config.KILL_ZONES.items():
        start = zone_times["start"]
        end = zone_times["end"]

        # Handle overnight zones
        if start > end:  # e.g., 23-1
            if current_hour >= start or current_hour < end:
                return {
                    "active": True,
                    "zone": zone_name,
                    "message": f"🔥 {zone_name} Kill Zone active! (UTC {start}:00-{end}:00)"
                }
        else:
            if start <= current_hour < end:
                return {
                    "active": True,
                    "zone": zone_name,
                    "message": f"🔥 {zone_name} Kill Zone active! (UTC {start}:00-{end}:00)"
                }

    return {
        "active": False,
        "message": "No active kill zone. Next: London (7-9 UTC)"
    }


def analyze_power_of_3(df):
    """Analyze Accumulation-Manipulation-Distribution"""
    if len(df) < 50:
        return {"phase": "RANGING", "message": "Insufficient data for PO3 analysis"}

    # Simple PO3 detection based on range and volatility
    recent_high = df['High'].iloc[-20:].max()
    recent_low = df['Low'].iloc[-20:].min()
    range_size = recent_high - recent_low
    current_price = df['Close'].iloc[-1]
    atr = df['atr'].iloc[-1] if 'atr' in df else range_size

    # Determine phase
    if range_size < atr * 0.5:
        phase = "ACCUMULATION"
        message = "🔄 Accumulation phase - Range bound, building for breakout"
    elif current_price > recent_high - range_size * 0.2:
        phase = "DISTRIBUTION_UP"
        message = "📈 Distribution to upside - Breakout above range"
    elif current_price < recent_low + range_size * 0.2:
        phase = "DISTRIBUTION_DOWN"
        message = "📉 Distribution to downside - Breakdown below range"
    else:
        # Check for manipulation
        if len(df) > 30:
            prev_range_high = df['High'].iloc[-40:-20].max()
            prev_range_low = df['Low'].iloc[-40:-20].min()
            if current_price < prev_range_low or current_price > prev_range_high:
                phase = "MANIPULATION"
                message = "🎯 Manipulation phase - False breakout before reversal"
            else:
                phase = "RANGING"
                message = "⏳ Ranging market - Waiting for direction"
        else:
            phase = "RANGING"
            message = "⏳ Ranging market - Waiting for direction"

    return {"phase": phase, "message": message}


def find_breaker_blocks(df):
    """Find breaker blocks"""
    if len(df) < 20:
        return []

    breakers = []
    order_blocks = find_order_blocks(df)

    for ob in order_blocks:
        # A breaker block occurs when price breaks an order block
        current = df['Close'].iloc[-1]

        if ob['direction'] == 'BUY' and current > ob['high']:
            breakers.append({
                "pattern_type": "BREAKER_BLOCK",
                "direction": "BUY",
                "low": ob['low'],
                "high": ob['high'],
                "description": f"Breaker block formed above {ob['high']:.2f}"
            })
        elif ob['direction'] == 'SELL' and current < ob['low']:
            breakers.append({
                "pattern_type": "BREAKER_BLOCK",
                "direction": "SELL",
                "low": ob['low'],
                "high": ob['high'],
                "description": f"Breaker block formed below {ob['low']:.2f}"
            })

    return breakers[-5:]


def find_displacement(df):
    """Find displacement moves"""
    if len(df) < 10:
        return []

    displacements = []

    for i in range(3, len(df)):
        # Look for strong moves (2x ATR)
        if 'atr' in df:
            atr = df['atr'].iloc[i]
            move = abs(df['Close'].iloc[i] - df['Close'].iloc[i-1])

            if move > atr * 2:
                direction = "BUY" if df['Close'].iloc[i] > df['Close'].iloc[i-1] else "SELL"
                displacements.append({
                    "pattern_type": "DISPLACEMENT",
                    "direction": direction,
                    "timestamp": df.index[i].isoformat(),
                    "magnitude": move,
                    "description": f"Displacement {direction} of {move:.2f} pts"
                })

    return displacements[-5:]


def calculate_bias(df):
    """Calculate overall bias"""
    if len(df) < 20:
        return "NEUTRAL"

    # Combine multiple indicators
    score = 0

    # EMAs
    if df['Close'].iloc[-1] > df['ema_21'].iloc[-1]:
        score += 1
    if df['Close'].iloc[-1] > df['ema_50'].iloc[-1]:
        score += 1
    if df['Close'].iloc[-1] > df['ema_200'].iloc[-1]:
        score += 1

    # RSI
    if 'rsi' in df and df['rsi'].iloc[-1] > 50:
        score += 1
    elif 'rsi' in df and df['rsi'].iloc[-1] < 50:
        score -= 1

    # MACD
    if 'macd' in df and df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]:
        score += 1
    elif 'macd' in df:
        score -= 1

    # Trend
    structure = analyze_market_structure(df)
    if structure.get('trend') == "BULLISH":
        score += 2
    elif structure.get('trend') == "BEARISH":
        score -= 2

    if score > 0:
        return "BUY"
    elif score < 0:
        return "SELL"
    else:
        return "NEUTRAL"


def calculate_confluence(ict_data):
    """Calculate buy/sell confluence"""
    buy_score = 0
    sell_score = 0

    # Check structure
    structure = ict_data.get('structure', {})
    if structure.get('trend') == "BULLISH":
        buy_score += 2
    elif structure.get('trend') == "BEARISH":
        sell_score += 2

    # Check order blocks
    for ob in ict_data.get('order_blocks', [])[-3:]:
        if ob['direction'] == "BUY":
            buy_score += 1
        else:
            sell_score += 1

    # Check FVGs
    for fvg in ict_data.get('fair_value_gaps', [])[-3:]:
        if fvg['direction'] == "BUY":
            buy_score += 1
        else:
            sell_score += 1

    # Check premium/discount
    pd = ict_data.get('premium_discount', {})
    if pd.get('zone') == "DISCOUNT":
        buy_score += 1
    elif pd.get('zone') == "PREMIUM":
        sell_score += 1

    # Check bias
    bias = ict_data.get('bias', 'NEUTRAL')
    if bias == "BUY":
        buy_score += 2
    elif bias == "SELL":
        sell_score += 2

    return buy_score, sell_score


def calculate_sl_tp(ict_data, df):
    """Calculate suggested SL and TP"""
    if df.empty:
        return 0, 0, 0

    current = df['Close'].iloc[-1]
    atr = df['atr'].iloc[-1] if 'atr' in df else 5

    # Determine direction from bias
    bias = ict_data.get('bias', 'NEUTRAL')
    buy_score = ict_data.get('confluence_buy', 0)
    sell_score = ict_data.get('confluence_sell', 0)

    if bias == "BUY" or buy_score > sell_score:
        # BUY setup
        sl = current - atr * 1.5
        tp = current + atr * 3
        rr = (tp - current) / (current - sl) if (current - sl) > 0 else 0
    elif bias == "SELL" or sell_score > buy_score:
        # SELL setup
        sl = current + atr * 1.5
        tp = current - atr * 3
        rr = (current - tp) / (sl - current) if (sl - current) > 0 else 0
    else:
        # Neutral - use ATR-based
        sl = current - atr * 1.5
        tp = current + atr * 2
        rr = (tp - current) / (current - sl) if (current - sl) > 0 else 0

    return sl, tp, rr