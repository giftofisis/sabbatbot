import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import ephem
import os
from zoneinfo import ZoneInfo
import random

# -----------------------
# Environment Variables
# -----------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))  # For slash commands registration
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

if not TOKEN:
    raise ValueError("❌ DISCORD_BOT_TOKEN missing!")
if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID missing!")
if not GUILD_ID:
    raise ValueError("❌ GUILD_ID missing!")

# -----------------------
# Bot Setup
# -----------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# -----------------------
# Regions
# -----------------------
REGIONS = {
    "NA": {"name": "North America", "role_id": 1416438886397251768, "tz": "America/New_York", "emoji": "🌲", "color": 0x2ecc71},
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

QUOTES = [
    "🌿 May the Wheel of the Year turn in your favor.",
    "🌕 Reflect, release, and renew under the Moon's light.",
    "✨ Blessed be, traveler of the mystical paths.",
    "🔥 May your rituals be fruitful and your intentions clear.",
    "🌱 Growth is guided by the cycles of the Earth and Moon."
]

# -----------------------
# Helpers
# -----------------------
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

async def send_embed(title, description, color):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=title, description=description, color=color)
        await channel.send(embed=embed)
    else:
        print("❌ Channel not found.")

def get_user_region(member):
    user_roles = [role.id for role in member.roles]
    return next((data for data in REGIONS.values() if data["role_id"] in user_roles), None)

# -----------------------
# Region Scheduler
# -----------------------
async def daily_region_check(region_name, role_id, tz_name, emoji, color):
    while True:
        now = datetime.datetime.now(ZoneInfo(tz_name))
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= target:
            target += datetime.timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

        today = datetime.datetime.now(ZoneInfo(tz_name)).date()
        mention = f"<@&{role_id}>"

        # Sabbats
        sabbats = get_sabbat_dates(today.year)
        for name, date_val in sabbats.items():
            if today == date_val:
                description = (
                    f"{mention} Today is **{format_date(today)}** — celebrate the Wheel of the Year.\n"
                    f"Region: **{region_name}** | Timezone: **{tz_name}**\n"
                    f"{random.choice(QUOTES)}"
                )
                await send_embed(f"{emoji} Blessed {name} in {region_name}", description, color)

        # Full Moon
        fm = next_full_moon_for_tz(tz_name)
        if today == fm:
            description = (
                f"{mention} Date: **{format_date(fm)}** — perfect for ritual and reflection.\n"
                f"Region: **{region_name}** | Timezone: **{tz_name}**\n"
                f"{random.choice(QUOTES)}"
            )
            await send_embed(f"{emoji} Full Moon tonight in {region_name}", description, color)

# -----------------------
# Slash Commands
# -----------------------
@tree.command(name="nextsabbat", description="Shows the next Sabbat for your region", guild=discord.Object(id=GUILD_ID))
async def nextsabbat(interaction: discord.Interaction):
    region_data = get_user_region(interaction.user)
    if not region_data:
        await interaction.response.send_message("⚠️ No region role detected. Please contact an admin.", ephemeral=True)
        return

    tz = region_data["tz"]
    emoji = region_data["emoji"]
    color = region_data["color"]
    region_name = region_data["name"]

    today = datetime.datetime.now(ZoneInfo(tz)).date()
    sabbats = get_sabbat_dates(today.year)
    upcoming = [(n, d) for n, d in sabbats.items() if d >= today]
    if not upcoming:
        upcoming = list(sabbats.items())
    name, date_val = sorted(upcoming, key=lambda x: x[1])[0]

    await interaction.response.send_message(
        f"{emoji} Next Sabbat for your region: **{name}** on **{format_date(date_val)}**\n"
        f"Region: **{region_name}** | Timezone: **{tz}**"
    )

@tree.command(name="nextmoon", description="Shows the next Full Moon for your region", guild=discord.Object(id=GUILD_ID))
async def nextmoon(interaction: discord.Interaction):
    region_data = get_user_region(interaction.user)
    if not region_data:
        await interaction.response.send_message("⚠️ No region role detected. Please contact an admin.", ephemeral=True)
        return

    tz = region_data["tz"]
    emoji = region_data["emoji"]
    color = region_data["color"]
    region_name = region_data["name"]

    fm = next_full_moon_for_tz(tz)
    phase_emoji = moon_phase_emoji(datetime.datetime.now(ZoneInfo(tz)))

    await interaction.response.send_message(
        f"{emoji} Next Full Moon for your region: **{format_date(fm)}** {phase_emoji}\n"
        f"Region: **{region_name}** | Timezone: **{tz}**"
    )

# -----------------------
# On Ready
# -----------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    await send_embed("✅ Bot Online", "I am online and sending region-specific 9AM reminders!", 0x1abc9c)

    for region_name, data in REGIONS.items():
        bot.loop.create_task(daily_region_check(region_name, data["role_id"], data["tz"], data["emoji"], data["color"]))

# -----------------------
# Run Bot
# -----------------------
bot.run(TOKEN)
