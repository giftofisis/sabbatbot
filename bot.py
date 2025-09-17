import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import datetime
import ephem
import os
from zoneinfo import ZoneInfo
import random
import sqlite3

# -----------------------
# Environment Variables
# -----------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# -----------------------
# Bot Setup
# -----------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

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

QUOTES = [
    "🌿 May the Wheel of the Year turn in your favor.",
    "🌕 Reflect, release, and renew under the Moon's light.",
    "✨ Blessed be, traveler of the mystical paths.",
    "🔥 May your rituals be fruitful and your intentions clear.",
    "🌱 Growth is guided by the cycles of the Earth and Moon"
]

JOURNAL_PROMPTS = [
    "What are three things you are grateful for today?",
    "Reflect on a recent challenge and what you learned.",
    "What intention do you want to set for today?"
]

# -----------------------
# SQLite Setup
# -----------------------
conn = sqlite3.connect("bot_data.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    region TEXT,
    zodiac TEXT,
    reminder_hour INTEGER DEFAULT 9,
    reminder_days TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri,Sat,Sun',
    subscribed INTEGER DEFAULT 1
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS journal_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT
)
""")
conn.commit()
conn.close()

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

def count_users_in_role(guild, role_id):
    role = guild.get_role(role_id)
    return len(role.members) if role else 0

# -----------------------
# SQLite User Management
# -----------------------
def save_user_preferences(user_id, region=None, zodiac=None, hour=None, days=None):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, region, zodiac, reminder_hour, reminder_days, subscribed)
    VALUES (?, ?, ?, ?, ?, COALESCE((SELECT subscribed FROM users WHERE user_id=?),1))
    """, (user_id, region, zodiac, hour or 9, ",".join(days) if days else 'Mon,Tue,Wed,Thu,Fri,Sat,Sun', user_id))
    conn.commit()
    conn.close()

