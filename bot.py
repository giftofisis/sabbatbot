import discord
from discord.ext import tasks, commands
import datetime
import ephem
import os
from zoneinfo import ZoneInfo

# --- Environment Variables ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not TOKEN:
    raise ValueError("❌ DISCORD_BOT_TOKEN environment variable is missing!")
if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID environment variable is missing!")

CHANNEL_ID = int(CHANNEL_ID)

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True  # Required for commands
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Region Roles & Timezones ---
REGIONS = {
    "NA": {"role_id": 1416438886397251768, "tz": "America/New_York"},
    "SA": {"role_id": 1416438925140164809, "tz": "America/Sao_Paulo"},
    "EU": {"role_id": 1416439011517534288, "tz": "Europe/London"},
    "AF": {"role_id": 1416439116043649224, "tz": "Africa/Johannesburg"},
    "OC": {"role_id": 1416439141339758773, "tz": "Australia/Sydney"},
}

# --- Fixed Sabbats ---
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

# --- Helpers ---
def format_date(d: datetime.date) -> str:
    return d.strftime("%-d %B %Y")  # e.g., 1 February 2025

def get_sabbat_dates(year: int):
    dates = {}
    for name, (m, d) in SABBATS.items():
        dates[name] = datetime.date(year, m, d)
    return dates

def get_next_full_moon_for_tz(tz_name: str):
    now = datetime.datetime.now(ZoneInfo(tz_name))
    fm_utc = ephem.next_full_moon(now).datetime()
    return fm_utc.astimezone(ZoneInfo(tz_name)).date()

# --- Daily Reminder Loop ---
@tasks.loop(hours=24)
async def daily_check():
    for region_name, data in REGIONS.items():
        tz = data["tz"]
        role_id = data["role_id"]
        today = datetime.datetime.now(ZoneInfo(tz)).date()
        mention = f"<@&{role_id}>"

        # Sabbats
        sabbats = get_sabbat_dates(today.year)
        for name, date_val in sabbats.items():
            if today == date_val:
                await send_message(f"✨ Blessed {name} in {region_name}! {mention}\nToday is **{format_date(today)}** — celebrate the turning of the Wheel of the Year.")

        # Full Moon
        fm = get_next_full_moon_for_tz(tz)
        if today == fm:
            await send_message(f"🌕 Full Moon tonight in {region_name}! {mention}\nDate: **{format_date(fm)}** — perfect for ritual and reflection.")

async def send_message(content: str):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(content)
    else:
        print("❌ Channel not found. Check CHANNEL_ID.")

# --- Commands ---
@bot.command()
async def nextsabbat(ctx):
    """Shows the next sabbat for the member's region."""
    member = ctx.author
    user_roles = [role.id for role in member.roles]
    region = None
    for reg_name, data in REGIONS.items():
        if data["role_id"] in user_roles:
            region = data
            break

    tz = region["tz"] if region else "UTC"
    today = datetime.datetime.now(ZoneInfo(tz)).date()
    sabbats = get_sabbat_dates(today.year)
    upcoming = [(name, date_val) for name, date_val in sabbats.items() if date_val >= today]
    if not upcoming:
        upcoming = [(name, date_val) for name, date_val in sabbats.items()]

    name, date_val = sorted(upcoming, key=lambda x: x[1])[0]
    await ctx.send(f"Next Sabbat for your region: **{name}** on **{format_date(date_val)}**.")

@bot.command()
async def nextmoon(ctx):
    """Shows the next Full Moon for the member's region."""
    member = ctx.author
    user_roles = [role.id for role in member.roles]
    region = None
    for reg_name, data in REGIONS.items():
        if data["role_id"] in user_roles:
            region = data
            break

    tz = region["tz"] if region else "UTC"
    fm = get_next_full_moon_for_tz(tz)
    await ctx.send(f"Next Full Moon for your region: **{format_date(fm)}**.")

# --- On Ready Event with Test Message ---
@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    # Test message
    await send_message("✅ Test: I am online and sending regional reminders correctly!")
    # Start daily loop
    daily_check.start()

# --- Run Bot ---
bot.run(TOKEN)
