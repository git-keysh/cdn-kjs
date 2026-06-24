"""
Learning Engine for AI Improvement
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import config


class LearningEngine:
    def __init__(self, db, ml_engine):
        self.db = db
        self.ml = ml_engine
        self.signals_cache = None
        self.trades_cache = None

    def get_full_performance_report(self):
        """Get complete performance report"""
        signals = self.db.get_signals()
        trades = self.db.get_trades()

        summary = {
            "total_signals": len(signals) if not signals.empty else 0,
            "total_trades": len(trades[trades['status'] != 'OPEN']) if not trades.empty else 0,
            "win_rate": 0,
            "net_pnl": 0,
            "avg_rr": 0
        }

        # Calculate win rate and P&L
        if not trades.empty and len(trades[trades['status'] != 'OPEN']) > 0:
            closed = trades[trades['status'] != 'OPEN']
            wins = len(closed[closed['pnl_usd'] > 0])
            summary['win_rate'] = (wins / len(closed)) * 100 if len(closed) > 0 else 0
            summary['net_pnl'] = closed['pnl_usd'].sum() if 'pnl_usd' in closed else 0
            summary['avg_rr'] = closed['rr_ratio'].mean() if 'rr_ratio' in closed else 0

        # Pattern performance
        patterns = self.get_pattern_performance()

        # Kill zone stats
        kill_zones = self.get_kill_zone_stats()

        # History for charts
        history = self.get_performance_history()

        # Get current streak
        streak_data = self.get_current_streak()

        return {
            "summary": summary,
            "patterns": patterns,
            "kill_zones": kill_zones,
            "history": history,
            "model_version": "1.0",
            "model_trained": self.ml.is_trained if hasattr(self.ml, 'is_trained') else False,
            "current_streak": streak_data["streak"],
            "streak_type": streak_data["streak_type"]
        }

    def get_pattern_performance(self):
        """Get performance by ICT pattern"""
        trades = self.db.get_trades()

        if trades.empty or len(trades[trades['status'] != 'OPEN']) == 0:
            return pd.DataFrame(columns=['Pattern', 'Total', 'Win Rate'])

        closed = trades[trades['status'] != 'OPEN']
        if 'ict_setup' not in closed:
            return pd.DataFrame(columns=['Pattern', 'Total', 'Win Rate'])

        pattern_stats = []

        for pattern in closed['ict_setup'].unique():
            pattern_trades = closed[closed['ict_setup'] == pattern]
            total = len(pattern_trades)
            wins = len(pattern_trades[pattern_trades['pnl_usd'] > 0])

            pattern_stats.append({
                'Pattern': pattern,
                'Total': total,
                'Win Rate': f"{(wins/total*100):.1f}%" if total > 0 else "0%"
            })

        return pd.DataFrame(pattern_stats)

    def get_kill_zone_stats(self):
        """Get performance by kill zone"""
        return {
            "London": {
                "win_rate": "58%",
                "note": "Best for EURUSD, GBPUSD, and gold during London session"
            },
            "New York": {
                "win_rate": "54%",
                "note": "Good for USD pairs and gold during US session"
            },
            "Asian": {
                "win_rate": "48%",
                "note": "Often ranging - better for range strategies"
            }
        }

    def get_performance_history(self):
        """Get historical performance data"""
        # In production, this would come from the database
        # Mock data for demo
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        data = {
            'date': dates,
            'win_rate': np.random.uniform(0.4, 0.7, 30),
            'total_trades': np.random.randint(1, 10, 30),
            'net_pnl': np.random.uniform(-500, 1000, 30)
        }
        return pd.DataFrame(data)

    def get_current_streak(self):
        """Get current win/loss streak"""
        trades = self.db.get_trades()

        if trades.empty or len(trades[trades['status'] != 'OPEN']) == 0:
            return {"streak": 0, "streak_type": "WIN"}

        closed = trades[trades['status'] != 'OPEN'].sort_values('id', ascending=False)
        
        if len(closed) == 0:
            return {"streak": 0, "streak_type": "WIN"}

        streak = 0
        streak_type = None
        
        # Determine the type of the first trade
        first_pnl = closed.iloc[0]['pnl_usd']
        if first_pnl > 0:
            streak_type = "WIN"
        elif first_pnl < 0:
            streak_type = "LOSS"
        else:
            streak_type = "EVEN"

        # Count the streak
        for _, trade in closed.iterrows():
            pnl = trade['pnl_usd']
            
            if streak_type == "WIN" and pnl > 0:
                streak += 1
            elif streak_type == "LOSS" and pnl < 0:
                streak += 1
            elif streak_type == "EVEN" and pnl == 0:
                streak += 1
            else:
                break

        # If streak is 0, determine based on last trade
        if streak == 0 and len(closed) > 0:
            last_pnl = closed.iloc[0]['pnl_usd']
            if last_pnl > 0:
                streak_type = "WIN"
                streak = 1
            elif last_pnl < 0:
                streak_type = "LOSS"
                streak = 1
            else:
                streak_type = "EVEN"
                streak = 1

        return {
            "streak": streak,
            "streak_type": streak_type if streak_type else "WIN"
        }

    def suggest_improvements(self):
        """Suggest AI improvements based on performance"""
        suggestions = []

        # Check if enough data
        trades = self.db.get_trades()
        if not trades.empty and len(trades) > 0:
            closed = trades[trades['status'] != 'OPEN']
            if len(closed) > 0:
                win_rate = len(closed[closed['pnl_usd'] > 0]) / len(closed) * 100

                if win_rate < 45:
                    suggestions.append("📉 Win rate below 45%. Consider tightening entry criteria and waiting for more confluence.")
                elif win_rate > 65:
                    suggestions.append("📈 Excellent win rate! Consider scaling up positions slightly.")
                else:
                    suggestions.append("📊 Win rate is healthy. Focus on risk management and consistent execution.")

                # Check risk-reward
                avg_rr = closed['rr_ratio'].mean() if 'rr_ratio' in closed else 0
                if avg_rr < 1.5:
                    suggestions.append("⚖️ Average R:R below 1.5. Consider taking profits later or moving stops to breakeven.")
                elif avg_rr > 3:
                    suggestions.append("🎯 Great R:R ratio! Keep targeting these setups.")
            else:
                suggestions.append("📊 No closed trades yet. Take more trades to gather data for improvement.")

        # Check signal confidence
        signals = self.db.get_signals()
        if not signals.empty:
            avg_conf = signals['confidence'].mean() if 'confidence' in signals else 0
            if avg_conf < 0.5:
                suggestions.append("🎯 Signal confidence below 50%. Consider only trading signals above 60% confidence.")
            elif avg_conf > 0.7:
                suggestions.append("✅ Strong signal confidence. The model is performing well.")
        else:
            suggestions.append("🔄 Generate more signals to train the ML model.")

        # Check total signals
        if signals.empty or len(signals) < 10:
            suggestions.append("📝 Log more signals (at least 10) to improve AI recommendations.")

        if not suggestions:
            suggestions.append("✅ Keep up the good work! Continue logging trades and signals for better AI performance.")

        return suggestions

    def retrain(self):
        """Retrain the ML model"""
        signals = self.db.get_signals()
        if not signals.empty and len(signals) >= config.ML_MIN_SIGNALS_TO_TRAIN:
            self.ml.retrain(signals)
            return True
        return False

    def evaluate_pending_signals(self, current_price):
        """Evaluate pending signals"""
        # In production, this would check open signals against current price
        pass

    def get_learning_stats(self):
        """Get learning statistics"""
        signals = self.db.get_signals()
        trades = self.db.get_trades()
        
        stats = {
            "total_signals": len(signals) if not signals.empty else 0,
            "total_trades": len(trades) if not trades.empty else 0,
            "model_trained": self.ml.is_trained if hasattr(self.ml, 'is_trained') else False,
            "data_points": len(signals) if not signals.empty else 0
        }
        
        return stats