def get_user_preferences(user_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT region, zodiac, reminder_hour, reminder_days, subscribed FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        region, zodiac, hour, days, subscribed = row
        return {
            "region": region,
            "zodiac": zodiac,
            "hour": hour,
            "days": days.split(","),
            "subscribed": bool(subscribed)
        }
    return None

def set_subscription(user_id, status: bool):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET subscribed = ? WHERE user_id = ?", (int(status), user_id))
    conn.commit()
    conn.close()

def add_quote(quote):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quotes (quote) VALUES (?)", (quote,))
    conn.commit()
    conn.close()

def get_all_quotes():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT quote FROM quotes")
    quotes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return QUOTES + quotes

def add_journal_prompt(prompt):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO journal_prompts (prompt) VALUES (?)", (prompt,))
    conn.commit()
    conn.close()

def get_all_journal_prompts():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT prompt FROM journal_prompts")
    prompts = [row[0] for row in cursor.fetchall()]
    conn.close()
    return JOURNAL_PROMPTS + prompts

# -----------------------
# Onboarding Buttons
# -----------------------
class OnboardingButton(discord.ui.Button):
    def __init__(self, label, emoji, member, region_key):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
        self.member = member
        self.region_key = region_key

    async def callback(self, interaction: discord.Interaction):
        guild = bot.get_guild(GUILD_ID)
        region_data = REGIONS[self.region_key]
        role = guild.get_role(region_data["role_id"])
        # Remove previous roles
        for rdata in REGIONS.values():
            prev_role = guild.get_role(rdata["role_id"])
            if prev_role in self.member.roles:
                await self.member.remove_roles(prev_role)
        await self.member.add_roles(role)
        save_user_preferences(self.member.id, region=self.region_key)
        await interaction.response.send_message(
            f"✅ You have been assigned the role for **{region_data['name']}**.", ephemeral=True
        )
        self.view.stop()

class OnboardingView(discord.ui.View):
    def __init__(self, member, timeout=300):
        super().__init__(timeout=timeout)
        self.member = member
        for key, data in REGIONS.items():
            self.add_item(OnboardingButton(label=data["name"], emoji=data["emoji"], member=member, region_key=key))

# -----------------------
# Onboarding Handlers
# -----------------------
async def start_onboarding(member):
    try:
        dm_channel = await member.create_dm()
        embed = discord.Embed(
            title="Welcome! 🌙",
            description="Please select your region by clicking one of the buttons below to receive your role and start receiving reminders.",
            color=0x9b59b6
        )
        await dm_channel.send(embed=embed, view=OnboardingView(member))
    except Exception as e:
        print(f"Failed to DM {member}: {e}")

@bot.event
async def on_member_join(member):
    await start_onboarding(member)

@tree.command(name="onboard", description="Start the onboarding process manually", guild=discord.Object(id=GUILD_ID))
async def onboard(interaction: discord.Interaction):
    await start_onboarding(interaction.user)
    await interaction.response.send_message("✅ Check your DMs to complete onboarding!", ephemeral=True)

# -----------------------
# /help Command
# -----------------------
@tree.command(name="help", description="Shows all available commands", guild=discord.Object(id=GUILD_ID))
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🌙 Bot Help", color=0x9b59b6)
    embed.add_field(name="/onboard", value="Start onboarding to select region, zodiac, and reminders.", inline=False)
    embed.add_field(name="/reminder", value="Receive your daily interactive reminder immediately.", inline=False)
    embed.add_field(name="/status", value="Show bot status, next Sabbat, full moon, and user counts.", inline=False)
    embed.add_field(name="/submit_quote <text>", value="Submit an inspirational quote for reminders.", inline=False)
    embed.add_field(name="/submit_journal <text>", value="Submit a journal prompt for daily reminders.", inline=False)
    embed.add_field(name="/unsubscribe", value="Stop receiving daily DM reminders.", inline=False)
    await interaction.user.send(embed=embed)
    await interaction.response.send_message("✅ Help sent to your DMs.", ephemeral=True)
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
# /reminder Command
# -----------------------
@tree.command(name="reminder", description="Get an interactive reminder", guild=discord.Object(id=GUILD_ID))
async def reminder(interaction: discord.Interaction):
    prefs = get_user_preferences(interaction.user.id)
    if not prefs or not prefs["subscribed"]:
        await interaction.response.send_message("⚠️ You are not subscribed. Use `/onboard` to set your preferences.", ephemeral=True)
        return
    region_data = REGIONS.get(prefs["region"])
    if not region_data:
        await interaction.response.send_message("⚠️ Region not set. Please complete onboarding.", ephemeral=True)
        return
    emoji = region_data["emoji"]
    color = region_data["color"]
    tz = region_data["tz"]
    today = datetime.datetime.now(ZoneInfo(tz)).date()
    embed = discord.Embed(
        title=f"{emoji} Daily Reminder",
        description=f"Good morning, {interaction.user.name}! 🌞\nToday is **{format_date(today)}**\nRegion: **{region_data['name']}** | Timezone: **{tz}**\n\n💫 Quote: {random.choice(get_all_quotes())}\n📝 Journal Prompt: {random.choice(get_all_journal_prompts())}",
        color=color
    )
    await interaction.response.send_message(embed=embed, view=ReminderButtons(region_data))

# -----------------------
# /submit_quote Command
# -----------------------
@tree.command(name="submit_quote", description="Submit an inspirational quote", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(quote="The quote text to submit")
async def submit_quote(interaction: discord.Interaction, quote: str):
    add_quote(quote)
    await interaction.response.send_message("✅ Quote submitted successfully.", ephemeral=True)

# -----------------------
# /submit_journal Command
# -----------------------
@tree.command(name="submit_journal", description="Submit a journal prompt", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(prompt="The journal prompt text to submit")
async def submit_journal(interaction: discord.Interaction, prompt: str):
    add_journal_prompt(prompt)
    await interaction.response.send_message("✅ Journal prompt submitted successfully.", ephemeral=True)

# -----------------------
# /unsubscribe Command
# -----------------------
@tree.command(name="unsubscribe", description="Stop receiving daily reminders", guild=discord.Object(id=GUILD_ID))
async def unsubscribe(interaction: discord.Interaction):
    set_subscription(interaction.user.id, False)
    await interaction.response.send_message("❌ You have unsubscribed from daily reminders.", ephemeral=True)

# -----------------------
# /status Command
# -----------------------
@tree.command(name="status", description="Shows bot status and upcoming events", guild=discord.Object(id=GUILD_ID))
async def status(interaction: discord.Interaction):
    now = datetime.datetime.utcnow()
    embed = discord.Embed(title="🌙 Bot Status", color=0x1abc9c)
    embed.add_field(name="Current UTC Time", value=now.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    guild = interaction.guild
    for data in REGIONS.values():
        tz = ZoneInfo(data["tz"])
        today = datetime.datetime.now(tz).date()
        sabbats = get_sabbat_dates(today.year)
        upcoming_sabbat = min((d for d in sabbats.values() if d >= today), default=None)
        next_moon = next_full_moon_for_tz(data["tz"])
        users_count = count_users_in_role(guild, data["role_id"])
        embed.add_field(
            name=f"{data['emoji']} {data['name']} ({data['tz']})",
            value=f"Next Sabbat: {format_date(upcoming_sabbat)}\nNext Full Moon: {format_date(next_moon)}\nUsers in region: {users_count}",
            inline=False
        )
    await interaction.response.send_message(embed=embed)

# -----------------------
# Daily Reminder Task
# -----------------------
async def send_daily_reminder(user_id, prefs):
    user = bot.get_user(user_id)
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
    await user.send(embed=embed, view=ReminderButtons(region_data))

@tasks.loop(minutes=1)
async def daily_reminder_loop():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, region, zodiac, reminder_hour, reminder_days, subscribed FROM users WHERE subscribed = 1")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        user_id, region, zodiac, hour, days, subscribed = row
        prefs = {"region": region, "zodiac": zodiac, "hour": hour, "days": days.split(","), "subscribed": bool(subscribed)}
        await send_daily_reminder(user_id, prefs)

# -----------------------
# On Ready Event
# -----------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    daily_reminder_loop.start()
    # Optional startup DM to all users or server announcement
    print("🌙 Daily reminder loop started.")

# -----------------------
# Run Bot
# -----------------------
bot.run(TOKEN)  # Line 434
