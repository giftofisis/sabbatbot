import discord
from discord.ext import commands, tasks
import datetime
import ephem
from zoneinfo import ZoneInfo
import random
from .db import get_user_preferences, get_all_quotes, get_all_journal_prompts, sqlite3

# -----------------------
# Regions & Sabbats
# -----------------------
REGIONS = {
    "NA": {"name": "North America", "role_id": 1416438886397251768, "tz": "America/New_York", "emoji": "🇺🇸", "color": 0x2ecc71},
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
            f"{emoji} Next Sabbat: **{name}** on **{format_date(date_val)}**\nRegion: **{region_name}** | Timezone: **{tz}**",
            ephemeral=True
        )

    @discord.ui.button(label="Next Full Moon", style=discord.ButtonStyle.secondary)
    async def next_moon(self, interaction: discord.Interaction, button: discord.ui.Button):
        tz = self.region_data["tz"]
        emoji = self.region_data["emoji"]
        region_name = self.region_data["name"]
        fm = next_full_moon_for_tz(tz)
        phase_emoji = moon_phase_emoji(datetime.datetime.now(ZoneInfo(tz)))
        await interaction.response.send_message(
            f"{emoji} Next Full Moon: **{format_date(fm)}** {phase_emoji}\nRegion: **{region_name}** | Timezone: **{tz}**",
            ephemeral=True
        )

    @discord.ui.button(label="Random Quote", style=discord.ButtonStyle.success)
    async def random_quote(self, interaction: discord.Interaction, button: discord.ui.Button):
        quote = random.choice(get_all_quotes())
        await interaction.response.send_message(f"💫 {quote}", ephemeral=True)

# -----------------------
# Reminders Cog
# -----------------------
class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_loop.start()

    async def send_daily_reminder(self, user_id, prefs):
        user = self.bot.get_user(user_id)
        if not user or not prefs["subscribed"]:
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
        embed = discord.Embed(
            title=f"{region_data['emoji']} Daily Reminder",
            description=f"Good morning, {user.name}! 🌞\nToday is **{format_date(now.date())}**\nRegion: **{region_data['name']}** | Timezone: **{tz}**\n\n💫 Quote: {random.choice(get_all_quotes())}\n📝 Journal Prompt: {random.choice(get_all_journal_prompts())}",
            color=region_data["color"]
        )
        try:
            await user.send(embed=embed, view=ReminderButtons(region_data))
            print(f"✅ Sent reminder to {user.name}")
        except discord.Forbidden:
            print(f"⚠️ Cannot DM {user.name}")

    @tasks.loop(minutes=1)
    async def daily_loop(self):
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, region, zodiac, reminder_hour, reminder_days, subscribed FROM users WHERE subscribed = 1")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            user_id, region, zodiac, hour, days, subscribed = row
            prefs = {"region": region, "zodiac": zodiac, "hour": hour, "days": days.split(","), "subscribed": bool(subscribed)}
            await self.send_daily_reminder(user_id, prefs)

    @daily_loop.before_loop
    async def before_daily_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RemindersCog(bot))
