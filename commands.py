# GBPBot - commands.py
# Version: 1.9.3.2
# Last Updated: 2026-01-18
# Notes:
# - Flat-structure refactor: imports no longer reference utils/ or cogs/.
# - /profile derives hemisphere from region constants (not DB).
# -----------------------
# CHANGE LOG
# -----------------------
# [2026-01-18] v1.9.3.2
# - Flat-structure imports: safe_send/logger/constants/reminders.
# - /profile: hemisphere derived from region data (constants) instead of prefs.
# [2026-01-18] v1.9.3.1
# - Removed cog_load sync; syncing is centralized in bot.py
# [2026-01-18] v1.9.3.0
# - Added /profile (DM-only) showing region/hemisphere/zodiac/subscription/daily flags (no internal fields).
# - Locked /onboarding_status and /test to administrators (guild-only).
# [2026-01-18] v1.9.2.2
# - Fixed startup failure on Discloud: removed outdated `VERSIONS` import from version_tracker.
# - Updated /version command to use `FILE_VERSIONS` + `get_file_version` consistently.
# - Fixed REGIONS import to use utils.constants (source of truth).
# - Made date formatting portable (removed %-d).
# - Removed duplicate bottom-of-file changelog block (single source at top).
# [2025-09-21] v1.9.0.0 - Updated commands to fully support safe_send, logging, and daily flag from DB.
# [2025-09-20] v1.8.0.0 - Initial slash command setup with /reminder, /submit_quote, /submit_journal, /unsubscribe, /help.

import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from zoneinfo import ZoneInfo

from safe_send import safe_send
from logger import robust_log

from db import (
    get_user_preferences, set_subscription,
    add_quote, add_journal_prompt,
    get_all_quotes, get_all_journal_prompts,
    clear_user_preferences
)

# Source-of-truth constants live here
from constants import REGIONS

# ReminderButtons is defined in reminders.py (flat import)
from reminders import ReminderButtons

# Version tracking
from version_tracker import FILE_VERSIONS, get_file_version


def _format_date(d: datetime.date) -> str:
    """Portable date formatting (avoids %-d issues)."""
    return d.strftime("%d %B %Y").lstrip("0")


