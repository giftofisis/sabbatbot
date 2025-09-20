# GBPBot - reminders.py
# Version: 1.0.0 build 1
# Last Updated: 2025-09-20
# Notes: Handles all region-based daily reminders, Sabbat & full moon buttons, random quotes/journal prompts
#        Integrated safe_send and robust logging. Added version_tracker integration.

import discord  # line 1
from discord.ext import commands, tasks  # line 2
import datetime  # line 3
import ephem  # line 4
from zoneinfo import ZoneInfo  # line 5
import random  # line 6

from db import get_user_preferences, get_all_quotes, get_all_journal_prompts, get_all_subscribed_users  # line 7
from utils.logger import robust_log  # centralized logger import  # line 8
from utils.safe_send import safe_send  # line 9
from version_tracker import GBPBot_version, file_versions, get_file_version  # version tracker

# -----------------------
# Config
# -----------------------
REGIONS = {  # line 12
    "North America": {"name": "North America", "role_id": 1416438886397251768, "tz": "America/New_York", "emoji": "🗽", "color": 0x2ecc71},
    "South America": {"name": "South America", "role_id": 1416438925140164809, "tz": "America/Sao_Paulo", "emoji": "🌴", "color": 0xe67e22},
    "Europe": {"name": "Europe", "role_id": 1416439011517534288, "tz": "Europe/London", "emoji": "🍀", "color": 0x3498db},
    "Africa": {"name": "Africa", "role_id": 1416439116043649224, "tz": "Africa/Johannesburg", "emoji": "🌍", "color": 0xf1c40f},
    "Oceania & Asia": {"name": "Oceania & Asia", "role_id": 1416439141339758773, "tz": "Australia/Sydney", "emoji": "🌺", "color": 0x9b59b6},
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

# -----------------------
# Helpers
# -----------------------
def format_date(d: datetime.date) -> str:
    return d.strftime("%-d %B %Y")

def get_sabbat_dates(year: int):
    return {name: datetime.date(year, m, d) for name, (m, d) in SABBATS.items()}

def next_full_moon_for_tz(tz_name: str):
    now = datetime.datetime.now(ZoneInfo(tz_name))
    fm_utc = ephem.next_full_moon(now).datetime()
    return fm_utc.astimezone(ZoneInfo(tz_name)).date()

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

# -----------------------
# Reminder Buttons
# -----------------------
class ReminderButtons(discord.ui.View):
    def __init__(self, region_data):
        super().__init__(timeout=None)
        self.region_data = region_data

    @discord.ui.button(label="Next Sabbat", style=discord.ButtonStyle.primary)
    async def next_sabbat(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            tz = self.region_data["tz"]
            emoji = self.region_data["emoji"]
            region_name = self.region_data["name"]
            today = datetime.datetime.now(ZoneInfo(tz)).date()
            sabbats = get_sabbat_dates(today.year)
            upcoming = [(n, d) for n, d in sabbats.items() if d >= today]
            if not upcoming:
                upcoming = list(sabbats.items())
            name, date_val = sorted(upcoming, key=lambda x: x[1])[0]
            await safe_send(interaction, f"{emoji} Next Sabbat: **{name}** on **{format_date(date_val)}**\nRegion: **{region_name}** | Timezone: **{tz}**", ephemeral=True)
        except Exception as e:
            await robust_log(interaction.client, f"[ERROR] Failed Next Sabbat button", e)
            await safe_send(interaction, "⚠️ Could not fetch next Sabbat.", ephemeral=True)

    @discord.ui.button(label="Next Full Moon", style=discord.ButtonStyle.secondary)
    async def next_moon(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            tz = self.region_data["tz"]
            emoji = self.region_data["emoji"]
            region_name = self.region_data["name"]
            fm = next_full_moon_for_tz(tz)
            phase_emoji = moon_phase_emoji(datetime.datetime.now(ZoneInfo(tz)))
            await safe_send(interaction, f"{emoji} Next Full Moon: **{format_date(fm)}** {phase_emoji}\nRegion: **{region_name}** | Timezone: **{tz}**", ephemeral=True)
        except Exception as e:
            await robust_log(interaction.client, f"[ERROR] Failed Next Full Moon button", e)
            await safe_send(interaction, "⚠️ Could not fetch next full moon.", ephemeral=True)

    @discord.ui.button(label="Random Quote / Prompt", style=discord.ButtonStyle.success)
    async def random_quote_prompt(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            quote_list = await get_all_quotes()
            prompt_list = await get_all_journal_prompts()
            quote = random.choice(quote_list) if quote_list else "No quotes available."
            prompt = random.choice(prompt_list) if prompt_list else "No journal prompts available."
            content = f"💫 Quote: {quote}\n📝 Journal Prompt: {prompt}"
            await safe_send(interaction, content, ephemeral=True)
        except Exception as e:
            await robust_log(interaction.client, "[ERROR] Failed Random Quote/Prompt button", e)
            await safe_send(interaction, "⚠️ Could not fetch quote or journal prompt.", ephemeral=True)

# -----------------------
# Reminders Cog
# -----------------------
class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_loop.start()

    async def send_daily_reminder(self, user_id, prefs):
        try:
            if not prefs["subscribed"]:
                return
            user = self.bot.get_user(user_id)
            if not user:
                try:
                    user = await self.bot.fetch_user(user_id)
                except Exception as e:
                    await robust_log(self.bot, f"Failed to fetch user {user_id}", e)
                    return

            region_data = REGIONS.get(prefs["region"])
            if not region_data:
                return

            tz = ZoneInfo(region_data["tz"])
            now = datetime.datetime.now(tz)

            if now.strftime("%a") not in prefs["days"]:
                return
            if now.hour != prefs["hour"]:
                return

            quote_list = await get_all_quotes()
            prompt_list = await get_all_journal_prompts()

            embed = discord.Embed(
                title=f"{region_data['emoji']} Daily Reminder",
                description=(
                    f"Good morning, {user.name}! 🌞\n"
                    f"Today is **{format_date(now.date())}**\n"
                    f"Region: **{region_data['name']}** | Timezone: **{tz}**\n\n"
                    f"💫 Quote: {random.choice(quote_list)}\n"
                    f"📝 Journal Prompt: {random.choice(prompt_list)}"
                ),
                color=region_data["color"]
            )

            await safe_send(user, embed=embed, view=ReminderButtons(region_data))
            await robust_log(self.bot, f"Sent daily reminder to {user.id}")

        except Exception as e:
            await robust_log(self.bot, f"[ERROR] Sending daily reminder to {user_id}", e)

    @tasks.loop(minutes=1)
    async def daily_loop(self):
        try:
            users = await get_all_subscribed_users()
            for row in users:
                user_id, region, zodiac, hour, days, subscribed = row
                prefs = {
                    "region": region,
                    "zodiac": zodiac,
                    "hour": hour,
                    "days": days.split(","),
                    "subscribed": bool(subscribed)
                }
                await self.send_daily_reminder(user_id, prefs)
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] Failed running daily loop", e)

    @daily_loop.before_loop
    async def before_daily_loop(self):
        await self.bot.wait_until_ready()
        await robust_log(self.bot, "🌙 Daily reminder loop is ready to start.")

# -----------------------
# Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(RemindersCog(bot))
    await robust_log(bot, f"✅ Loaded RemindersCog (v{GBPBot_version.get('major')}.{GBPBot_version.get('minor')}.{GBPBot_version.get('patch')}.{GBPBot_version.get('build')})")

# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-20] v1.0.0b1 - Added version_tracker integration
# [2025-09-20] Added robust logging and safe_send to all reminder and button interactions
# [2025-09-20] Next Sabbat, Next Full Moon, Random Quote/Prompt buttons fully implemented
