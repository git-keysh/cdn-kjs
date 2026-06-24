"""
AI Engine for XAUUSD Trading Partner
"""

import anthropic
import pandas as pd
import numpy as np
import config
import json
from datetime import datetime


class MLSignalEngine:
    """Machine Learning signal engine"""
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.feature_columns = ['rsi', 'macd', 'macd_signal', 'macd_hist',
                                'ema_21', 'ema_50', 'ema_200', 'atr',
                                'bb_upper', 'bb_lower', 'volume_sma']

    def predict(self, df, ict_data):
        """
        Generate trading signal using ML + ICT confluence
        """
        if df.empty:
            return {"signal": "HOLD", "confidence": 0, "probabilities": {}}

        # Use ICT confluence as primary signal
        buy_conf = ict_data.get('confluence_buy', 0)
        sell_conf = ict_data.get('confluence_sell', 0)

        # Calculate base confidence
        total_conf = buy_conf + sell_conf
        if total_conf == 0:
            return {"signal": "HOLD", "confidence": 0, "probabilities": {"HOLD": 1.0}}

        # Determine signal
        if buy_conf > sell_conf and buy_conf >= 2:
            signal = "BUY"
            confidence = min(0.95, buy_conf / 10)
            probabilities = {
                "BUY": confidence,
                "SELL": 0.1,
                "HOLD": 1 - confidence - 0.1
            }
        elif sell_conf > buy_conf and sell_conf >= 2:
            signal = "SELL"
            confidence = min(0.95, sell_conf / 10)
            probabilities = {
                "BUY": 0.1,
                "SELL": confidence,
                "HOLD": 1 - confidence - 0.1
            }
        else:
            signal = "HOLD"
            confidence = 0.3
            probabilities = {
                "BUY": 0.2,
                "SELL": 0.2,
                "HOLD": 0.6
            }

        return {
            "signal": signal,
            "confidence": confidence,
            "probabilities": probabilities,
            "features": self.extract_features(df)
        }

    def extract_features(self, df):
        """Extract features for ML model"""
        if df.empty:
            return {}

        latest = df.iloc[-1]
        features = {}
        for col in self.feature_columns:
            if col in df:
                features[col] = float(latest[col])

        return features

    def retrain(self, signals_df):
        """Retrain ML model with new signals"""
        # Placeholder for actual ML training
        self.is_trained = True
        return True


