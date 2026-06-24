"""
🥇 XAUUSD AI Trading Partner
==============================
Full ICT-powered gold trading dashboard.
Run with:  streamlit run app.py
"""

import sys
import os

# Add the current directory to Python's path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json
from datetime import datetime

# ── Page config (must be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="🥇 XAUUSD AI Trading Partner",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports ─────────────────────────────────────────────────────
import config
from core.database import Database
from core.data_fetcher import fetch_ohlcv, fetch_live_price, fetch_correlated_assets, add_indicators, fetch_gold_news, get_macro_bias
from core.ict_engine import full_ict_analysis
from core.ai_engine import MLSignalEngine, ClaudeTradingPartner
from core.risk_manager import RiskManager
from core.learning import LearningEngine


# ── Session State Init ──────────────────────────────────────────
def init_state():
    defaults = {
        "db": Database(),
        "ml": MLSignalEngine(),
        "risk": RiskManager(),
        "last_refresh": 0,
        "ict_cache": {},
        "df_cache": {},
        "news": [],
        "chat_input": "",
        "balance": config.DEFAULT_ACCOUNT_BALANCE,
        "auto_refresh": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Lazy-init after db is ready
    if "claude" not in st.session_state:
        st.session_state["claude"] = ClaudeTradingPartner(st.session_state["db"])
    if "learning" not in st.session_state:
        st.session_state["learning"] = LearningEngine(
            st.session_state["db"], st.session_state["ml"])


init_state()

db = st.session_state["db"]
ml = st.session_state["ml"]
risk = st.session_state["risk"]
claude = st.session_state["claude"]
learning = st.session_state["learning"]


# ── Helpers ─────────────────────────────────────────────────────

def refresh_data(timeframe: str):
    """Fetch fresh market data and run ICT analysis."""
    df = fetch_ohlcv(timeframe)
    if df is not None and not df.empty:
        df = add_indicators(df)
        ict = full_ict_analysis(df, timeframe)
        st.session_state["df_cache"][timeframe] = df
        st.session_state["ict_cache"][timeframe] = ict
        return df, ict
    return pd.DataFrame(), {}


def get_cached(timeframe: str):
    df = st.session_state["df_cache"].get(timeframe)
    ict = st.session_state["ict_cache"].get(timeframe)
    return df, ict


def candlestick_chart(df: pd.DataFrame, ict: dict, timeframe: str) -> go.Figure:
    """Build an annotated candlestick chart with ICT overlays."""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.65, 0.20, 0.15],
        subplot_titles=("XAUUSD Price (ICT Annotated)", "RSI", "MACD"),
    )

    # ── Candles
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color=config.CANDLE_UP_COLOR,
        decreasing_line_color=config.CANDLE_DOWN_COLOR,
        name="XAUUSD",
    ), row=1, col=1)

    # ── EMAs
    for ema, color, width in [("ema_21", "#FFD700", 1.5), ("ema_50", "#FF8C00", 1.5), ("ema_200", "#FFFFFF", 2)]:
        if ema in df:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ema], name=ema.upper(),
                line=dict(color=color, width=width), opacity=0.8
            ), row=1, col=1)

    # ── Order Blocks
    obs = ict.get("order_blocks", [])
    for ob in obs[-6:]:
        color = "rgba(38,166,154,0.15)" if ob["direction"] == "BUY" else "rgba(239,83,80,0.15)"
        border = config.CANDLE_UP_COLOR if ob["direction"] == "BUY" else config.CANDLE_DOWN_COLOR
        try:
            x0 = pd.Timestamp(ob["timestamp"])
            x1 = df.index[-1]
            fig.add_shape(type="rect", x0=x0, x1=x1,
                          y0=ob["low"], y1=ob["high"],
                          fillcolor=color, line=dict(color=border, width=1),
                          layer="below", row=1, col=1)
            fig.add_annotation(x=x1, y=(ob["high"]+ob["low"])/2,
                               text=f"{'Bull' if ob['direction']=='BUY' else 'Bear'} OB",
                               font=dict(size=9, color=border), showarrow=False,
                               xref="x", yref="y")
        except:
            pass

    # ── Fair Value Gaps
    fvgs = ict.get("fair_value_gaps", [])
    for fvg in fvgs[-4:]:
        color = "rgba(38,166,154,0.08)" if fvg["direction"] == "BUY" else "rgba(239,83,80,0.08)"
        try:
            x0 = pd.Timestamp(fvg["timestamp"])
            x1 = df.index[-1]
            fig.add_shape(type="rect", x0=x0, x1=x1,
                          y0=fvg["low"], y1=fvg["high"],
                          fillcolor=color,
                          line=dict(color="#888888", width=0.5, dash="dot"),
                          layer="below", row=1, col=1)
        except:
            pass

    # ── Premium / Discount
    pd_data = ict.get("premium_discount", {})
    if pd_data.get("equilibrium"):
        fig.add_hline(y=pd_data["equilibrium"], line_dash="dash",
                      line_color="#FFD700", line_width=1,
                      annotation_text="EQ (50%)", annotation_position="right",
                      row=1, col=1)
    if pd_data.get("swing_high"):
        fig.add_hline(y=pd_data["swing_high"], line_dash="dot",
                      line_color="#ef5350", line_width=1,
                      annotation_text="Swing H", annotation_position="right",
                      row=1, col=1)
    if pd_data.get("swing_low"):
        fig.add_hline(y=pd_data["swing_low"], line_dash="dot",
                      line_color="#26a69a", line_width=1,
                      annotation_text="Swing L", annotation_position="right",
                      row=1, col=1)

    # ── Liquidity levels
    liq = ict.get("liquidity", {})
    for bsl in liq.get("bsl", [])[:3]:
        try:
            fig.add_hline(y=bsl["level"], line_dash="dot",
                          line_color="#29b6f6", line_width=0.8,
                          annotation_text="BSL", row=1, col=1)
        except:
            pass
    for ssl in liq.get("ssl", [])[:3]:
        try:
            fig.add_hline(y=ssl["level"], line_dash="dot",
                          line_color="#ff7043", line_width=0.8,
                          annotation_text="SSL", row=1, col=1)
        except:
            pass

    # ── RSI
    if "rsi" in df:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["rsi"], name="RSI",
            line=dict(color="#9c27b0", width=1.5)
        ), row=2, col=1)
        for lvl, color in [(70, "#ef5350"), (30, "#26a69a"), (50, "#555555")]:
            fig.add_hline(y=lvl, line_color=color, line_width=0.7,
                          line_dash="dash", row=2, col=1)
        fig.update_yaxes(range=[0, 100], row=2, col=1)

    # ── MACD
    if "macd" in df:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["macd"], name="MACD",
            line=dict(color="#2196f3", width=1)
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["macd_signal"], name="Signal",
            line=dict(color="#ff9800", width=1)
        ), row=3, col=1)
        colors_hist = df["macd_hist"].apply(
            lambda x: config.CANDLE_UP_COLOR if x >= 0 else config.CANDLE_DOWN_COLOR)
        fig.add_trace(go.Bar(
            x=df.index, y=df["macd_hist"], name="Hist",
            marker_color=colors_hist, opacity=0.7
        ), row=3, col=1)

    fig.update_layout(
        template=config.CHART_THEME,
        height=700,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", y=1.02),
        margin=dict(l=50, r=80, t=50, b=30),
        font=dict(size=11),
    )
    return fig


