# GBPBot - bot.py
# Version: 1.2.4 build 6
# Last Updated: 2025-09-20
# Notes: Safe_send fixed, onboarding flow robust, daily reminder loop fixed, version tracking added to all cogs

import os
import discord
from discord.ext import commands
import asyncio
import traceback

from db import init_db as db_init
from utils.logger import robust_log
from version_tracker import GBPBot_version, get_file_version

# -----------------------
# Environment Variables
# -----------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

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
                await robust_log(
                    self,
                    f"✅ Loaded cog {cog} | version {get_file_version(cog.split('.')[-1] + '.py')}"
                )
            except Exception:
                tb = traceback.format_exc()
                await robust_log(self, f"[ERROR] Failed to load cog {cog}\n{tb}")

        # Sync commands to guild
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
# CHANGE LOG
# -----------------------
# [2025-09-20 12:50] v1.2.4b6 - Updated safe_send, onboarding flow, daily reminders loop, and version_tracker integration across all cogs