def _on_off(value) -> str:
    """Coerce common stored values into a nice On/Off display."""
    if value in (1, True, "1", "true", "True", "on", "On", "enabled", "Enabled", "yes", "Yes"):
        return "✅ On"
    if value in (0, False, "0", "false", "False", "off", "Off", "disabled", "Disabled", "no", "No"):
        return "❌ Off"
    return "—"


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # /profile Command (DM only)
    # -----------------------
    @app_commands.command(name="profile", description="View your settings (DM only).")
    async def profile(self, interaction: discord.Interaction):
        try:
            # DM only
            if interaction.guild is not None:
                await safe_send(interaction, "📩 Please DM me and run `/profile` there (DM-only).", ephemeral=True, bot=self.bot)
                return

            prefs = await get_user_preferences(interaction.user.id) or {}

            region_key = prefs.get("region")
            region_data = REGIONS.get(region_key) if region_key else None

            region_name = region_data.get("name") if region_data else (region_key or "Not set")
            region_emoji = region_data.get("emoji") if region_data else "🌍"
            tz = region_data.get("tz") if region_data else "Not set"
            hemisphere = region_data.get("hemisphere") if region_data else "Not set"

            zodiac = prefs.get("zodiac") or "Not set"
            subscribed = _on_off(prefs.get("subscribed", False))
            daily = _on_off(prefs.get("daily", None))

            embed = discord.Embed(
                title=f"{region_emoji} Your Profile",
                description="Here are your current settings:",
                color=(region_data.get("color") if region_data else 0x9b59b6)
            )

            embed.add_field(name="🌍 Region", value=f"**{region_name}**", inline=True)
            embed.add_field(name="🕰️ Timezone", value=f"**{tz}**", inline=True)
            embed.add_field(name="🧭 Hemisphere", value=f"**{hemisphere}**", inline=True)

            embed.add_field(name="♈ Zodiac", value=f"**{zodiac}**", inline=True)
            embed.add_field(name="📬 Subscription", value=subscribed, inline=True)
            embed.add_field(name="☀️ Daily Messages", value=daily, inline=True)

            embed.set_footer(text="Tip: Use /onboard in DMs to change your settings.")

            await safe_send(interaction, embed=embed, ephemeral=True, bot=self.bot)

        except Exception as e:
            await robust_log(self.bot, "[ERROR] /profile failed", exc=e)
            await safe_send(interaction, "⚠️ Could not load your profile. Try again later.", ephemeral=True, bot=self.bot)

    # -----------------------
    # /reminder Command
    # -----------------------
    @app_commands.command(name="reminder", description="Get an interactive reminder")
    async def reminder(self, interaction: discord.Interaction):
        try:
            prefs = await get_user_preferences(interaction.user.id)
            if not prefs or not prefs.get("subscribed", False):
                await safe_send(interaction, "⚠️ You are not subscribed. Use `/onboard` in DMs to set your preferences.", bot=self.bot)
                return

            region_data = REGIONS.get(prefs.get("region"))
            if not region_data:
                await safe_send(interaction, "⚠️ Region not set. Please complete onboarding.", bot=self.bot)
                return

            tz = region_data["tz"]
            today = datetime.datetime.now(ZoneInfo(tz)).date()

            quotes = await get_all_quotes()
            prompts = await get_all_journal_prompts()

            embed = discord.Embed(
                title=f"{region_data['emoji']} Daily Reminder",
                description=(
                    f"Good morning, {interaction.user.name}! 🌞\n"
                    f"Today is **{_format_date(today)}**\n"
                    f"Region: **{region_data['name']}** | Timezone: **{tz}**\n\n"
                    f"💫 Quote: {random.choice(quotes) if quotes else 'No quotes available.'}\n"
                    f"📝 Journal Prompt: {random.choice(prompts) if prompts else 'No prompts available.'}"
                ),
                color=region_data.get("color", 0x2F3136)
            )
            await safe_send(interaction, embed=embed, view=ReminderButtons(region_data), bot=self.bot)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /reminder command failed", exc=e)
            await safe_send(interaction, "⚠️ Could not send your reminder. Try again later.", bot=self.bot)

    # -----------------------
    # /submit_quote Command
    # -----------------------
    @app_commands.command(name="submit_quote", description="Submit an inspirational quote")
    @app_commands.describe(quote="The quote text to submit")
    async def submit_quote(self, interaction: discord.Interaction, quote: str):
        try:
            await add_quote(quote, bot=self.bot)
            await safe_send(interaction, "✅ Quote submitted successfully.", bot=self.bot)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /submit_quote failed", exc=e)
            await safe_send(interaction, "⚠️ Could not submit quote. Try again later.", bot=self.bot)

    # -----------------------
    # /submit_journal Command
    # -----------------------
    @app_commands.command(name="submit_journal", description="Submit a journal prompt")
    @app_commands.describe(prompt="The journal prompt text to submit")
    async def submit_journal(self, interaction: discord.Interaction, prompt: str):
        try:
            await add_journal_prompt(prompt, bot=self.bot)
            await safe_send(interaction, "✅ Journal prompt submitted successfully.", bot=self.bot)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /submit_journal failed", exc=e)
            await safe_send(interaction, "⚠️ Could not submit journal prompt. Try again later.", bot=self.bot)

    # -----------------------
    # /unsubscribe Command
    # -----------------------
    @app_commands.command(name="unsubscribe", description="Stop receiving daily reminders")
    async def unsubscribe(self, interaction: discord.Interaction):
        try:
            await set_subscription(interaction.user.id, False, bot=self.bot)
            await safe_send(interaction, "❌ You have unsubscribed from daily reminders.", bot=self.bot)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /unsubscribe failed", exc=e)
            await safe_send(interaction, "⚠️ Could not update subscription. Try again later.", bot=self.bot)

    # -----------------------
    # /help Command
    # -----------------------
    @app_commands.command(name="help", description="Shows all available commands")
    async def help_command(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title="🌙 Bot Help", color=0x9b59b6)
            embed.add_field(name="/reminder", value="Receive your daily interactive reminder immediately.", inline=False)
            embed.add_field(name="/submit_quote <text>", value="Submit an inspirational quote for reminders.", inline=False)
            embed.add_field(name="/submit_journal <text>", value="Submit a journal prompt for daily reminders.", inline=False)
            embed.add_field(name="/unsubscribe", value="Stop receiving daily DM reminders.", inline=False)
            embed.add_field(name="/profile", value="View your user-facing settings (DM only).", inline=False)
            embed.add_field(name="/onboarding_status", value="(Admin) Check which members have completed onboarding.", inline=False)
            embed.add_field(name="/clear_onboarding", value="Clear your onboarding status to start again.", inline=False)
            embed.add_field(name="/version", value="Show the bot's current version.", inline=False)
            embed.add_field(name="/test", value="(Admin) Test if the bot is responsive.", inline=False)
            embed.set_footer(text="Use `/onboard` in DMs to start your onboarding process.")

            await safe_send(interaction.user, embed=embed, bot=self.bot)
            await safe_send(interaction, "✅ Help sent to your DMs.", bot=self.bot)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /help command failed", exc=e)
            await safe_send(interaction, "⚠️ Could not send help. Try again later.", bot=self.bot)

    # -----------------------
    # /onboarding_status Command (ADMIN ONLY)
    # -----------------------
    @app_commands.command(name="onboarding_status", description="(Admin) Check which members have completed onboarding")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def onboarding_status(self, interaction: discord.Interaction):
        try:
            onboarded = []
            not_onboarded = []

            if not interaction.guild:
                await safe_send(interaction, "⚠️ This command can only be used in a server.", ephemeral=True, bot=self.bot)
                return

            for member in interaction.guild.members:
                if member.bot:
                    continue
                prefs = await get_user_preferences(member.id)
                if prefs:
                    onboarded.append(member.name)
                else:
                    not_onboarded.append(member.name)

            embed = discord.Embed(title="📝 Onboarding Status", color=0x3498db)
            embed.add_field(name="✅ Completed Onboarding", value="\n".join(onboarded) or "None", inline=False)
            embed.add_field(name="❌ Not Completed", value="\n".join(not_onboarded) or "None", inline=False)
            await safe_send(interaction, embed=embed, ephemeral=True, bot=self.bot)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /onboarding_status failed", exc=e)
            await safe_send(interaction, "⚠️ Could not fetch onboarding status. Try again later.", ephemeral=True, bot=self.bot)

    # -----------------------
    # /clear_onboarding Command
    # -----------------------
    @app_commands.command(name="clear_onboarding", description="Clear your onboarding status")
    async def clear_onboarding(self, interaction: discord.Interaction):
        try:
            await clear_user_preferences(interaction.user.id, bot=self.bot)
            await safe_send(interaction, "❌ Your onboarding status has been cleared. You can start `/onboard` again.", bot=self.bot)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /clear_onboarding failed", exc=e)
            await safe_send(interaction, "⚠️ Could not clear onboarding status. Try again later.", bot=self.bot)

    # -----------------------
    # /version Command
    # -----------------------
    @app_commands.command(name="version", description="Show the bot's current version")
    async def version(self, interaction: discord.Interaction):
        try:
            bot_core_version = FILE_VERSIONS.get("bot.py", "unknown")
            commands_version = get_file_version("commands.py") or FILE_VERSIONS.get("commands.py", "unknown")

            embed = discord.Embed(title="🤖 GBPBot Version Info", color=0x9b59b6)
            embed.add_field(name="Bot Core Version", value=f"**{bot_core_version}**", inline=False)
            embed.add_field(name="Commands Cog Version", value=f"**{commands_version}**", inline=False)

            files_list = "\n".join(f"{f}: {v}" for f, v in FILE_VERSIONS.items())
            embed.add_field(name="All Tracked Files", value=files_list or "No files tracked.", inline=False)

            await safe_send(interaction, embed=embed, ephemeral=True, bot=self.bot)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /version command failed", exc=e)
            await safe_send(interaction, "⚠️ Could not fetch version info.", ephemeral=True, bot=self.bot)

    # -----------------------
    # /test Command (ADMIN ONLY)
    # -----------------------
    @app_commands.command(name="test", description="(Admin) Test if the bot is working")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def test(self, interaction: discord.Interaction):
        try:
            await safe_send(interaction, "✅ Test successful! Bot is responsive.", ephemeral=True, bot=self.bot)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /test command failed", exc=e)


# -----------------------
# Cog Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
    await robust_log(bot, f"✅ CommandsCog loaded | version {get_file_version('commands.py')}")