def signal_card(signal_type: str, conf: float, ict: dict, tf: str):
    """Render a signal card."""
    emoji = "🟢" if signal_type == "BUY" else ("🔴" if signal_type == "SELL" else "⬛")
    color = "#1b5e20" if signal_type == "BUY" else ("#b71c1c" if signal_type == "SELL" else "#333")
    ep = ict.get("current_price", 0)
    sl = ict.get("suggested_sl", 0)
    tp = ict.get("suggested_tp", 0)
    rr = ict.get("rr_ratio", 0)

    st.markdown(f"""
    <div style="background:{color};border-radius:10px;padding:16px;margin:4px 0;">
        <h2 style="color:white;margin:0;">{emoji} {signal_type} SIGNAL</h2>
        <p style="color:#eee;margin:4px 0;">Confidence: {conf*100:.0f}% | {tf} | {datetime.now().strftime('%H:%M UTC')}</p>
        <table style="color:white;width:100%">
            <tr><td><b>Entry</b></td><td>${ep:.2f}</td></tr>
            <tr><td><b>Stop Loss</b></td><td>${sl:.2f}</td></tr>
            <tr><td><b>Take Profit</b></td><td>${tp:.2f}</td></tr>
            <tr><td><b>R:R</b></td><td>1:{rr:.2f}</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🥇 Gold AI Partner")
    st.caption("ICT-Powered XAUUSD Analysis")
    st.divider()

    # Live price
    live = fetch_live_price()
    price = live["price"]
    chg = live["change"]
    pct = live["pct"]
    chg_color = "#26a69a" if chg >= 0 else "#ef5350"
    chg_arrow = "▲" if chg >= 0 else "▼"

    st.markdown(f"""
    <div style="background:#1a1a2e;border-radius:8px;padding:12px;text-align:center">
        <p style="color:#FFD700;font-size:28px;font-weight:bold;margin:0">
            ${price:,.2f}
        </p>
        <p style="color:{chg_color};margin:0">
            {chg_arrow} {abs(chg):.2f} ({abs(pct):.2f}%)
        </p>
        <p style="color:#888;font-size:11px;margin:4px 0">{live['time']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Correlated assets
    corr = fetch_correlated_assets()
    col1, col2 = st.columns(2)
    col1.metric("💵 DXY", f"{corr.get('DXY', 0):.2f}")
    col2.metric("📈 US10Y", f"{corr.get('US10Y', 0):.2f}%")

    st.divider()

    # Settings
    st.subheader("⚙️ Settings")
    tf_choice = st.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], index=1)
    balance = st.number_input("Account Balance ($)", value=st.session_state["balance"],
                              min_value=100.0, step=100.0)
    risk_pct = st.slider("Risk per Trade (%)", 0.5, 5.0, config.DEFAULT_RISK_PERCENT, 0.1)
    st.session_state["balance"] = balance
    risk.update_balance(balance)
    risk.risk_pct = risk_pct

    auto_ref = st.toggle("Auto-Refresh (60s)", value=True)
    st.session_state["auto_refresh"] = auto_ref

    if st.button("🔄 Refresh Now", use_container_width=True):
        with st.spinner("Fetching data …"):
            refresh_data(tf_choice)
        st.success("Refreshed!")

    st.divider()

    # API key status
    if config.ANTHROPIC_API_KEY:
        st.success("✅ AI Partner: Online")
    else:
        st.warning("⚠️ Add ANTHROPIC_API_KEY to .env for AI chat")
        st.markdown("[Get API Key →](https://console.anthropic.com/)")

    st.divider()

    # Account summary
    acct = risk.get_account_summary()
    st.subheader("💰 Account")
    st.metric("Balance", f"${acct['balance']:,.2f}")
    st.metric("Daily P&L", f"${acct['daily_pnl']:+.2f}",
              delta=f"{acct['daily_used_pct']:.0f}% of limit used")
    if not acct["can_trade"]:
        st.error("🚫 Daily loss limit reached!")


