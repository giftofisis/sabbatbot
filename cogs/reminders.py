# GBPBot - reminders.py
# Version: 1.10.0
# Last Updated: 2025-09-21
# Notes:
# - Added hemisphere-aware sabbat reminder system.
# - Daily loop respects 'daily' flag from DB and now includes moon phase emoji.
# - Robust safe_send handling across all buttons, loops, and sabbat notifications.
# - Compatible with updated db.py get_all_subscribed_users.
# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-21 18:00 BST] v1.10.0 - Added hemisphere-aware sabbat reminders for DMs and optional channel posts.

import discord
from discord.ext import commands, tasks
import datetime
import ephem
from zoneinfo import ZoneInfo
import random

from db import get_user_preferences, get_all_quotes, get_all_journal_prompts, get_all_subscribed_users
from utils.logger import robust_log
from utils.safe_send import safe_send
from version_tracker import GBPBot_version, get_file_version
from utils.constants import REGIONS, SABBATS_HEMISPHERES

# Optional: set a channel ID to post sabbat notifications publicly
SABBAT_CHANNEL_ID = None  # Replace with channel ID if needed

# -----------------------
# Helpers
# -----------------------
def format_date(d: datetime.date) -> str:
    return d.strftime("%-d %B %Y")

def next_full_moon_for_tz(tz_name: str):
    now = datetime.datetime.now(ZoneInfo(tz_name))
    fm_utc = ephem.next_full_moon(now).datetime()
    return fm_utc.astimezone(ZoneInfo(tz_name)).date()

def moon_phase_emoji(date: datetime.date) -> str:
    moon = ephem.Moon(ephem.Date(date))
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

