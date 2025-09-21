# GBPBot - db.py
# Version: 1.0.3b4
# Last Updated: 2025-09-21
# Notes:
# - Added 'daily' column support with auto-ALTER TABLE if missing.
# - save_user_preferences/get_user_preferences updated to handle 'daily'.
# - Fully compatible with reminders.py daily_loop and subscription handling.
# - Minor fixes for async DB operations and robust exception logging.

# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-20 12:30 BST] v1.0.3b1 - Added 'daily' column support for users table; updated save_user_preferences and get_user_preferences.
# [2025-09-20 12:35 BST] v1.0.3b2 - Automatic ALTER TABLE to add 'daily' if missing; backward-compatible with set_user_preferences.
# [2025-09-20 12:40 BST] v1.0.3b3 - Minor fixes for async DB operations and exception logging.
# [2025-09-21 11:40 BST] v1.0.3b4 - Corrected get_all_subscribed_users and daily unpacking; synced with reminders.py daily loop.


import sqlite3
from typing import List, Optional, Tuple
import traceback
import asyncio

from utils.logger import robust_log
from version_tracker import GBPBot_version, file_versions, get_file_version

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
async def init_db(bot=None) -> None:
    """
    Async DB initialization.
    Creates tables and pre-populates quotes and prompts.
    Automatically adds 'daily' column if missing.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Users table
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

        # Ensure daily column exists
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN daily INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Quotes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT
            )
        """)

        # Journal Prompts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT
            )
        """)

        conn.commit()

        # Pre-populate quotes
        cursor.execute("SELECT COUNT(*) FROM quotes")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO quotes (quote) VALUES (?)",
                [(q,) for q in DEFAULT_QUOTES]
            )
            conn.commit()

        # Pre-populate prompts
        cursor.execute("SELECT COUNT(*) FROM journal_prompts")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO journal_prompts (prompt) VALUES (?)",
                [(p,) for p in DEFAULT_PROMPTS]
            )
            conn.commit()

        if bot:
            await robust_log(bot, "✅ Database initialized successfully.")

    except Exception as e:
        if bot:
            await robust_log(bot, f"❌ Failed to initialize DB: {e}", exc=traceback.format_exc())
        else:
            print(f"DB init error: {e}\n{traceback.format_exc()}")

    finally:
        conn.close()

# -----------------------
# User Preferences
# -----------------------
async def save_user_preferences(
    user_id: int,
    region: Optional[str] = None,
    zodiac: Optional[str] = None,
    hour: Optional[int] = None,
    days: Optional[List[str]] = None,
    subscribed: Optional[bool] = None,
    daily: Optional[bool] = None,  # new parameter
    bot=None
) -> None:
    """
    Upsert preserving existing values when parameters are None.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT region, zodiac, reminder_hour, reminder_days, subscribed, daily FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            cur_region, cur_zodiac, cur_hour, cur_days, cur_sub, cur_daily = row
        else:
            cur_region, cur_zodiac, cur_hour, cur_days, cur_sub, cur_daily = (None, None, 9, DEFAULT_DAYS, 1, 1)

        new_region = region if region is not None else cur_region
        new_zodiac = zodiac if zodiac is not None else cur_zodiac
        new_hour = hour if hour is not None else cur_hour
        new_days = ",".join(days) if days is not None else cur_days
        new_subscribed = int(subscribed) if subscribed is not None else cur_sub
        new_daily = int(daily) if daily is not None else cur_daily

        cursor.execute("""
            INSERT OR REPLACE INTO users
            (user_id, region, zodiac, reminder_hour, reminder_days, subscribed, daily)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, new_region, new_zodiac, new_hour, new_days, new_subscribed, new_daily))

        conn.commit()

    except Exception as e:
        if bot:
            await robust_log(bot, f"❌ Failed to save user preferences for {user_id}: {e}", exc=traceback.format_exc())
        else:
            print(f"Save user prefs error: {e}\n{traceback.format_exc()}")

    finally:
        conn.close()


async def get_user_preferences(user_id: int) -> Optional[dict]:
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT region, zodiac, reminder_hour, reminder_days, subscribed, daily FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            region, zodiac, hour, days, subscribed, daily = row
            return {
                "region": region,
                "zodiac": zodiac,
                "hour": hour,
                "days": days.split(",") if days else DEFAULT_DAYS.split(","),
                "subscribed": bool(subscribed),
                "daily": bool(daily)
            }

    except Exception as e:
        print(f"Get user prefs error: {e}\n{traceback.format_exc()}")

    finally:
        conn.close()
    return None


async def set_subscription(user_id: int, status: bool, bot=None) -> None:
    await save_user_preferences(user_id, subscribed=status, bot=bot)


# -----------------------
# Clear User Preferences
# -----------------------
async def clear_user_preferences(user_id: int, bot=None) -> None:
    """ Deletes a user's preferences from the DB. """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()

        if bot:
            await robust_log(bot, f"✅ Cleared preferences for user {user_id}.")

    except Exception as e:
        if bot:
            await robust_log(bot, f"❌ Failed to clear preferences for {user_id}: {e}", exc=traceback.format_exc())
        else:
            print(f"Clear user prefs error: {e}\n{traceback.format_exc()}")

    finally:
        conn.close()


# -----------------------
# Quotes
# -----------------------
async def add_quote(quote: str, bot=None) -> None:
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quotes (quote) VALUES (?)", (quote,))
        conn.commit()

    except Exception as e:
        if bot:
            await robust_log(bot, f"❌ Failed to add quote: {e}", exc=traceback.format_exc())
        else:
            print(f"Add quote error: {e}\n{traceback.format_exc()}")

    finally:
        conn.close()


async def get_all_quotes() -> List[str]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT quote FROM quotes")
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return DEFAULT_QUOTES + rows


# -----------------------
# Journal Prompts
# -----------------------
async def add_journal_prompt(prompt: str, bot=None) -> None:
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO journal_prompts (prompt) VALUES (?)", (prompt,))
        conn.commit()

    except Exception as e:
        if bot:
            await robust_log(bot, f"❌ Failed to add journal prompt: {e}", exc=traceback.format_exc())
        else:
            print(f"Add journal prompt error: {e}\n{traceback.format_exc()}")

    finally:
        conn.close()


async def get_all_journal_prompts() -> List[str]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompt FROM journal_prompts")
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return DEFAULT_PROMPTS + rows


# -----------------------
# Subscribed Users
# -----------------------
async def get_all_subscribed_users() -> List[Tuple]:
    """
    Return list of rows for subscribed users:
    (user_id, region, zodiac, reminder_hour, reminder_days, daily)
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, region, zodiac, reminder_hour, reminder_days, daily FROM users WHERE subscribed = 1"
        )
        rows = cursor.fetchall()
        return rows

    except Exception as e:
        print(f"Get subscribed users error: {e}\n{traceback.format_exc()}")
        return []

    finally:
        conn.close()


# -----------------------
# Aliases for backward compatibility
# -----------------------
set_user_preferences = save_user_preferences
