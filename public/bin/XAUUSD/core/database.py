"""
Database module for XAUUSD AI Trading Partner
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json
import config


class Database:
    def __init__(self, db_path=config.DB_PATH):
        self.db_path = db_path
        self.init_tables()

    def init_tables(self):
        """Initialize database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Signals table
        c.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                timeframe TEXT,
                signal_type TEXT,
                confidence REAL,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                rr_ratio REAL,
                ict_patterns TEXT,
                indicators TEXT,
                outcome TEXT,
                exit_price REAL,
                pnl REAL,
                created_at TEXT
            )
        ''')

        # Trades table
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                direction TEXT,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                lot_size REAL,
                risk_usd REAL,
                reward_usd REAL,
                rr_ratio REAL,
                ict_setup TEXT,
                notes TEXT,
                status TEXT DEFAULT 'OPEN',
                exit_price REAL,
                pnl_usd REAL,
                closed_at TEXT
            )
        ''')

        # Chat history table
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                timestamp TEXT
            )
        ''')

        # News table
        c.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                headline TEXT,
                source TEXT,
                sentiment REAL,
                timestamp TEXT
            )
        ''')

        # Performance history
        c.execute('''
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                win_rate REAL,
                total_trades INTEGER,
                net_pnl REAL
            )
        ''')

        conn.commit()
        conn.close()

    def save_signal(self, signal_data):
        """Save a trading signal to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO signals (
                timestamp, timeframe, signal_type, confidence,
                entry_price, stop_loss, take_profit, rr_ratio,
                ict_patterns, indicators, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal_data.get('timestamp', datetime.now().isoformat()),
            signal_data.get('timeframe', ''),
            signal_data.get('signal_type', ''),
            signal_data.get('confidence', 0),
            signal_data.get('entry_price', 0),
            signal_data.get('stop_loss', 0),
            signal_data.get('take_profit', 0),
            signal_data.get('rr_ratio', 0),
            json.dumps(signal_data.get('ict_patterns', [])),
            json.dumps(signal_data.get('indicators', {})),
            datetime.now().isoformat()
        ))

        signal_id = c.lastrowid
        conn.commit()
        conn.close()
        return signal_id

    def get_signals(self, limit=100):
        """Get recent signals"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            f"SELECT * FROM signals ORDER BY id DESC LIMIT {limit}",
            conn
        )
        conn.close()
        return df

    def save_trade(self, trade_data):
        """Save a trade to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO trades (
                timestamp, direction, entry_price, stop_loss,
                take_profit, lot_size, risk_usd, reward_usd,
                rr_ratio, ict_setup, notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('timestamp', datetime.now().isoformat()),
            trade_data.get('direction', ''),
            trade_data.get('entry_price', 0),
            trade_data.get('stop_loss', 0),
            trade_data.get('take_profit', 0),
            trade_data.get('lot_size', 0),
            trade_data.get('risk_usd', 0),
            trade_data.get('reward_usd', 0),
            trade_data.get('rr_ratio', 0),
            trade_data.get('ict_setup', ''),
            trade_data.get('notes', ''),
            'OPEN'
        ))

        trade_id = c.lastrowid
        conn.commit()
        conn.close()
        return trade_id

    def close_trade(self, trade_id, exit_price, pnl_usd):
        """Close an open trade"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            UPDATE trades
            SET status = 'CLOSED',
                exit_price = ?,
                pnl_usd = ?,
                closed_at = ?
            WHERE id = ?
        ''', (exit_price, pnl_usd, datetime.now().isoformat(), trade_id))

        # Determine if trade was win or loss
        status = 'WIN' if pnl_usd > 0 else 'LOSS'

        conn.commit()
        conn.close()

    def get_trades(self):
        """Get all trades"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC", conn)
        conn.close()
        return df

    def get_open_trades(self):
        """Get open trades"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            "SELECT * FROM trades WHERE status = 'OPEN' ORDER BY id DESC",
            conn
        )
        conn.close()
        return df

    def save_message(self, role, content):
        """Save chat message to history"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO chat_history (role, content, timestamp)
            VALUES (?, ?, ?)
        ''', (role, content, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_chat_history(self, limit=50):
        """Get chat history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT role, content, timestamp
            FROM chat_history
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        # Return in chronological order
        return [{"role": r[0], "content": r[1], "timestamp": r[2]}
                for r in reversed(rows)]

    def clear_chat(self):
        """Clear chat history"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM chat_history")
        conn.commit()
        conn.close()

    def save_news(self, news_list):
        """Save news articles"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        for news in news_list:
            c.execute('''
                INSERT INTO news (headline, source, sentiment, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                news.get('headline', ''),
                news.get('source', ''),
                news.get('sentiment', 0),
                news.get('timestamp', datetime.now().isoformat())
            ))

        conn.commit()
        conn.close()