# ════════════════════════════════════════════════════════════════
#  MAIN CONTENT – TABS
# ════════════════════════════════════════════════════════════════
st.title(config.APP_TITLE)
st.caption(f"Inner Circle Trader methodology applied to XAUUSD | {datetime.now().strftime('%A, %d %B %Y')}")

tabs = st.tabs([
    "📊 Dashboard",
    "🎯 Signals",
    "📚 ICT Patterns",
    "🤖 AI Partner",
    "📒 Trade Journal",
    "📈 Performance",
    "📰 News & Macro",
])


# ─────────────────────────────────────────────
#  TAB 1 – DASHBOARD
# ─────────────────────────────────────────────
with tabs[0]:
    # Ensure data is loaded
    df, ict = get_cached(tf_choice)
    if df is None or df.empty:
        with st.spinner(f"Loading {tf_choice} data …"):
            df, ict = refresh_data(tf_choice)

    if df is None or df.empty:
        st.error("Could not fetch data. Check your internet connection.")
        st.stop()

    # Top metrics row
    c1, c2, c3, c4, c5 = st.columns(5)
    trend = ict.get("structure", {}).get("trend", "?")
    trend_emoji = "🟢" if trend == "BULLISH" else ("🔴" if trend == "BEARISH" else "⬛")
    c1.metric("Trend", f"{trend_emoji} {trend}")
    c2.metric("ATR", f"${ict.get('atr', 0):.2f}")
    c3.metric("ICT Bias", f"{'🟢' if ict.get('bias')=='BUY' else '🔴' if ict.get('bias')=='SELL' else '⬛'} {ict.get('bias','NEUTRAL')}")
    c4.metric("Buy Conf", f"{ict.get('confluence_buy', 0)} pts")
    c5.metric("Sell Conf", f"{ict.get('confluence_sell', 0)} pts")

    # Kill Zone banner
    kz = ict.get("kill_zone", {})
    if kz.get("active"):
        st.success(kz.get("message", ""))
    else:
        st.info(kz.get("message", ""))

    # Chart
    st.subheader(f"📉 XAUUSD – {tf_choice} Chart (ICT Annotated)")
    fig = candlestick_chart(df, ict, tf_choice)
    st.plotly_chart(fig, use_container_width=True)

    # Premium/Discount
    pd_data = ict.get("premium_discount", {})
    if pd_data:
        zone = pd_data.get("zone", "?")
        pos = pd_data.get("position_pct", 50)
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.subheader("Premium / Discount Zone")
            st.progress(int(pos), text=f"Price at {pos:.0f}% of range – {'🔴 PREMIUM' if zone=='PREMIUM' else '🟢 DISCOUNT'}")
            st.info(pd_data.get("message", ""))
        with col_b:
            st.subheader("Power of 3")
            amd = ict.get("power_of_3", {})
            phase = amd.get("phase", "?")
            p_colors = {
                "ACCUMULATION": "info",
                "MANIPULATION": "warning",
                "DISTRIBUTION_UP": "success",
                "DISTRIBUTION_DOWN": "error",
                "RANGING": "info",
            }
            getattr(st, p_colors.get(phase, "info"))(amd.get("message", "N/A"))

    # Auto-refresh countdown
    if st.session_state["auto_refresh"]:
        now = time.time()
        elapsed = now - st.session_state["last_refresh"]
        if elapsed >= config.REFRESH_SECONDS:
            st.session_state["last_refresh"] = now
            refresh_data(tf_choice)
            st.rerun()
        remaining = int(config.REFRESH_SECONDS - elapsed)
        st.caption(f"⏱ Auto-refresh in {remaining}s")


