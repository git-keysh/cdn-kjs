"""
Risk Management Module
"""

import config
from datetime import datetime


class RiskManager:
    def __init__(self):
        self.balance = config.DEFAULT_ACCOUNT_BALANCE
        self.risk_pct = config.DEFAULT_RISK_PERCENT
        self.daily_pnl = 0
        self.trades_today = 0
        self.daily_loss_limit_pct = config.MAX_DAILY_LOSS_PERCENT
        self.trades = []

    def update_balance(self, new_balance):
        """Update account balance"""
        self.balance = float(new_balance)

    def calculate_lot_size(self, entry_price, stop_loss):
        """Calculate lot size based on risk percentage"""
        if not entry_price or not stop_loss or self.balance <= 0:
            return {"lot_size": 0, "risk_usd": 0}

        # Risk amount in USD
        risk_usd = self.balance * (self.risk_pct / 100)

        # Risk in points
        risk_points = abs(entry_price - stop_loss)

        if risk_points == 0:
            return {"lot_size": 0, "risk_usd": 0}

        # Lot size for Gold (XAUUSD): 1 point = $1 per lot
        # So: lot_size = risk_usd / risk_points
        lot_size = risk_usd / risk_points

        # Round to 0.01 lots
        lot_size = round(lot_size * 100) / 100

        # Maximum lot size (safety)
        max_lot = 10.0
        lot_size = min(lot_size, max_lot)

        return {
            "lot_size": lot_size,
            "risk_usd": lot_size * risk_points
        }

    def validate_setup(self, entry, stop_loss, take_profit, direction):
        """Validate trading setup"""
        warnings = []
        rr = 0
        risk_usd = 0
        reward_usd = 0
        lot_size = 0

        if not entry or not stop_loss or not take_profit:
            warnings.append("Missing price levels")

        if stop_loss and take_profit and entry:
            if direction == "BUY":
                risk_points = entry - stop_loss
                reward_points = take_profit - entry
            else:
                risk_points = stop_loss - entry
                reward_points = entry - take_profit

            if risk_points <= 0:
                warnings.append("Invalid stop loss level")
            else:
                rr = reward_points / risk_points if risk_points > 0 else 0

                if rr < config.MIN_RR_RATIO:
                    warnings.append(f"R:R ratio {rr:.2f} below minimum {config.MIN_RR_RATIO}")

            # Calculate lot size
            lot_calc = self.calculate_lot_size(entry, stop_loss)
            lot_size = lot_calc["lot_size"]
            risk_usd = lot_calc["risk_usd"]
            reward_usd = risk_usd * rr if rr > 0 else 0

        # Check daily loss limit
        if self.daily_pnl < 0 and abs(self.daily_pnl) >= self.balance * (self.daily_loss_limit_pct / 100):
            warnings.append(f"Daily loss limit reached ({self.daily_loss_limit_pct}%)")

        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "rr": rr,
            "lot_size": lot_size,
            "risk_usd": risk_usd,
            "reward_usd": reward_usd,
            "can_trade": len(warnings) == 0
        }

    def record_pnl(self, pnl):
        """Record profit/loss for today"""
        self.daily_pnl += pnl
        self.trades_today += 1

        return {
            "pnl": pnl,
            "daily_pnl": self.daily_pnl,
            "trades_today": self.trades_today
        }

    def get_account_summary(self):
        """Get account summary"""
        daily_loss_limit = self.balance * (self.daily_loss_limit_pct / 100)
        can_trade = self.daily_pnl > -daily_loss_limit

        return {
            "balance": self.balance,
            "daily_pnl": self.daily_pnl,
            "daily_used_pct": abs(self.daily_pnl) / daily_loss_limit * 100 if daily_loss_limit > 0 else 0,
            "trades_today": self.trades_today,
            "can_trade": can_trade,
            "daily_limit": daily_loss_limit
        }

    def reset_daily_stats(self):
        """Reset daily stats (call at midnight)"""
        self.daily_pnl = 0
        self.trades_today = 0