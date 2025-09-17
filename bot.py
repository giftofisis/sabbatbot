import discord
from discord.ext import commands
import os
import sqlite3

# -----------------------
# Environment Variables
# -----------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# -----------------------
# Intents & Bot Setup
# -----------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------
# SQLite Initialization
# -----------------------
def init_db():
    conn = sqlite3.connect("bot_data.db")
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
# Load Cogs
# -----------------------
async def load_cogs():
    for cog in ["cogs.onboarding", "cogs.reminders", "cogs.commands"]:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

# -----------------------
# On Ready Event
# -----------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print("✅ Commands synced.")

# -----------------------
# Run Bot
# -----------------------
if __name__ == "__main__":
    init_db()
    bot.loop.run_until_complete(load_cogs())
    bot.run(TOKEN)
