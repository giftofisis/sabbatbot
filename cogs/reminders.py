import discord  # line 1
from discord.ext import commands, tasks  # line 2
import datetime  # line 3
import ephem  # line 4
from zoneinfo import ZoneInfo  # line 5
import random  # line 6

from db import get_user_preferences, get_all_quotes, get_all_journal_prompts, get_all_subscribed_users  # line 7
from utils.logger import robust_log  # centralized logger import  # line 8
from utils.safe_send import safe_send  # line 9

# -----------------------
# Config
# -----------------------
REGIONS = {  # line 12
    "North America": {"name": "North America", "role_id": 1416438886397251768, "tz": "America/New_York", "emoji": "🗽", "color": 0x2ecc71},  # line 13
    "South America": {"name": "South America", "role_id": 1416438925140164809, "tz": "America/Sao_Paulo", "emoji": "🌴", "color": 0xe67e22},  # line 14
    "Europe": {"name": "Europe", "role_id": 1416439011517534288, "tz": "Europe/London", "emoji": "🍀", "color": 0x3498db},  # line 15
    "Africa": {"name": "Africa", "role_id": 1416439116043649224, "tz": "Africa/Johannesburg", "emoji": "🌍", "color": 0xf1c40f},  # line 16
    "Oceania & Asia": {"name": "Oceania & Asia", "role_id": 1416439141339758773, "tz": "Australia/Sydney", "emoji": "🌺", "color": 0x9b59b6},  # line 17
}  # line 18

SABBATS = {  # line 20
    "Imbolc": (2, 1),  # line 21
    "Ostara": (3, 20),  # line 22
    "Beltane": (5, 1),  # line 23
    "Litha": (6, 21),  # line 24
    "Lughnasadh": (8, 1),  # line 25
    "Mabon": (9, 22),  # line 26
    "Samhain": (10, 31),  # line 27
    "Yule": (12, 21),  # line 28
}  # line 29

# -----------------------
# Helpers
# -----------------------
def format_date(d: datetime.date) -> str:  # line 32
    return d.strftime("%-d %B %Y")  # line 33

def get_sabbat_dates(year: int):  # line 35
    return {name: datetime.date(year, m, d) for name, (m, d) in SABBATS.items()}  # line 36

def next_full_moon_for_tz(tz_name: str):  # line 38
    now = datetime.datetime.now(ZoneInfo(tz_name))  # line 39
    fm_utc = ephem.next_full_moon(now).datetime()  # line 40
    return fm_utc.astimezone(ZoneInfo(tz_name)).date()  # line 41

def moon_phase_emoji(date: datetime.date) -> str:  # line 43
    moon = ephem.Moon(date)  # line 44
    phase = moon.phase  # line 45
    if phase < 10:  # line 46
        return "🌑"  # line 47
    elif phase < 50:  # line 48
        return "🌒"  # line 49
    elif phase < 60:  # line 50
        return "🌕"  # line 51
    elif phase < 90:  # line 52
        return "🌘"  # line 53
    else:  # line 54
        return "🌑"  # line 55

# -----------------------
# Reminder Buttons
# -----------------------
class ReminderButtons(discord.ui.View):  # line 58
    def __init__(self, region_data):  # line 59
        super().__init__(timeout=None)  # line 60
        self.region_data = region_data  # line 61

    @discord.ui.button(label="Next Sabbat", style=discord.ButtonStyle.primary)  # line 63
    async def next_sabbat(self, interaction: discord.Interaction, button: discord.ui.Button):  # line 64
        try:  # line 65
            tz = self.region_data["tz"]  # line 66
            emoji = self.region_data["emoji"]  # line 67
            region_name = self.region_data["name"]  # line 68
            today = datetime.datetime.now(ZoneInfo(tz)).date()  # line 69
            sabbats = get_sabbat_dates(today.year)  # line 70
            upcoming = [(n, d) for n, d in sabbats.items() if d >= today]  # line 71
            if not upcoming:  # line 72
                upcoming = list(sabbats.items())  # line 73
            name, date_val = sorted(upcoming, key=lambda x: x[1])[0]  # line 74
            await safe_send(interaction, f"{emoji} Next Sabbat: **{name}** on **{format_date(date_val)}**\nRegion: **{region_name}** | Timezone: **{tz}**", ephemeral=True)  # line 75
        except Exception as e:  # line 76
            await robust_log(interaction.client, f"[ERROR] Failed Next Sabbat button", e)  # line 77
            await safe_send(interaction, "⚠️ Could not fetch next Sabbat.", ephemeral=True)  # line 78

    @discord.ui.button(label="Next Full Moon", style=discord.ButtonStyle.secondary)  # line 80
    async def next_moon(self, interaction: discord.Interaction, button: discord.ui.Button):  # line 81
        try:  # line 82
            tz = self.region_data["tz"]  # line 83
            emoji = self.region_data["emoji"]  # line 84
            region_name = self.region_data["name"]  # line 85
            fm = next_full_moon_for_tz(tz)  # line 86
            phase_emoji = moon_phase_emoji(datetime.datetime.now(ZoneInfo(tz)))  # line 87
            await safe_send(interaction, f"{emoji} Next Full Moon: **{format_date(fm)}** {phase_emoji}\nRegion: **{region_name}** | Timezone: **{tz}**", ephemeral=True)  # line 88
        except Exception as e:  # line 89
            await robust_log(interaction.client, f"[ERROR] Failed Next Full Moon button", e)  # line 90
            await safe_send(interaction, "⚠️ Could not fetch next full moon.", ephemeral=True)  # line 91

    @discord.ui.button(label="Random Quote / Prompt", style=discord.ButtonStyle.success)  # line 93
    async def random_quote_prompt(self, interaction: discord.Interaction, button: discord.ui.Button):  # line 94
        try:  # line 95
            quote_list = await get_all_quotes()  # line 96
            prompt_list = await get_all_journal_prompts()  # line 97
            quote = random.choice(quote_list) if quote_list else "No quotes available."  # line 98
            prompt = random.choice(prompt_list) if prompt_list else "No journal prompts available."  # line 99
            content = f"💫 Quote: {quote}\n📝 Journal Prompt: {prompt}"  # line 100
            await safe_send(interaction, content, ephemeral=True)  # line 101
        except Exception as e:  # line 102
            await robust_log(interaction.client, "[ERROR] Failed Random Quote/Prompt button", e)  # line 103
            await safe_send(interaction, "⚠️ Could not fetch quote or journal prompt.", ephemeral=True)  # line 104

