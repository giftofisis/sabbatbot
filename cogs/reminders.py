import discord
from discord.ext import tasks, commands
from utils import REGIONS, format_date, next_full_moon_for_tz, moon_phase_emoji, get_sabbat_dates, get_all_quotes, get_all_journal_prompts, get_user_preferences, DB_FILE, sqlite3
import datetime
from zoneinfo import ZoneInfo
import random

class ReminderButtons(discord.ui.View):
    def __init__(self, region_data):
        super().__init__(timeout=None)
        self.region_data = region_data

    @discord.ui.button(label="Next Sabbat", style=discord.ButtonStyle.primary)
    async def next_sabbat(self, interaction, button):
        tz = self.region_data["tz"]
        today = datetime.datetime.now(ZoneInfo(tz)).date()
        sabbats = get_sabbat_dates(today.year)
        upcoming = [(n,d) for n,d in sabbats.items() if d>=today]
        if not upcoming: upcoming = list(sabbats.items())
        name, date_val = sorted(upcoming, key=lambda x: x[1])[0]
        await interaction.response.send_message(f"{self.region_data['emoji']} Next Sabbat: **{name}** on **{format_date(date_val)}**", ephemeral=True)

    @discord.ui.button(label="Next Full Moon", style=discord.ButtonStyle.secondary)
    async def next_moon(self, interaction, button):
        tz = self.region_data["tz"]
        fm = next_full_moon_for_tz(tz)
        await interaction.response.send_message(f"{self.region_data['emoji']} Next Full Moon: **{format_date(fm)}**", ephemeral=True)

    @discord.ui.button(label="Random Quote", style=discord.ButtonStyle.success)
    async def random_quote(self, interaction, button):
        quote = random.choice(get_all_quotes())
        await interaction.response.send_message(f"💫 {quote}", ephemeral=True)

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_reminder_loop.start()

    async def send_daily_reminder(self, user_id, prefs):
        if not prefs["subscribed"]: return
        user = self.bot.get_user(user_id)
        if not user: return
        region_data = REGIONS.get(prefs["region"])
        if not region_data: return
        now = datetime.datetime.now(ZoneInfo(region_data["tz"]))
        if now.strftime("%a") not in prefs["days"] or now.hour != prefs["hour"]:
            return
        embed = discord.Embed(
            title=f"{region_data['emoji']} Daily Reminder",
            description=f"Good morning, {user.name}!\nToday is **{format_date(now.date())}**\n💫 Quote: {random.choice(get_all_quotes())}\n📝 Journal Prompt: {random.choice(get_all_journal_prompts())}",
            color=region_data["color"]
        )
        await user.send(embed=embed, view=ReminderButtons(region_data))

    @tasks.loop(minutes=1)
    async def daily_reminder_loop(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, region, zodiac, reminder_hour, reminder_days, subscribed FROM users WHERE subscribed=1")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            user_id, region, zodiac, hour, days, subscribed = row
            prefs = {"region": region, "zodiac": zodiac, "hour": hour, "days": days.split(","), "subscribed": bool(subscribed)}
            await self.send_daily_reminder(user_id, prefs)

async def setup(bot):
    await bot.add_cog(Reminders(bot))
