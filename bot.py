import discord
from discord.ext import tasks, commands
import datetime
import ephem
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Ensure channel is set
CHANNEL_ID = os.getenv("CHANNEL_ID")
if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID environment variable is missing!")
CHANNEL_ID = int(CHANNEL_ID)

# Role ID optional
ROLE_ID = os.getenv("ROLE_ID")
ROLE_ID = int(ROLE_ID) if ROLE_ID else 0

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Fixed Sabbats with full names
SABBATS = {
    "Imbolc": (2, 1),
    "Beltane": (5, 1),
    "Lughnasadh": (8, 1),
    "Samhain": (10, 31),
    "Yule (Winter Solstice)": (12, 21),  # sample placeholder
}

def next_full_moon():
    today = datetime.date.today()
    return ephem.next_full_moon(today).datetime().date()

def format_date(date: datetime.date) -> str:
    """Format dates as 'Day Month Year', e.g. 1 February 2025"""
    return date.strftime("%-d %B %Y") if hasattr(date, "strftime") else str(date)

@tasks.loop(hours=24)
async def daily_check():
    channel = bot.get_channel(CHANNEL_ID)
    today = datetime.date.today()
    today_str = format_date(today)

    # Sabbats
    for name, (month, day) in SABBATS.items():
        if today.month == month and today.day == day:
            role_mention = f"<@&{ROLE_ID}>" if ROLE_ID else ""
            await channel.send(
                f"✨ Blessed {name}! {role_mention}\n"
                f"Today is **{today_str}** — celebrate the turning of the Wheel of the Year. 🌿🔥"
            )

    # Full Moon
    fm_date = next_full_moon()
    if today == fm_date:
        await channel.send(
            f"🌕 Tonight is the **Full Moon** ({format_date(fm_date)})!\n"
            "A perfect time for ritual, release, and reflection."
        )

@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    daily_check.start()

bot.run(TOKEN)
