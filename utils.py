import sqlite3
import datetime
import ephem
from zoneinfo import ZoneInfo
import random

# -----------------------
# Regions & Sabbats
# -----------------------
REGIONS = {
    "NA": {"name": "North America", "role_id": 1416438886397251768, "tz": "America/New_York", "emoji": "🇺🇸", "color": 0x2ecc71},
    "SA": {"name": "South America", "role_id": 1416438925140164809, "tz": "America/Sao_Paulo", "emoji": "🌴", "color": 0xe67e22},
    "EU": {"name": "Europe", "role_id": 1416439011517534288, "tz": "Europe/London", "emoji": "🍀", "color": 0x3498db},
    "AF": {"name": "Africa", "role_id": 1416439116043649224, "tz": "Africa/Johannesburg", "emoji": "🌍", "color": 0xf1c40f},
    "OC": {"name": "Oceania & Asia", "role_id": 1416439141339758773, "tz": "Australia/Sydney", "emoji": "🌺", "color": 0x9b59b6},
}

SABBATS = {
    "Imbolc": (2, 1),
    "Ostara": (3, 20),
    "Beltane": (5, 1),
    "Litha": (6, 21),
    "Lughnasadh": (8, 1),
    "Mabon": (9, 22),
    "Samhain": (10, 31),
    "Yule": (12, 21),
}

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

QUOTES = [
    "🌿 May the Wheel of the Year turn in your favor.",
    "🌕 Reflect, release, and renew under the Moon's light.",
    "✨ Blessed be, traveler of the mystical paths.",
    "🔥 May your rituals be fruitful and your intentions clear.",
    "🌱 Growth is guided by the cycles of the Earth and Moon"
]

JOURNAL_PROMPTS = [
    "What are three things you are grateful for today?",
    "Reflect on a recent challenge and what you learned.",
    "What intention do you want to set for today?"
]

DB_FILE = "bot_data.db"

# -----------------------
# SQLite Helpers
# -----------------------
def init_db():
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

# User preferences
def save_user_preferences(user_id, region=None, zodiac=None, hour=None, days=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, region, zodiac, reminder_hour, reminder_days, subscribed)
    VALUES (?, ?, ?, ?, ?, COALESCE((SELECT subscribed FROM users WHERE user_id=?),1))
    """, (user_id, region, zodiac, hour or 9, ",".join(days) if days else 'Mon,Tue,Wed,Thu,Fri,Sat,Sun', user_id))
    conn.commit()
    conn.close()

def get_user_preferences(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT region, zodiac, reminder_hour, reminder_days, subscribed FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        region, zodiac, hour, days, subscribed = row
        return {"region": region, "zodiac": zodiac, "hour": hour, "days": days.split(","), "subscribed": bool(subscribed)}
    return None

def set_subscription(user_id, status: bool):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET subscribed=? WHERE user_id=?", (int(status), user_id))
    conn.commit()
    conn.close()

def add_quote(quote):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quotes (quote) VALUES (?)", (quote,))
    conn.commit()
    conn.close()

def get_all_quotes():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT quote FROM quotes")
    quotes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return QUOTES + quotes

def add_journal_prompt(prompt):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO journal_prompts (prompt) VALUES (?)", (prompt,))
    conn.commit()
    conn.close()

def get_all_journal_prompts():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompt FROM journal_prompts")
    prompts = [row[0] for row in cursor.fetchall()]
    conn.close()
    return JOURNAL_PROMPTS + prompts

# Date helpers
def format_date(d: datetime.date) -> str:
    return d.strftime("%-d %B %Y")

def next_full_moon_for_tz(tz_name: str):
    now = datetime.datetime.now(ZoneInfo(tz_name))
    fm_utc = ephem.next_full_moon(now).datetime()
    return fm_utc.astimezone(ZoneInfo(tz_name)).date()

def get_sabbat_dates(year: int):
    return {name: datetime.date(year, m, d) for name, (m, d) in SABBATS.items()}

def moon_phase_emoji(date: datetime.date) -> str:
    moon = ephem.Moon(date)
    phase = moon.phase
    if phase < 10:
        return "🌑"
    elif phase < 50:
        return "🌒"
    elif phase < 60:
        return "🌕"
    elif phase < 90:
        return "🌘"
    else:
        return "🌑"