class ClaudeTradingPartner:
    """AI Trading Partner using Claude"""
    def __init__(self, db):
        self.db = db
        self.client = None

        if config.ANTHROPIC_API_KEY:
            try:
                self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            except:
                self.client = None

        self.system_prompt = """You are an expert ICT (Inner Circle Trader) trading mentor specializing in XAUUSD (Gold).

Key principles you follow:
1. ICT methodology: Order Blocks, Fair Value Gaps, Market Structure, Premium/Discount
2. Risk Management: Always recommend 1-2% risk per trade
3. Technical Analysis: Use price action, liquidity levels, kill zones
4. Patience: Wait for confluence and confirmations
5. Education: Teach users to think like institutional traders

Your responses should be:
- Educational and explain the reasoning
- Clear and actionable
- Include specific price levels when relevant
- Focus on risk management
- Be honest about uncertainty

Never guarantee profits or give reckless advice."""

    def chat(self, user_message, market_context=None):
        """Chat with Claude"""
        if not self.client:
            return self._fallback_response(user_message)

        try:
            # Build context
            context = self._build_context(market_context)

            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": f"{context}\n\nUser question: {user_message}"}
                ]
            )

            reply = response.content[0].text
            self.db.save_message("assistant", reply)
            return reply

        except Exception as e:
            print(f"Claude API error: {e}")
            return self._fallback_response(user_message)

    def analyze_setup(self, ict_data):
        """Analyze current market setup"""
        if not self.client or not ict_data:
            return self._fallback_analysis(ict_data)

        try:
            prompt = f"""
            Analyze this XAUUSD trading setup using ICT methodology:

            Current Price: ${ict_data.get('current_price', 0):.2f}
            Bias: {ict_data.get('bias', 'NEUTRAL')}
            Trend: {ict_data.get('structure', {}).get('trend', 'NEUTRAL')}
            Buy Confluence: {ict_data.get('confluence_buy', 0)}
            Sell Confluence: {ict_data.get('confluence_sell', 0)}
            Premium/Discount Zone: {ict_data.get('premium_discount', {}).get('zone', 'NEUTRAL')}

            Order Blocks Detected: {len(ict_data.get('order_blocks', []))}
            FVGs Detected: {len(ict_data.get('fair_value_gaps', []))}
            Kill Zone Active: {ict_data.get('kill_zone', {}).get('active', False)}

            Provide:
            1. Your bias and reasoning
            2. Key levels to watch (entry, SL, TP)
            3. Risk management suggestions
            4. Additional ICT patterns to look for
            """

            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            print(f"Analysis error: {e}")
            return self._fallback_analysis(ict_data)

    def explain_concept(self, concept):
        """Explain an ICT concept"""
        if not self.client:
            return self._fallback_concept_explanation(concept)

        try:
            prompt = f"""
            Explain the ICT concept: "{concept}" in the context of trading XAUUSD.

            Include:
            1. What it is and why it matters
            2. How to identify it on a chart
            3. How to trade it effectively
            4. Common mistakes to avoid
            5. A practical example with price levels

            Keep it clear and actionable.
            """

            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=600,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            print(f"Concept explanation error: {e}")
            return self._fallback_concept_explanation(concept)

    def _build_context(self, market_context):
        """Build market context for chat"""
        if not market_context:
            return "Current market data not available."

        price = market_context.get('price', 'N/A')
        ict = market_context.get('ict', {})

        context = f"""
        Current XAUUSD Price: {price}
        ICT Bias: {ict.get('bias', 'NEUTRAL')}
        Trend: {ict.get('structure', {}).get('trend', 'NEUTRAL')}
        Kill Zone: {'Active' if ict.get('kill_zone', {}).get('active', False) else 'Inactive'}
        """

        return context

    def _fallback_response(self, message):
        """Fallback response when Claude API is unavailable"""
        return f"""I'm currently in offline mode (API key not configured). 

        However, based on your question about "{message[:50]}...", here's some general ICT guidance:

        1. Always check market structure first (trend, BOS, CHoCH)
        2. Look for Order Blocks and Fair Value Gaps for entries
        3. Use Premium/Discount zones for bias
        4. Never risk more than 1-2% per trade
        5. Wait for confluence before entering

        To enable full AI analysis, add your ANTHROPIC_API_KEY to the .env file.
        """

    def _fallback_analysis(self, ict_data):
        """Fallback market analysis"""
        if not ict_data:
            return "Unable to analyze market - no data available."

        price = ict_data.get('current_price', 0)
        bias = ict_data.get('bias', 'NEUTRAL')
        trend = ict_data.get('structure', {}).get('trend', 'NEUTRAL')
        buy_conf = ict_data.get('confluence_buy', 0)
        sell_conf = ict_data.get('confluence_sell', 0)

        analysis = f"""
        ## Market Analysis Summary

        **Current Price:** ${price:.2f}
        **Bias:** {bias}
        **Trend:** {trend}
        **Buy Confluence:** {buy_conf} pts
        **Sell Confluence:** {sell_conf} pts

        ### Key Observations:
        """
        if buy_conf > sell_conf:
            analysis += f"\n- Bullish bias with {buy_conf} pts of confluence"
        elif sell_conf > buy_conf:
            analysis += f"\n- Bearish bias with {sell_conf} pts of confluence"
        else:
            analysis += "\n- Neutral market - wait for clearer signals"

        analysis += f"""
        ### Suggested Levels:
        - Entry: ${price:.2f}
        - Stop Loss: ${ict_data.get('suggested_sl', price - 10):.2f}
        - Take Profit: ${ict_data.get('suggested_tp', price + 20):.2f}
        - R:R Ratio: 1:{ict_data.get('rr_ratio', 0):.2f}

        ### Risk Management:
        - Risk 1-2% of account per trade
        - Use proper position sizing
        - Check kill zones for optimal entries
        """
        return analysis

    def _fallback_concept_explanation(self, concept):
        """Fallback concept explanation"""
        concepts = {
            "Order Blocks": "An Order Block is the last bullish or bearish candle before a strong move. It represents institutional orders and often acts as support/resistance. Look for price returning to these zones for entries.",
            "Fair Value Gaps": "FVG is a gap between high and low of consecutive candles. Price often returns to fill these gaps, making them good entry/exit zones.",
            "Market Structure": "Understanding market structure means identifying trends, breakouts, and reversals. Look for higher highs (bullish) and lower lows (bearish) with BOS and CHoCH confirmations.",
            "Kill Zones": "Kill zones are specific times when institutional trading is most active: London (7-9 UTC), New York (13-15 UTC), and Asian (23-1 UTC).",
            "Premium and Discount": "These are the upper (premium) and lower (discount) thirds of the price range. Buy in discount, sell in premium.",
            "OTE Fibonacci": "Optimal Trade Entry uses Fibonacci retracements (61.8-79%) to find high-probability entries.",
            "Power of 3 AMD": "Accumulation, Manipulation, Distribution. The institutional cycle: accumulate, manipulate price to trap traders, then distribute.",
            "Displacement": "A strong move in one direction that shows institutional interest and often leads to continuation.",
            "Breaker Blocks": "When price breaks an Order Block, it becomes a Breaker Block - often leading to a reversal.",
            "Liquidity BSL SSL": "BSL (Buy-Side Liquidity) and SSL (Sell-Side Liquidity) are areas where stop losses are placed. Price often hunts these before reversing.",
            "BOS and CHoCH": "Break of Structure (BOS) and Change of Character (CHoCH) are key pattern changes that signal trend continuations or reversals.",
            "Smart Money Concepts": "Smart Money Concepts explain how institutions trade and how to follow their footprints in the market."
        }

        return concepts.get(concept, f"'{concept}' is an important ICT concept. Please check the ICT quick reference in the app for more details.")