# ─────────────────────────────────────────────
#  TAB 2 – SIGNALS
# ─────────────────────────────────────────────
with tabs[1]:
    st.header("🎯 AI Trading Signals")

    df, ict = get_cached(tf_choice)
    if df is None or df.empty:
        df, ict = refresh_data(tf_choice)

    if ict:
        # Generate ML signal
        ml_result = ml.predict(df, ict)
        sig_type = ml_result["signal"]
        confidence = ml_result["confidence"]

        col_sig, col_card = st.columns([1, 1])

        with col_sig:
            signal_card(sig_type, confidence, ict, tf_choice)

            # Confidence bar
            st.metric("ML Confidence", f"{confidence*100:.0f}%",
                      help="Combined ICT confluence + ML model score")
            probas = ml_result.get("probabilities", {})
            for s, p in probas.items():
                bar_color = "#26a69a" if s == "BUY" else ("#ef5350" if s == "SELL" else "#666")
                st.markdown(f"""
                <div style="margin:3px 0">
                  <span style="color:#ccc;width:50px;display:inline-block">{s}</span>
                  <div style="display:inline-block;width:{int(p*200)}px;height:12px;
                              background:{bar_color};border-radius:4px;vertical-align:middle"></div>
                  <span style="color:#ccc;margin-left:8px">{p*100:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)

        with col_card:
            st.subheader("Risk Calculation")
            ep = ict.get("current_price", 0)
            sl = ict.get("suggested_sl", ep - ict.get("atr", 5) * 1.5)
            tp = ict.get("suggested_tp", ep + ict.get("atr", 5) * 3)

            ep = st.number_input("Entry Price", value=float(ep), step=0.1, format="%.2f")
            sl = st.number_input("Stop Loss", value=float(sl), step=0.1, format="%.2f")
            tp = st.number_input("Take Profit", value=float(tp), step=0.1, format="%.2f")

            validation = risk.validate_setup(ep, sl, tp, sig_type)
            lot = validation["lot_size"]

            st.metric("Lot Size", f"{lot} lots")
            st.metric("Risk Amount", f"${validation['risk_usd']:.2f}")
            st.metric("Reward Amount", f"${validation['reward_usd']:.2f}")
            st.metric("R:R Ratio", f"1:{validation['rr']}")

            for w in validation["warnings"]:
                st.warning(w)

            # Save signal button
            if sig_type != "HOLD" and confidence >= config.SIGNAL_CONFIDENCE_THRESHOLD:
                if st.button(f"💾 Log this {sig_type} Signal", type="primary"):
                    ict_patterns = (
                        ict.get("order_blocks", [])[:3] +
                        ict.get("fair_value_gaps", [])[:3]
                    )
                    sig_id = db.save_signal({
                        "timestamp": str(df.index[-1]),
                        "timeframe": tf_choice,
                        "signal_type": sig_type,
                        "confidence": confidence,
                        "entry_price": ep,
                        "stop_loss": sl,
                        "take_profit": tp,
                        "rr_ratio": validation["rr"],
                        "ict_patterns": ict_patterns,
                        "indicators": {
                            "rsi": float(df["rsi"].iloc[-1]) if "rsi" in df else 0,
                            "trend": ict.get("structure", {}).get("trend", "?"),
                        },
                    })
                    st.success(f"✅ Signal #{sig_id} logged to database!")

        # Recent Signals table
        st.divider()
        st.subheader("Recent Signals")
        recent = db.get_signals(limit=20)
        if not recent.empty:
            display = recent[["timestamp", "timeframe", "signal_type",
                              "confidence", "entry_price", "stop_loss",
                              "take_profit", "rr_ratio", "outcome"]].copy()
            display.columns = ["Time", "TF", "Signal", "Conf", "Entry", "SL", "TP", "R:R", "Outcome"]
            display["Conf"] = display["Conf"].apply(lambda x: f"{x*100:.0f}%")
            st.dataframe(display, use_container_width=True)
        else:
            st.info("No signals logged yet. Generate your first signal above!")


# ─────────────────────────────────────────────
#  TAB 3 – ICT PATTERNS
# ─────────────────────────────────────────────
with tabs[2]:
    st.header("📚 ICT Pattern Analysis")

    df, ict = get_cached(tf_choice)
    if df is None or df.empty:
        df, ict = refresh_data(tf_choice)

    if ict:
        # Market Structure
        st.subheader("🏗 Market Structure")
        ms = ict.get("structure", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Trend", ms.get("trend", "?"))
        c2.metric("Last HH", f"${ms.get('last_hh', 0):.2f}")
        c3.metric("Last LL", f"${ms.get('last_ll', 0):.2f}")
        c4.metric("Last HL", f"${ms.get('last_hl', 0):.2f}")

        bos = ms.get("bos_list", [])
        cho = ms.get("choch_list", [])
        if bos:
            for b in bos:
                st.success(b.get("message", "BOS detected"))
        if cho:
            for c in cho:
                st.warning(c.get("message", "CHoCH detected"))

        st.divider()

        # Order Blocks
        col_ob, col_fvg = st.columns(2)
        with col_ob:
            st.subheader("🧱 Order Blocks")
            obs = ict.get("order_blocks", [])
            if obs:
                for ob in obs[-5:]:
                    emoji = "🟢" if ob["direction"] == "BUY" else "🔴"
                    st.markdown(f"""
                    <div style="border-left:3px solid {'#26a69a' if ob['direction']=='BUY' else '#ef5350'};
                                padding:8px;margin:4px 0;background:#1a1a2e;border-radius:4px">
                        <b>{emoji} {ob['pattern_type'].replace('_', ' ')}</b><br>
                        <small>Zone: ${ob['low']:.2f} – ${ob['high']:.2f}</small><br>
                        <small>Strength: {ob['strength']*100:.0f}%</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No active Order Blocks detected")

        with col_fvg:
            st.subheader("⚡ Fair Value Gaps")
            fvgs = ict.get("fair_value_gaps", [])
            if fvgs:
                for fvg in fvgs[-5:]:
                    emoji = "🟢" if fvg["direction"] == "BUY" else "🔴"
                    st.markdown(f"""
                    <div style="border-left:3px solid {'#26a69a' if fvg['direction']=='BUY' else '#ef5350'};
                                padding:8px;margin:4px 0;background:#1a1a2e;border-radius:4px">
                        <b>{emoji} {fvg['pattern_type'].replace('_', ' ')}</b><br>
                        <small>Gap: ${fvg['low']:.2f} – ${fvg['high']:.2f}</small><br>
                        <small>Size: {fvg['size']:.2f} pts</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No active FVGs detected")

        st.divider()

        # Liquidity
        st.subheader("💧 Liquidity Levels")
        liq = ict.get("liquidity", {})
        col_bsl, col_ssl = st.columns(2)
        with col_bsl:
            st.markdown("**BSL (Buy-Side Liquidity) – Highs**")
            bsl_all = liq.get("bsl", []) + liq.get("equal_highs", [])
            for b in bsl_all[:4]:
                st.markdown(f"🔵 `${b['level']:.2f}` — {b.get('description', 'BSL')}")
        with col_ssl:
            st.markdown("**SSL (Sell-Side Liquidity) – Lows**")
            ssl_all = liq.get("ssl", []) + liq.get("equal_lows", [])
            for s in ssl_all[:4]:
                st.markdown(f"🟠 `${s['level']:.2f}` — {s.get('description', 'SSL')}")

        st.divider()

        # Breaker Blocks
        breakers = ict.get("breaker_blocks", [])
        if breakers:
            st.subheader("💥 Breaker Blocks")
            for bb in breakers:
                emoji = "🟢" if bb["direction"] == "BUY" else "🔴"
                st.markdown(f"{emoji} **{bb['pattern_type'].replace('_', ' ')}** @ ${bb['low']:.2f}–${bb['high']:.2f}")

        # Displacement
        disps = ict.get("displacement", [])
        if disps:
            st.subheader("⚡ Recent Displacements")
            for d in disps[-3:]:
                emoji = "🟢" if d["direction"] == "BUY" else "🔴"
                st.markdown(f"{emoji} {d['description']}")


# ─────────────────────────────────────────────
#  TAB 4 – AI PARTNER
# ─────────────────────────────────────────────
with tabs[3]:
    st.header("🤖 AI Trading Partner")
    st.caption("Powered by Claude (Anthropic) | Trained in ICT methodology")

    if not config.ANTHROPIC_API_KEY:
        st.warning("""
        **API Key Required for Full AI Chat**

        To use the AI partner:
        1. Get your key at https://console.anthropic.com/
        2. Add to the `.env` file: `ANTHROPIC_API_KEY=your_key_here`
        3. Restart the app

        The system still runs full ICT analysis and signals without the API key.
        """)

    # ICT Concept reference
    with st.expander("📚 ICT Quick Reference – Click any to learn"):
        concepts = [
            "Order Blocks", "Fair Value Gaps", "Market Structure",
            "Kill Zones", "Premium and Discount", "OTE Fibonacci",
            "Power of 3 AMD", "Displacement", "Breaker Blocks",
            "Liquidity BSL SSL", "BOS and CHoCH", "Smart Money Concepts",
            "How to trade gold with ICT", "Daily Bias for XAUUSD",
            "Risk Management ICT style"
        ]
        cols = st.columns(3)
        for i, concept in enumerate(concepts):
            if cols[i % 3].button(concept, key=f"concept_{i}"):
                with st.spinner(f"Loading ICT lesson: {concept} …"):
                    _, cur_ict = get_cached(tf_choice)
                    response = claude.explain_concept(concept)
                st.markdown(f"### 📖 {concept}")
                st.markdown(response)

    st.divider()

    # Auto-analyze current setup
    _, cur_ict = get_cached(tf_choice)
    if cur_ict and st.button("🔍 Auto-Analyze Current Setup", type="primary"):
        with st.spinner("Asking AI to analyze the current XAUUSD setup …"):
            analysis = claude.analyze_setup(cur_ict)
        st.subheader("📊 AI Setup Analysis")
        st.markdown(analysis)
        db.save_message("assistant", analysis)

    st.divider()

    # Chat history
    st.subheader("💬 Chat with your Trading Partner")
    history = db.get_chat_history(limit=20)
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask about ICT, analyze a setup, or get trade ideas for XAUUSD …")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        _, cur_ict = get_cached(tf_choice)
        live_ctx = {
            "price": f"${fetch_live_price()['price']:,.2f}",
            "ict": cur_ict,
        }

        with st.chat_message("assistant"):
            with st.spinner("Thinking …"):
                reply = claude.chat(user_input, market_context=live_ctx)
            st.markdown(reply)

    # Clear chat
    if st.button("🗑 Clear Chat History"):
        db.clear_chat()
        st.rerun()


# ─────────────────────────────────────────────
#  TAB 5 – TRADE JOURNAL
# ─────────────────────────────────────────────
with tabs[4]:
    st.header("📒 Trade Journal")

    # Add trade form
    with st.expander("➕ Log a New Trade"):
        c1, c2 = st.columns(2)
        direction = c1.selectbox("Direction", ["BUY", "SELL"])
        setup_type = c2.selectbox("ICT Setup", [
            "Order Block", "FVG Fill", "OTE", "Breaker Block",
            "Liquidity Sweep", "BOS Retest", "CHoCH", "AMD Power of 3", "Other"
        ])

        c3, c4, c5 = st.columns(3)
        t_entry = c3.number_input("Entry", value=float(fetch_live_price()["price"]), step=0.1, format="%.2f")
        t_sl = c4.number_input("Stop Loss", value=float(t_entry - 10 if direction == "BUY" else t_entry + 10), step=0.1, format="%.2f")
        t_tp = c5.number_input("Take Profit", value=float(t_entry + 20 if direction == "BUY" else t_entry - 20), step=0.1, format="%.2f")

        t_notes = st.text_area("Trade Notes / Reason", placeholder="Why are you taking this trade? ICT confluences?")

        if st.button("💾 Log Trade", type="primary"):
            validation = risk.validate_setup(t_entry, t_sl, t_tp, direction)
            lot_info = risk.calculate_lot_size(t_entry, t_sl)

            trade_id = db.save_trade({
                "timestamp": datetime.now().isoformat(),
                "direction": direction,
                "entry_price": t_entry,
                "stop_loss": t_sl,
                "take_profit": t_tp,
                "lot_size": lot_info["lot_size"],
                "risk_usd": lot_info["risk_usd"],
                "reward_usd": validation["reward_usd"],
                "rr_ratio": validation["rr"],
                "ict_setup": setup_type,
                "notes": t_notes,
            })
            st.success(f"✅ Trade #{trade_id} logged!")

    # Open trades
    st.subheader("📂 Open Trades")
    open_trades = db.get_open_trades()
    if not open_trades.empty:
        for _, t in open_trades.iterrows():
            curr_price = fetch_live_price()["price"]
            if curr_price > 0:
                if t["direction"] == "BUY":
                    unrealized = (curr_price - t["entry_price"]) * t["lot_size"] * 100
                else:
                    unrealized = (t["entry_price"] - curr_price) * t["lot_size"] * 100
            else:
                unrealized = 0

            color = "#1b5e20" if unrealized >= 0 else "#b71c1c"
            st.markdown(f"""
            <div style="background:#1a1a2e;border-radius:8px;padding:12px;margin:6px 0;
                        border-left:4px solid {'#26a69a' if t['direction']=='BUY' else '#ef5350'}">
                <b>#{t['id']} {t['direction']} XAUUSD</b> — {t['ict_setup']}<br>
                Entry: ${t['entry_price']:.2f} | SL: ${t['stop_loss']:.2f} | TP: ${t['take_profit']:.2f}<br>
                <span style="color:{color}">Unrealized P&L: ${unrealized:+.2f}</span>
            </div>
            """, unsafe_allow_html=True)

            col_cl, col_sp = st.columns([1, 4])
            if col_cl.button(f"Close #{t['id']}", key=f"close_{t['id']}"):
                cp = fetch_live_price()["price"]
                if t["direction"] == "BUY":
                    pnl = (cp - t["entry_price"]) * float(t["lot_size"]) * 100
                else:
                    pnl = (t["entry_price"] - cp) * float(t["lot_size"]) * 100
                db.close_trade(t["id"], cp, pnl)
                risk.record_pnl(pnl)
                st.success(f"Trade #{t['id']} closed. P&L: ${pnl:+.2f}")
                st.rerun()
    else:
        st.info("No open trades. Log a trade above when you enter the market.")

    # Trade history
    st.subheader("📜 Trade History")
    all_trades = db.get_trades()
    if not all_trades.empty:
        closed_t = all_trades[all_trades["status"] != "OPEN"]
        if not closed_t.empty:
            display = closed_t[["id", "direction", "entry_price", "stop_loss",
                                "take_profit", "rr_ratio", "lot_size",
                                "status", "pnl_usd", "ict_setup"]].copy()
            display.columns = ["#", "Dir", "Entry", "SL", "TP", "R:R", "Lots", "Result", "P&L", "Setup"]
            st.dataframe(display.style.applymap(
                lambda v: "color: #26a69a" if v == "WIN"
                else "color: #ef5350" if v == "LOSS" else "",
                subset=["Result"]
            ), use_container_width=True)


# ─────────────────────────────────────────────
#  TAB 6 – PERFORMANCE
# ─────────────────────────────────────────────
with tabs[5]:
    st.header("📈 AI Performance & Learning")

    report = learning.get_full_performance_report()
    stats = report["summary"]

    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Signals", stats.get("total_signals", 0))
    c2.metric("Total Trades", stats.get("total_trades", 0))
    c3.metric("Win Rate", f"{stats.get('win_rate', 0):.1f}%")
    c4.metric("Net P&L", f"${stats.get('net_pnl', 0):+.2f}")
    c5.metric("Avg R:R", f"1:{stats.get('avg_rr', 0):.2f}")

    # Streak
    st.markdown(f"**Current Streak:** {report['current_streak']} × {report['streak_type']}")

    st.divider()

    col_l, col_r = st.columns(2)
    with col_l:
        # Pattern win rates
        st.subheader("🏆 ICT Pattern Performance")
        pat_df = report["patterns"]
        if not isinstance(pat_df, pd.DataFrame) or pat_df.empty:
            st.info("Trade more to see pattern performance statistics.")
        else:
            for _, row in pat_df.iterrows():
                wr = float(str(row["Win Rate"]).replace("%", ""))
                color = "#26a69a" if wr >= 55 else ("#ff9800" if wr >= 45 else "#ef5350")
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                            background:#1a1a2e;padding:8px;border-radius:4px;margin:3px 0">
                    <span>{row['Pattern'].replace('_', ' ')}</span>
                    <span style="color:{color}"><b>{row['Win Rate']}</b> ({row['Total']} trades)</span>
                </div>
                """, unsafe_allow_html=True)

    with col_r:
        # AI suggestions
        st.subheader("💡 AI Improvement Tips")
        suggestions = learning.suggest_improvements()
        for s in suggestions:
            st.info(s)

        st.subheader("🕐 Kill Zone Stats (Historical)")
        for zone, data in report["kill_zones"].items():
            st.markdown(f"**{zone}**: {data['win_rate']} — _{data['note']}_")

    st.divider()

    # Retrain button
    st.subheader("🧠 Model Management")
    col_tr, col_info = st.columns([1, 2])
    with col_tr:
        if st.button("🔄 Retrain AI Model Now", type="primary"):
            with st.spinner("Retraining …"):
                learning.retrain()
            st.success("Model retrained!")
    with col_info:
        st.info(f"""
        **Model Version:** {report['model_version']}
        **Model Trained:** {'Yes' if report['model_trained'] else 'No (will use ICT-only signals)'}

        The AI automatically retrains every {config.ML_RETRAIN_EVERY_N_SIGNALS} resolved signals.
        More trades = smarter AI.
        """)

    # Performance history chart
    history = report["history"]
    if isinstance(history, pd.DataFrame) and not history.empty:
        st.subheader("📊 Win Rate Over Time")
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Scatter(
            x=history["date"], y=history["win_rate"] * 100,
            mode="lines+markers", name="Win Rate %",
            line=dict(color="#FFD700", width=2)
        ))
        fig_perf.update_layout(
            template=config.CHART_THEME, height=300,
            yaxis=dict(range=[0, 100], title="Win Rate %")
        )
        st.plotly_chart(fig_perf, use_container_width=True)


