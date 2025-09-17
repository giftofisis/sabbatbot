import discord
from discord.ext import commands
from discord import app_commands
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
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# -----------------------
# Bot Setup
# -----------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# -----------------------
# Regions & Sabbats
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

def get_user_region(member):
    user_roles = [role.id for role in member.roles]
    return next((data for data in REGIONS.values() if data["role_id"] in user_roles), None)

# -----------------------
# Buttons for /reminder
# -----------------------
class ReminderButtons(discord.ui.View):
    def __init__(self, region_data):
        super().__init__(timeout=None)
        self.region_data = region_data

    @discord.ui.button(label="Next Sabbat", style=discord.ButtonStyle.primary)
    async def next_sabbat(self, interaction: discord.Interaction, button: discord.ui.Button):
        tz = self.region_data["tz"]
        emoji = self.region_data["emoji"]
        region_name = self.region_data["name"]

        today = datetime.datetime.now(ZoneInfo(tz)).date()
        sabbats = get_sabbat_dates(today.year)
        upcoming = [(n, d) for n, d in sabbats.items() if d >= today]
        if not upcoming:
            upcoming = list(sabbats.items())
        name, date_val = sorted(upcoming, key=lambda x: x[1])[0]

        await interaction.response.send_message(
            f"{emoji} Next Sabbat for your region: **{name}** on **{format_date(date_val)}**\n"
            f"Region: **{region_name}** | Timezone: **{tz}**", ephemeral=True
        )

    @discord.ui.button(label="Next Full Moon", style=discord.ButtonStyle.secondary)
    async def next_moon(self, interaction: discord.Interaction, button: discord.ui.Button):
        tz = self.region_data["tz"]
        emoji = self.region_data["emoji"]
        region_name = self.region_data["name"]

        fm = next_full_moon_for_tz(tz)
        phase_emoji = moon_phase_emoji(datetime.datetime.now(ZoneInfo(tz)))

        await interaction.response.send_message(
            f"{emoji} Next Full Moon: **{format_date(fm)}** {phase_emoji}\n"
            f"Region: **{region_name}** | Timezone: **{tz}**", ephemeral=True
        )

    @discord.ui.button(label="Random Quote", style=discord.ButtonStyle.success)
    async def random_quote(self, interaction: discord.Interaction, button: discord.ui.Button):
        quote = random.choice(QUOTES)
        await interaction.response.send_message(f"💫 {quote}", ephemeral=True)

# -----------------------
# Slash Command /reminder
# -----------------------
@tree.command(name="reminder", description="Get an interactive reminder with buttons", guild=discord.Object(id=GUILD_ID))
async def reminder(interaction: discord.Interaction):
    region_data = get_user_region(interaction.user)
    if not region_data:
        await interaction.response.send_message("⚠️ No region role detected. Please contact an admin.", ephemeral=True)
        return

    emoji = region_data["emoji"]
    color = region_data["color"]
    region_name = region_data["name"]
    tz = region_data["tz"]

    today = datetime.datetime.now(ZoneInfo(tz)).date()
    description = (
        f"Today is **{format_date(today)}**\n"
        f"Region: **{region_name}** | Timezone: **{tz}**\n"
        f"{random.choice(QUOTES)}"
    )

    embed = discord.Embed(title=f"{emoji} Daily Reminder", description=description, color=color)
    await interaction.response.send_message(embed=embed, view=ReminderButtons(region_data))

# -----------------------
# On Ready
# -----------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    await tree.sync(guild=discord.Object(id=GUILD_ID))

# -----------------------
# Run Bot
# -----------------------
bot.run(TOKEN)
