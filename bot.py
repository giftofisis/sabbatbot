import os
import discord
from discord.ext import commands, tasks
import asyncio
import traceback

from db import init_db  # async DB init
from utils.logger import robust_log  # centralized logger

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
        # ---------------------------
        # 1️⃣ Initialize the database
        # ---------------------------
        try:
            await init_db(self)  # async DB init
            await robust_log(self, "✅ Database initialized successfully.")
        except Exception as e:
            await robust_log(self, "[ERROR] Failed to initialize database", exc=traceback.format_exc())

        # ---------------------------
        # 2️⃣ Load cogs
        # ---------------------------
        for cog in ["cogs.onboarding", "cogs.reminders", "cogs.commands"]:
            try:
                await self.load_extension(cog)
                await robust_log(self, f"✅ Loaded cog {cog}")
            except Exception as e:
                await robust_log(self, f"[ERROR] Failed to load cog {cog}", exc=traceback.format_exc())

        # ---------------------------
        # 3️⃣ Sync slash commands to guild
        # ---------------------------
        try:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            await robust_log(self, f"✅ Slash commands synced to guild {GUILD_ID}")
        except Exception as e:
            await robust_log(self, "[ERROR] Failed to sync slash commands", exc=traceback.format_exc())

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
        await robust_log(self, f"[UNHANDLED COMMAND ERROR] {error}", exc=traceback.format_exc())


# -----------------------
# Async Main
# -----------------------
async def main():
    bot = MyBot()
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