# -----------------------
# Reminders Cog
# -----------------------
class RemindersCog(commands.Cog):  # line 107
    def __init__(self, bot):  # line 108
        self.bot = bot  # line 109
        self.daily_loop.start()  # line 110

    async def send_daily_reminder(self, user_id, prefs):  # line 112
        try:  # line 113
            if not prefs["subscribed"]:  # line 114
                return  # line 115
            user = self.bot.get_user(user_id)  # line 116
            if not user:  # line 117
                try:  # line 118
                    user = await self.bot.fetch_user(user_id)  # line 119
                except Exception as e:  # line 120
                    await robust_log(self.bot, f"Failed to fetch user {user_id}", e)  # line 121
                    return  # line 122

            region_data = REGIONS.get(prefs["region"])  # line 124
            if not region_data:  # line 125
                return  # line 126

            tz = ZoneInfo(region_data["tz"])  # line 128
            now = datetime.datetime.now(tz)  # line 129

            if now.strftime("%a") not in prefs["days"]:  # line 131
                return  # line 132
            if now.hour != prefs["hour"]:  # line 133
                return  # line 134

            quote_list = await get_all_quotes()  # line 136
            prompt_list = await get_all_journal_prompts()  # line 137

            embed = discord.Embed(  # line 139
                title=f"{region_data['emoji']} Daily Reminder",  # line 140
                description=(  # line 141
                    f"Good morning, {user.name}! 🌞\n"  # line 142
                    f"Today is **{format_date(now.date())}**\n"  # line 143
                    f"Region: **{region_data['name']}** | Timezone: **{tz}**\n\n"  # line 144
                    f"💫 Quote: {random.choice(quote_list)}\n"  # line 145
                    f"📝 Journal Prompt: {random.choice(prompt_list)}"  # line 146
                ),  # line 147
                color=region_data["color"]  # line 148
            )  # line 149

            await safe_send(user, embed=embed, view=ReminderButtons(region_data))  # line 151
            await robust_log(self.bot, f"Sent daily reminder to {user.id}")  # line 152

        except Exception as e:  # line 154
            await robust_log(self.bot, f"[ERROR] Sending daily reminder to {user_id}", e)  # line 155

    @tasks.loop(minutes=1)  # line 157
    async def daily_loop(self):  # line 158
        try:  # line 159
            users = await get_all_subscribed_users()  # line 160
            for row in users:  # line 161
                user_id, region, zodiac, hour, days, subscribed = row  # line 162
                prefs = {  # line 163
                    "region": region,  # line 164
                    "zodiac": zodiac,  # line 165
                    "hour": hour,  # line 166
                    "days": days.split(","),  # line 167
                    "subscribed": bool(subscribed)  # line 168
                }  # line 169
                await self.send_daily_reminder(user_id, prefs)  # line 170
        except Exception as e:  # line 171
            await robust_log(self.bot, f"[ERROR] Failed running daily loop", e)  # line 172

    @daily_loop.before_loop  # line 174
    async def before_daily_loop(self):  # line 175
        await self.bot.wait_until_ready()  # line 176
        await robust_log(self.bot, "🌙 Daily reminder loop is ready to start.")  # line 177

# -----------------------
# Setup
# -----------------------
async def setup(bot):  # line 180
    await bot.add_cog(RemindersCog(bot))  # line 181
#endline181
