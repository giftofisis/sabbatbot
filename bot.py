import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# List of cogs
COGS = ["cogs.onboarding", "cogs.reminders", "cogs.commands"]

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load cog {cog}: {e}")

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"{bot.user} is online.")
    await load_cogs()
    print("🌙 All cogs loaded successfully.")

bot.run(TOKEN)
