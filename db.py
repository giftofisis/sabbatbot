import sqlite3
from typing import List, Optional, Tuple

DB_FILE = "bot_data.db"
DEFAULT_DAYS = "Mon,Tue,Wed,Thu,Fri,Sat,Sun"

DEFAULT_QUOTES = [
    "🌿 May the Wheel of the Year turn in your favor.",
    "🌕 Reflect, release, and renew under the Moon's light.",
    "✨ Blessed be, traveler of the mystical paths.",
    "🔥 May your rituals be fruitful and your intentions clear.",
    "🌱 Growth is guided by the cycles of the Earth and Moon"
]

DEFAULT_PROMPTS = [
    "What are three things you are grateful for today?",
    "Reflect on a recent challenge and what you learned.",
    "What intention do you want to set for today?"
]

# -----------------------
# Initialization
# -----------------------
def init_db() -> None:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        region TEXT,
        zodiac TEXT,
        reminder_hour INTEGER DEFAULT 9,
        reminder_days TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri,Sat,Sun',
        subscribed INTEGER DEFAULT 1
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS journal_prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt TEXT
    )
    """)
    conn.commit()
    conn.close()

# -----------------------
# User Preferences
# -----------------------
def save_user_preferences(
    user_id: int,
    region: Optional[str] = None,
    zodiac: Optional[str] = None,
    hour: Optional[int] = None,
    days: Optional[List[str]] = None,
    subscribed: Optional[bool] = None   # <-- added support
) -> None:
    """
    Upsert preserving existing values when parameters are None.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT region, zodiac, reminder_hour, reminder_days, subscribed FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        cur_region, cur_zodiac, cur_hour, cur_days, cur_sub = row
    else:
        cur_region, cur_zodiac, cur_hour, cur_days, cur_sub = (None, None, 9, DEFAULT_DAYS, 1)

    new_region = region if region is not None else cur_region
    new_zodiac = zodiac if zodiac is not None else cur_zodiac
    new_hour = hour if hour is not None else cur_hour
    new_days = ",".join(days) if days is not None else cur_days
    new_subscribed = int(subscribed) if subscribed is not None else cur_sub

    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, region, zodiac, reminder_hour, reminder_days, subscribed)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, new_region, new_zodiac, new_hour, new_days, new_subscribed))
    conn.commit()
    conn.close()

def get_user_preferences(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT region, zodiac, reminder_hour, reminder_days, subscribed FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        region, zodiac, hour, days, subscribed = row
        return {
            "region": region,
            "zodiac": zodiac,
            "hour": hour,
            "days": days.split(",") if days else DEFAULT_DAYS.split(","),
            "subscribed": bool(subscribed)
        }
    return None

def set_subscription(user_id: int, status: bool) -> None:
    save_user_preferences(user_id, subscribed=status)

# -----------------------
# Quotes
# -----------------------
def add_quote(quote: str) -> None:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quotes (quote) VALUES (?)", (quote,))
    conn.commit()
    conn.close()

def get_all_quotes() -> List[str]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT quote FROM quotes")
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return DEFAULT_QUOTES + rows

# -----------------------
# Journal Prompts
# -----------------------
def add_journal_prompt(prompt: str) -> None:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO journal_prompts (prompt) VALUES (?)", (prompt,))
    conn.commit()
    conn.close()

def get_all_journal_prompts() -> List[str]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompt FROM journal_prompts")
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return DEFAULT_PROMPTS + rows

# -----------------------
# Subscribed Users
# -----------------------
def get_all_subscribed_users() -> List[Tuple]:
    """
    Return list of rows for subscribed users:
    (user_id, region, zodiac, reminder_hour, reminder_days, subscribed)
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, region, zodiac, reminder_hour, reminder_days, subscribed FROM users WHERE subscribed = 1")
    rows = cursor.fetchall()
    conn.close()
    return rows

# **Fix:** Add alias for backward compatibility
set_user_preferences = save_user_preferences