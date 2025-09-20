# GBPBot - bot.py
# Version: 1.2.3 build 5
# Last Updated: 2025-09-19
# Notes: Current build with fixed bot.py and cogs

import os
import discord
from discord.ext import commands
import asyncio
import traceback

from db import init_db as db_init
from utils.logger import robust_log  # centralized logger

from version_tracker import GBPBot_version, file_versions, get_file_version  # version tracker

# -----------------------
# Environment Variables
# -----------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# -----------------------
# GBPBot Version Tracker
# -----------------------
GBPBot_version = {
    "major": 1,
    "minor": 2,
    "patch": 3,
    "build": 5,  # increment on every build
    "date": "2025-09-19T09:05:00Z",
    "notes": "current build with fixed bot.py and cogs"
}

# -----------------------
# Intents & Bot Setup
# -----------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# -----------------------
# Custom Bot Class
# -----------------------
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Initialize database
        try:
            await db_init(self)
            await robust_log(self, "✅ Database initialized successfully.")
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self, f"[ERROR] Failed to initialize database\n{tb}")

        # Load cogs
        for cog in ["cogs.onboarding", "cogs.reminders", "cogs.commands"]:
            try:
                await self.load_extension(cog)
                await robust_log(self, f"✅ Loaded cog {cog}")
            except Exception:
                tb = traceback.format_exc()
                await robust_log(self, f"[ERROR] Failed to load cog {cog}\n{tb}")

        # Sync commands to guild for faster testing
        try:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            await robust_log(self, f"✅ Slash commands synced to guild {GUILD_ID}")
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self, f"[ERROR] Failed to sync slash commands\n{tb}")

    async def on_ready(self):
        await robust_log(self, f"🤖 {self.user} is online and ready!")

        # Start reminder loops if RemindersCog is loaded
        cog = self.get_cog("RemindersCog")
        if cog and hasattr(cog, "daily_loop"):
            if not cog.daily_loop.is_running():
                cog.daily_loop.start()
                await robust_log(self, "🌙 Daily reminder loop started.")

    async def on_command_error(self, ctx, error):
        # Catch uncaught exceptions globally
        tb = traceback.format_exc()
        await robust_log(self, f"[UNHANDLED COMMAND ERROR] {error}\n{tb}")

# -----------------------
# Async Main
# -----------------------
async def main():
    bot = MyBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

# -----------------------
# Change Tracking
# -----------------------
# [2025-09-20 12:30] v1.2.3b5 - Added version comment and change tracking comment
