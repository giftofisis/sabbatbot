import discord
from discord.ext import commands, tasks
import datetime
import ephem
from zoneinfo import ZoneInfo
import random
from cogs.db import get_all_subscribed_users, get_all_quotes, get_all_journal_prompts

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

def count_users_in_role(guild: discord.Guild, role_id: int) -> int:
    role = guild.get_role(role_id)
    return len(role.members) if role else 0

class ReminderButtons(discord.ui.View):
    def __init__(self, region_data):
        super().__init__(timeout=None)
        self.region_data = region_data

    @discord.ui.button(label="Next Sabbat", style=discord.ButtonStyle.primary)
    async def next_sabbat(self, interaction: discord.Interaction, button: discord.ui.Button):
        tz = self.region_data["tz"]
        today = datetime.datetime.now(ZoneInfo(tz)).date()
        sabbats = get_sabbat_dates(today.year)
        upcoming = [(n, d) for n, d in sabbats.items() if d >= today]
        if not upcoming:
            upcoming = list(sabbats.items())
        name, date_val = sorted(upcoming, key=lambda x: x[1])[0]
        await interaction.response.send_message(
            f"{self.region_data['emoji']} Next Sabbat: **{name}** on **{format_date(date_val)}**\nRegion: **{self.region_data['name']}** | Timezone: **{tz}**",
            ephemeral=True
        )

    @discord.ui.button(label="Next Full Moon", style=discord.ButtonStyle.secondary)
    async def next_moon(self, interaction: discord.Interaction, button: discord.ui.Button):
        tz = self.region_data["tz"]
        fm = next_full_moon_for_tz(tz)
        phase_emoji = moon_phase_emoji(datetime.datetime.now(ZoneInfo(tz)))
        await interaction.response.send_message(
            f"{self.region_data['emoji']} Next Full Moon: **{format_date(fm)}** {phase_emoji}\nRegion: **{self.region_data['name']}** | Timezone: **{tz}**",
            ephemeral=True
        )

    @discord.ui.button(label="Random Quote", style=discord.ButtonStyle.success)
    async def random_quote(self, interaction: discord.Interaction, button: discord.ui.Button):
        quote = random.choice(get_all_quotes())
        await interaction.response.send_message(f"💫 {quote}", ephemeral=True)

class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Do NOT start loop here; start it on-ready in bot.py to avoid duplicate starts.

    async def send_daily_reminder(self, user_id: int, prefs: dict, force: bool = False):
        user = self.bot.get_user(user_id)
        if user is None:
            return
        if not prefs.get("subscribed", False) and not force:
            return
        region_key = prefs.get("region")
        region_data = REGIONS.get(region_key)
        if not region_data and not force:
            return

        tz = ZoneInfo(region_data["tz"]) if region_data else ZoneInfo("UTC")
        now = datetime.datetime.now(tz)

        # If not forced, check day + hour (minute 0)
        if not force:
            if now.strftime("%a") not in prefs.get("days", []):
                return
            if now.hour != prefs.get("hour", 9) or now.minute != 0:
                return

        # Build embed
        embed = discord.Embed(
            title=f"{region_data['emoji'] if region_data else '🌙'} Daily Reminder",
            description=(
                f"Good morning, {user.name}! 🌞\n"
                f"Today is **{format_date(now.date())}**\n"
                f"Region: **{region_data['name']}** | Timezone: **{region_data['tz']}**\n\n"
                f"💫 Quote: {random.choice(get_all_quotes())}\n"
                f"📝 Journal Prompt: {random.choice(get_all_journal_prompts())}"
            ),
            color=region_data["color"] if region_data else 0x95a5a6
        )

        try:
            await user.send(embed=embed, view=ReminderButtons(region_data or {"name":"Unknown","tz":"UTC","emoji":"🌙","color":0x95a5a6}))
            print(f"✅ Sent reminder to {user} ({user.id})")
        except discord.Forbidden:
            print(f"⚠️ Cannot DM {user} ({user.id})")
        except Exception as e:
            print(f"❌ Error sending DM to {user} ({user.id}): {e}")

    @tasks.loop(minutes=1)
    async def daily_loop(self):
        rows = get_all_subscribed_users()
        for row in rows:
            user_id, region, zodiac, hour, days, subscribed = row
            prefs = {
                "region": region,
                "zodiac": zodiac,
                "hour": hour,
                "days": days.split(",") if days else ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
                "subscribed": bool(subscribed)
            }
            await self.send_daily_reminder(user_id, prefs, force=False)

    @daily_loop.before_loop
    async def before_daily_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RemindersCog(bot))
