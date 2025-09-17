import sqlite3

DB_FILE = "bot_data.db"

# -----------------------
# Database Initialization
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
    print("✅ Database initialized.")

# -----------------------
# User Preferences
# -----------------------
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
    cursor.execute("SELECT region, zodiac, reminder_hour, reminder_days, subscribed FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        region, zodiac, hour, days, subscribed = row
        return {"region": region, "zodiac": zodiac, "hour": hour, "days": days.split(","), "subscribed": bool(subscribed)}
    return None

def set_subscription(user_id, status: bool):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET subscribed = ? WHERE user_id = ?", (int(status), user_id))
    conn.commit()
    conn.close()

# -----------------------
# Quotes & Journal Prompts
# -----------------------
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
    return quotes

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
    return prompts