def get_sabbat_dates_for_hemisphere(hemisphere: str, year: int):
    return {name: datetime.date(year, m, d) for name, (m, d) in SABBATS_HEMISPHERES[hemisphere].items()}

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
            hemisphere = self.region_data.get("hemisphere", "north")
            today = datetime.datetime.now(ZoneInfo(tz)).date()
            sabbats = get_sabbat_dates_for_hemisphere(hemisphere, today.year)
            upcoming = [(n, d) for n, d in sabbats.items() if d >= today]
            if not upcoming:
                upcoming = list(sabbats.items())
            name, date_val = sorted(upcoming, key=lambda x: x[1])[0]
            await safe_send(interaction, f"{emoji} Next Sabbat: **{name}** on **{format_date(date_val)}**\nRegion: **{region_name}** | Timezone: **{tz}**", ephemeral=True, view=None)
        except Exception as e:
            await robust_log(interaction.client, f"[ERROR] Failed Next Sabbat button\n{e}")
            await safe_send(interaction, "⚠️ Could not fetch next Sabbat.", ephemeral=True, view=None)

    @discord.ui.button(label="Next Full Moon", style=discord.ButtonStyle.secondary)
    async def next_moon(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            tz = self.region_data["tz"]
            emoji = self.region_data["emoji"]
            region_name = self.region_data["name"]
            fm = next_full_moon_for_tz(tz)
            phase_emoji = moon_phase_emoji(datetime.datetime.now(ZoneInfo(tz)))
            await safe_send(interaction, f"{emoji} Next Full Moon: **{format_date(fm)}** {phase_emoji}\nRegion: **{region_name}** | Timezone: **{tz}**", ephemeral=True, view=None)
        except Exception as e:
            await robust_log(interaction.client, f"[ERROR] Failed Next Full Moon button\n{e}")
            await safe_send(interaction, "⚠️ Could not fetch next full moon.", ephemeral=True, view=None)

    @discord.ui.button(label="Random Quote / Prompt", style=discord.ButtonStyle.success)
    async def random_quote_prompt(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            quote_list = await get_all_quotes()
            prompt_list = await get_all_journal_prompts()
            quote = random.choice(quote_list) if quote_list else "No quotes available."
            prompt = random.choice(prompt_list) if prompt_list else "No journal prompts available."
            content = f"💫 Quote: {quote}\n📝 Journal Prompt: {prompt}"
            await safe_send(interaction, content, ephemeral=True, view=None)
        except Exception as e:
            await robust_log(interaction.client, f"[ERROR] Failed Random Quote/Prompt button\n{e}")
            await safe_send(interaction, "⚠️ Could not fetch quote or journal prompt.", ephemeral=True, view=None)

# -----------------------
# Reminders Cog
# -----------------------
class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_loop.start()
        self.sabbat_loop.start()

    async def send_daily_reminder(self, user_id, prefs):
        try:
            if not prefs["subscribed"] or not prefs["daily"]:
                return
            user = self.bot.get_user(user_id)
            if not user:
                try:
                    user = await self.bot.fetch_user(user_id)
                except Exception as e:
                    await robust_log(self.bot, f"Failed to fetch user {user_id}\n{e}")
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
            moon_emoji = moon_phase_emoji(now.date())

            embed = discord.Embed(
                title=f"{region_data['emoji']} Daily Reminder",
                description=(
                    f"Good morning, {user.name}! 🌞\n"
                    f"Today is **{format_date(now.date())}** {moon_emoji}\n"
                    f"Region: **{region_data['name']}** | Timezone: **{tz}**\n\n"
                    f"💫 Quote: {random.choice(quote_list)}\n"
                    f"📝 Journal Prompt: {random.choice(prompt_list)}"
                ),
                color=region_data["color"]
            )

            await safe_send(user, embed=embed, view=ReminderButtons(region_data))
            await robust_log(self.bot, f"Sent daily reminder to {user.id}")

        except Exception as e:
            await robust_log(self.bot, f"[ERROR] Sending daily reminder to {user_id}\n{e}")

    @tasks.loop(minutes=1)
    async def daily_loop(self):
        try:
            users = await get_all_subscribed_users()
            for row in users:
                try:
                    user_id, region, zodiac, hour, days, daily = row
                    prefs = {
                        "region": region,
                        "zodiac": zodiac,
                        "hour": hour,
                        "days": days.split(","),
                        "subscribed": True,
                        "daily": bool(daily)
                    }
                    await self.send_daily_reminder(user_id, prefs)
                except Exception as e:
                    await robust_log(self.bot, f"[ERROR] Failed sending reminder to user {row[0]}\n{e}")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] Failed running daily loop\n{e}")

    @daily_loop.before_loop
    async def before_daily_loop(self):
        await self.bot.wait_until_ready()
        await robust_log(self.bot, "🌙 Daily reminder loop is ready to start.")

    # -----------------------
    # Sabbat Loop
    # -----------------------
    @tasks.loop(minutes=60)
    async def sabbat_loop(self):
        try:
            users = await get_all_subscribed_users()
            today = datetime.date.today()
            for row in users:
                try:
                    user_id, region, zodiac, hour, days, daily = row
                    region_data = REGIONS.get(region)
                    if not region_data:
                        continue
                    hemisphere = region_data.get("hemisphere", "north")
                    sabbats = get_sabbat_dates_for_hemisphere(hemisphere, today.year)
                    delta_msgs = {7: "in 7 days", 1: "tomorrow", 0: "today!"}
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    for name, date_val in sabbats.items():
                        delta = (date_val - today).days
                        if delta in delta_msgs:
                            if delta == 7:
                                msg = f"🪐 Upcoming Sabbat ({hemisphere.title()} Hemisphere): **{name}** {delta_msgs[delta]}"
                            elif delta == 1:
                                msg = f"🌿 **{name}** is tomorrow! ({hemisphere.title()} Hemisphere Sabbat)"
                            else:
                                msg = f"🔥 Happy **{name}**! Today is the Sabbat in the {hemisphere.title()} Hemisphere 🔥"
                            await safe_send(user, msg)
                            if SABBAT_CHANNEL_ID:
                                channel = self.bot.get_channel(SABBAT_CHANNEL_ID) or await self.bot.fetch_channel(SABBAT_CHANNEL_ID)
                                await safe_send(channel, msg)
                except Exception as e:
                    await robust_log(self.bot, f"[ERROR] Sabbat reminder for user {row[0]}\n{e}")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] Sabbat loop failed\n{e}")

    @sabbat_loop.before_loop
    async def before_sabbat_loop(self):
        await self.bot.wait_until_ready()
        await robust_log(self.bot, "🌙 Sabbat reminder loop is ready to start.")

# -----------------------
# Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(RemindersCog(bot))
    await robust_log(bot, f"✅ RemindersCog loaded | version {get_file_version('reminders.py')}")
