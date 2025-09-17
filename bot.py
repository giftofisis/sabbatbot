import discord
from discord.ext import tasks, commands
import datetime
import ephem
import os
# --- Environment Variables ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ROLE_ID = os.getenv("ROLE_ID", "0")  # optional role to ping

if not TOKEN:
    raise ValueError("❌ DISCORD_BOT_TOKEN environment variable is missing!")
if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID environment variable is missing!")

CHANNEL_ID = int(CHANNEL_ID)
ROLE_ID = int(ROLE_ID) if ROLE_ID else 0

# --- Bot Setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Fixed Sabbats ---
SABBATS = {
    "Imbolc": (2, 1),
    "Ostara": (3, 20),
    "Beltane": (5, 1),
    "Litha": (6, 21),
    "Lughnasadh": (8, 1),
    "Mabon": (9, 22),
    "Samhain": (10, 31),
    "Yule": (12, 21)
}

def next_full_moon():
    today = datetime.date.today()
    return ephem.next_full_moon(today).datetime().date()

def format_date(d):
    """Full date format for international audiences."""
    return d.strftime("%-d %B %Y")  # e.g., 1 February 2025

# --- Daily Reminder Loop ---
@tasks.loop(hours=24)
async def daily_check():
    channel = bot.get_channel(CHANNEL_ID)
    today = datetime.date.today()

    # Sabbats
    for name, (month, day) in SABBATS.items():
        if today.month == month and today.day == day:
            mention = f"<@&{ROLE_ID}>" if ROLE_ID else ""
            await channel.send(f"✨ Blessed {name}! {mention}\nToday is **{format_date(today)}** — celebrate the turning of the Wheel of the Year. 🌿🔥")

    # Full Moon
    fm = next_full_moon()
    if today == fm:
        await channel.send(f"🌕 Tonight is the **Full Moon** ({format_date(fm)})!\nPerfect time for ritual, release, and reflection.")

# --- On Ready Event with Test Message ---
@bot.event
async def on_ready():
    print(f"{bot.user} is online.")  # Logs in Railway

    # --- TEST MESSAGE ---
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Test: I am online and can send messages here!")
    else:
        print("❌ Channel not found. Check CHANNEL_ID.")

    # Start daily reminder loop
    daily_check.start()

# --- Run Bot ---
bot.run(TOKEN)