# ─────────────────────────────────────────────
#  TAB 7 – NEWS & MACRO
# ─────────────────────────────────────────────
with tabs[6]:
    st.header("📰 Gold News & Macro Sentiment")

    if st.button("🔄 Refresh News") or not st.session_state["news"]:
        with st.spinner("Fetching gold news …"):
            news = fetch_gold_news()
            db.save_news(news)
            st.session_state["news"] = news

    news = st.session_state.get("news", [])
    if news:
        macro = get_macro_bias(news)
        bias_color = "#1b5e20" if macro["bias"] == "BULLISH" else \
            "#b71c1c" if macro["bias"] == "BEARISH" else "#333"
        st.markdown(f"""
        <div style="background:{bias_color};border-radius:10px;padding:12px;text-align:center;margin-bottom:16px">
            <h3 style="color:white;margin:0">News Macro Bias: {macro['label']}</h3>
            <p style="color:#ddd;margin:4px 0">Sentiment Score: {macro['score']:+.2f}</p>
        </div>
        """, unsafe_allow_html=True)

        for n in news[:15]:
            sent = n.get("sentiment", 0)
            color = "#26a69a" if sent > 0.1 else ("#ef5350" if sent < -0.1 else "#888")
            icon = "📈" if sent > 0.1 else ("📉" if sent < -0.1 else "➡️")
            st.markdown(f"""
            <div style="border-left:3px solid {color};padding:8px 12px;margin:6px 0;background:#1a1a2e;border-radius:4px">
                {icon} {n.get('headline', '')}
                <span style="color:#888;font-size:11px;float:right">{n.get('source', '')} | Sentiment: {sent:+.2f}</span>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Key macro factors for gold
    st.subheader("🌐 Key Macro Drivers for Gold")
    drivers = {
        "💵 US Dollar (DXY)": "Inverse correlation. Rising DXY = bearish gold. Falling DXY = bullish gold.",
        "📈 US Treasury Yields": "Higher real yields = bearish gold (opportunity cost). Lower yields = bullish.",
        "🏦 Fed Policy": "Hawkish (rate hikes) = bearish gold. Dovish (cuts/pause) = bullish.",
        "⚠️ Geopolitical Risk": "Wars, crises, uncertainty = bullish gold (safe haven).",
        "📊 Inflation (CPI)": "High inflation surprises = bullish gold (inflation hedge).",
        "🛢️ Commodities Cycle": "Gold often leads commodities. Watch oil and broad commodity trends.",
        "🏦 Central Bank Buying": "Record central bank purchases (EM) are structurally bullish.",
        "💎 Physical Demand": "China/India jewelry & investment demand adds seasonal patterns.",
    }
    for driver, explanation in drivers.items():
        with st.expander(driver):
            st.write(explanation)


# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center;color:#555;font-size:12px;padding:8px">
    🥇 XAUUSD AI Trading Partner | ICT Methodology | For educational purposes only.<br>
    Past performance does not guarantee future results. Trade responsibly. Never risk money you cannot afford to lose.
</div>
""", unsafe_allow_html=True)

# Evaluate pending signals on every page load
if price > 0:
    try:
        learning.evaluate_pending_signals(price)
    except:
        pass