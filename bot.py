# GBPBot - bot.py
# Version: 1.9.5.1
# Last Updated: 2026-01-18
# Notes:
# - Loads .env via python-dotenv before importing local modules (required when host doesn't inject env vars).
# - Exposes GUILD_ID on the bot instance for cogs that reference bot.GUILD_ID.
# - Adds Forbidden fallback for guild command sync (Missing Access -> global sync).
# - FLAT STRUCTURE: imports/extensions assume all .py files are in the same directory as bot.py
# -----------------------
# CHANGE LOG
# -----------------------
# [2026-01-18] v1.9.5.1 - Flat-structure refactor: switch utils.logger -> logger, and cogs.* extensions -> flat module names.
# [2026-01-18] v1.9.5.0 - Attach self.GUILD_ID to bot instance (fixes CommandsCog "GUILD_ID not found on bot instance").
#                      - Add 403 Forbidden (Missing Access) fallback: if guild sync fails, fall back to global sync.
#                      - Cleaned duplicated changelog header lines.
# [2026-01-18] v1.9.4.0 - Load .env early using python-dotenv so DISCORD_TOKEN/GUILD_ID/LOG_CHANNEL_ID/DB_FILE work on hosts that don't inject ENV.
# [2026-01-18] v1.9.3.0 - Updated env loading for Discloud: supports DISCORD_TOKEN (preferred) and DISCORD_BOT_TOKEN (legacy).
#                      - Added safe parsing/validation for GUILD_ID (no startup crash if missing).
#                      - Improved startup logging when env vars are missing/misconfigured.
# [2025-09-21] v1.9.2.0 - Synced bot.py with updated cogs (onboarding.py v1.9.2.0, reminders.py v1.10.0), version_tracker, and safe_send improvements.
# [2025-09-21] v1.2.4b6 - Updated safe_send, onboarding flow, daily reminders loop, and version_tracker integration across all cogs.
# [2025-09-21] v1.9.0.0 - Synced bot.py with updated cogs, version_tracker, and safe_send improvements.
# [2025-09-20] v1.8.0.0 - Initial integration of reminders.py, onboarding.py, commands.py with daily_loop and safe_send.

import os

# -----------------------
# Load .env EARLY (before importing local modules that read env vars)
# -----------------------
try:
    from dotenv import load_dotenv
    load_dotenv()  # reads .env in the current working directory
except Exception:
    # If python-dotenv isn't installed or .env isn't present, continue safely
    pass

import discord
from discord.ext import commands
import asyncio
import traceback

from db import init_db as db_init
from logger import robust_log
from version_tracker import GBPBot_version, get_file_version

# -----------------------
# Environment Variables
# -----------------------
def _get_env(name: str):
    v = os.getenv(name)
    if v is None:
        return None
    v = v.strip()
    return v if v else None

TOKEN = (
    _get_env("DISCORD_TOKEN")
    or _get_env("DISCORD_BOT_TOKEN")
    or _get_env("TOKEN")
    or _get_env("BOT_TOKEN")
)

GUILD_ID_RAW = _get_env("GUILD_ID")
try:
    GUILD_ID = int(GUILD_ID_RAW) if GUILD_ID_RAW else None
except ValueError:
    GUILD_ID = None

# SAFE debug (prints which keys exist, NOT their values)
print(
    "[BOOT] Env present:",
    "DISCORD_TOKEN" if _get_env("DISCORD_TOKEN") else "-",
    "DISCORD_BOT_TOKEN" if _get_env("DISCORD_BOT_TOKEN") else "-",
    "TOKEN" if _get_env("TOKEN") else "-",
    "BOT_TOKEN" if _get_env("BOT_TOKEN") else "-",
    "GUILD_ID" if _get_env("GUILD_ID") else "-",
    "LOG_CHANNEL_ID" if _get_env("LOG_CHANNEL_ID") else "-",
    "DB_FILE" if _get_env("DB_FILE") else "-"
)

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
        # Expose guild id on the bot instance for cogs that look for bot.GUILD_ID
        self.GUILD_ID = GUILD_ID

    async def setup_hook(self):
        # Report env issues early (but keep logs safe: never print tokens)
        if not TOKEN:
            await robust_log(
                self,
                "[ERROR] Missing Discord token env var. Set DISCORD_TOKEN (preferred) or DISCORD_BOT_TOKEN."
            )

        if not GUILD_ID_RAW:
            await robust_log(
                self,
                "ℹ️ GUILD_ID not set. Will do global command sync (may take longer to appear)."
            )
        elif GUILD_ID is None:
            await robust_log(
                self,
                f"[ERROR] Invalid GUILD_ID value: {GUILD_ID_RAW!r}. Must be a number. Will fall back to global sync."
            )

        # Initialize database
        try:
            await db_init(self)
            await robust_log(self, "✅ Database initialized successfully.")
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self, f"[ERROR] Failed to initialize database\n{tb}")

        # -----------------------
        # Load cogs (FLAT MODULE NAMES)
        # -----------------------
        for ext in ["onboarding", "reminders", "commands"]:
            try:
                await self.load_extension(ext)
                await robust_log(
                    self,
                    f"✅ Loaded cog {ext} | version {get_file_version(ext + '.py')}"
                )
            except Exception:
                tb = traceback.format_exc()
                await robust_log(self, f"[ERROR] Failed to load cog {ext}\n{tb}")

        # -----------------------
        # Sync commands
        # -----------------------
        # Note: If your CommandsCog also syncs in cog_load, you'll see duplicate sync logs.
        try:
            if GUILD_ID:
                guild = discord.Object(id=GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                await robust_log(self, f"✅ Slash commands synced to guild {GUILD_ID}")
            else:
                await self.tree.sync()
                await robust_log(self, "✅ Slash commands synced globally (may take time to appear).")

        except discord.Forbidden:
            # 403 Missing Access: bot not in guild / wrong guild id / permissions issue
            await robust_log(
                self,
                f"[ERROR] Missing access to guild {GUILD_ID}. Falling back to global sync."
            )
            try:
                await self.tree.sync()
                await robust_log(self, "✅ Slash commands synced globally (may take time to appear).")
            except Exception:
                tb = traceback.format_exc()
                await robust_log(self, f"[ERROR] Global sync also failed\n{tb}")

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
    if not TOKEN:
        print("[FATAL] Missing DISCORD_TOKEN (or DISCORD_BOT_TOKEN). Bot cannot start.")
        return

    bot = MyBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
