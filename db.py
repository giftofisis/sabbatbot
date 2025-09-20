# GBPBot - db.py
# Version: 1.0.3b3
# Last Updated: 2025-09-20
# Notes: Added 'daily' support for user preferences, auto-ALTER TABLE, backward-compatible aliases, and robust async logging.

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
    Async DB initialization. Creates tables and pre-populates quotes and prompts.
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
            subscribed INTEGER DEFAULT 1,
            daily TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'
        )
        """)

        # Quotes table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote TEXT
        )
        """)

        # Journal Prompts table
