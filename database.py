import sqlite3
import json
import datetime
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)
DB_PATH = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            mode TEXT DEFAULT 'friendly',
            free_used_week INTEGER DEFAULT 0,
            week_start TEXT,
            subscription_end TEXT,
            paid INTEGER DEFAULT 0,
            vision_model TEXT DEFAULT 'gemini',
            history TEXT DEFAULT '[]'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "mode": row[1],
            "free_used_week": row[2],
            "week_start": row[3],
            "subscription_end": row[4],
            "paid": bool(row[5]),
            "vision_model": row[6],
            "history": json.loads(row[7]) if row[7] else []
        }
    return None

def save_user(user_data: Dict[str, Any]):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users
        (user_id, mode, free_used_week, week_start, subscription_end, paid, vision_model, history)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data["user_id"],
        user_data["mode"],
        user_data["free_used_week"],
        user_data.get("week_start"),
        user_data.get("subscription_end"),
        1 if user_data.get("paid") else 0,
        user_data.get("vision_model", "gemini"),
        json.dumps(user_data.get("history", []), ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

def get_all_users() -> List[int]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_subscribers() -> List[int]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM subscribers")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_subscriber(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def remove_subscriber(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM subscribers WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()