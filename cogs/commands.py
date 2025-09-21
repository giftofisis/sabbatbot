# GBPBot - commands.py
# Version: 1.9.0.0
# Last Updated: 2025-09-21
# Notes:
# - Slash commands fully use safe_send and robust logging.
# - Compatible with updated db.py user preferences including 'daily'.
# - /onboard command removed from this cog (only in onboarding.py).
# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-21] v1.9.0.0 - Updated commands to fully support safe_send, logging, and daily flag from DB.
# [2025-09-20] v1.8.0.0 - Initial slash command setup with /reminder, /submit_quote, /submit_journal, /unsubscribe, /help.

import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from zoneinfo import ZoneInfo
from utils.safe_send import safe_send

from db import (
    get_user_preferences, set_subscription,
    add_quote, add_journal_prompt,
    get_all_quotes, get_all_journal_prompts,
    clear_user_preferences
)
from cogs.reminders import REGIONS, ReminderButtons
from utils.logger import robust_log
from version_tracker import GBPBot_version, get_file_version

from version_tracker import VERSIONS as FILE_VERSIONS

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # Sync commands on load
    # -----------------------
    async def cog_load(self):
        try:
            guild_id = getattr(self.bot, "GUILD_ID", None)
            if guild_id is None:
                await robust_log(self.bot, "[WARN] GUILD_ID not found; syncing globally.")
                synced = await self.bot.tree.sync()
                await robust_log(self.bot, f"[INFO] Globally synced {len(synced)} commands.")
            else:
                guild = discord.Object(id=guild_id)
                synced = await self.bot.tree.sync(guild=guild)
                await robust_log(self.bot, f"[INFO] Synced {len(synced)} commands to guild {guild_id}")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] Failed to sync commands\n{e}")

    # -----------------------
    # /reminder Command
    # -----------------------
    @app_commands.command(name="reminder", description="Get an interactive reminder")
    async def reminder(self, interaction: discord.Interaction):
        try:
            prefs = await get_user_preferences(interaction.user.id)
            if not prefs or not prefs.get("subscribed", False):
                await safe_send(interaction, "⚠️ You are not subscribed. Use `/onboard` in DMs to set your preferences.")
                return

            region_data = REGIONS.get(prefs.get("region"))
            if not region_data:
                await safe_send(interaction, "⚠️ Region not set. Please complete onboarding.")
                return

            tz = region_data["tz"]
            today = datetime.datetime.now(ZoneInfo(tz)).date()
            embed = discord.Embed(
                title=f"{region_data['emoji']} Daily Reminder",
                description=(
                    f"Good morning, {interaction.user.name}! 🌞\n"
                    f"Today is **{today.strftime('%-d %B %Y')}**\n"
                    f"Region: **{region_data['name']}** | Timezone: **{tz}**\n\n"
                    f"💫 Quote: {random.choice(await get_all_quotes())}\n"
                    f"📝 Journal Prompt: {random.choice(await get_all_journal_prompts())}"
                ),
                color=region_data["color"]
            )
            await safe_send(interaction, embed=embed, view=ReminderButtons(region_data))
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /reminder command failed\n{e}")
            await safe_send(interaction, "⚠️ Could not send your reminder. Try again later.")

    # -----------------------
    # /submit_quote Command
    # -----------------------
    @app_commands.command(name="submit_quote", description="Submit an inspirational quote")
    @app_commands.describe(quote="The quote text to submit")
    async def submit_quote(self, interaction: discord.Interaction, quote: str):
        try:
            await add_quote(quote, bot=self.bot)
            await safe_send(interaction, "✅ Quote submitted successfully.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /submit_quote failed\n{e}")
            await safe_send(interaction, "⚠️ Could not submit quote. Try again later.")

    # -----------------------
    # /submit_journal Command
    # -----------------------
    @app_commands.command(name="submit_journal", description="Submit a journal prompt")
    @app_commands.describe(prompt="The journal prompt text to submit")
    async def submit_journal(self, interaction: discord.Interaction, prompt: str):
        try:
            await add_journal_prompt(prompt, bot=self.bot)
            await safe_send(interaction, "✅ Journal prompt submitted successfully.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /submit_journal failed\n{e}")
            await safe_send(interaction, "⚠️ Could not submit journal prompt. Try again later.")

    # -----------------------
    # /unsubscribe Command
    # -----------------------
    @app_commands.command(name="unsubscribe", description="Stop receiving daily reminders")
    async def unsubscribe(self, interaction: discord.Interaction):
        try:
            await set_subscription(interaction.user.id, False, bot=self.bot)
            await safe_send(interaction, "❌ You have unsubscribed from daily reminders.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /unsubscribe failed\n{e}")
            await safe_send(interaction, "⚠️ Could not update subscription. Try again later.")

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
            embed.add_field(name="/onboarding_status", value="Check which members have completed onboarding.", inline=False)
            embed.add_field(name="/clear_onboarding", value="Clear your onboarding status to start again.", inline=False)
            embed.add_field(name="/version", value="Show the bot's current version.", inline=False)
            embed.add_field(name="/test", value="Test if the bot is responsive.", inline=False)
            embed.set_footer(text="Use `/onboard` in DMs to start your onboarding process.")
            await safe_send(interaction.user, embed=embed)
            await safe_send(interaction, "✅ Help sent to your DMs.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /help command failed\n{e}")
            await safe_send(interaction, "⚠️ Could not send help. Try again later.")

    # -----------------------
    # /onboarding_status Command
    # -----------------------
    @app_commands.command(name="onboarding_status", description="Check which members have completed onboarding")
    async def onboarding_status(self, interaction: discord.Interaction):
        try:
            onboarded = []
            not_onboarded = []
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
            await safe_send(interaction, embed=embed)
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /onboarding_status failed\n{e}")
            await safe_send(interaction, "⚠️ Could not fetch onboarding status. Try again later.")

    # -----------------------
    # /clear_onboarding Command
    # -----------------------
    @app_commands.command(name="clear_onboarding", description="Clear your onboarding status")
    async def clear_onboarding(self, interaction: discord.Interaction):
        try:
            await clear_user_preferences(interaction.user.id, bot=self.bot)
            await safe_send(interaction, "❌ Your onboarding status has been cleared. You can start `/onboard` again.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /clear_onboarding failed\n{e}")
            await safe_send(interaction, "⚠️ Could not clear onboarding status. Try again later.")

    # -----------------------
    # /version Command
    # -----------------------
    from version_tracker import VERSIONS, get_file_version

    @app_commands.command(name="version", description="Show the bot's current version")
    async def version(self, interaction: discord.Interaction):
        try:
            # Bot core version from version_tracker.py
            bot_version = VERSIONS.get("bot.py", "unknown")
            
            # Individual file version example: commands.py
            commands_version = get_file_version("commands.py") or "unknown"

            # Build a neat response
            embed = discord.Embed(
                title="🤖 GBPBot Version Info",
                color=0x9b59b6
            )
            embed.add_field(name="Bot Core Version", value=f"**{bot_version}**", inline=False)
            embed.add_field(name="Commands Cog Version", value=f"**{commands_version}**", inline=False)
            
            # Optional: add all tracked files
            files_list = "\n".join(f"{f}: {v}" for f, v in VERSIONS.items())
            embed.add_field(name="All Tracked Files", value=files_list, inline=False)
# GBPBot - commands.py
# Version: 1.9.1.0
# Last Updated: 2025-09-21
# Notes:
# - Slash commands fully use safe_send and robust logging.
# - Compatible with updated db.py user preferences including 'daily'.
# - /onboard command removed from this cog (only in onboarding.py).
# - /version command updated to be robust with version_tracker.py
# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-21] v1.9.1.0 - Updated /version command to safely display bot and commands versions using version_tracker.py
# [2025-09-21] v1.9.0.0 - Updated commands to fully support safe_send, logging, and daily flag from DB.
# [2025-09-20] v1.8.0.0 - Initial slash command setup with /reminder, /submit_quote, /submit_journal, /unsubscribe, /help.

import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from zoneinfo import ZoneInfo
from utils.safe_send import safe_send

from db import (
    get_user_preferences, set_subscription,
    add_quote, add_journal_prompt,
    get_all_quotes, get_all_journal_prompts,
    clear_user_preferences
)
from cogs.reminders import REGIONS, ReminderButtons
from utils.logger import robust_log
from version_tracker import get_file_version, VERSIONS

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # Sync commands on load
    # -----------------------
    async def cog_load(self):
        try:
            guild_id = getattr(self.bot, "GUILD_ID", None)
            if guild_id is None:
                await robust_log(self.bot, "[WARN] GUILD_ID not found; syncing globally.")
                synced = await self.bot.tree.sync()
                await robust_log(self.bot, f"[INFO] Globally synced {len(synced)} commands.")
            else:
                guild = discord.Object(id=guild_id)
                synced = await self.bot.tree.sync(guild=guild)
                await robust_log(self.bot, f"[INFO] Synced {len(synced)} commands to guild {guild_id}")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] Failed to sync commands\n{e}")

    # -----------------------
    # /reminder Command
    # -----------------------
    @app_commands.command(name="reminder", description="Get an interactive reminder")
    async def reminder(self, interaction: discord.Interaction):
        try:
            prefs = await get_user_preferences(interaction.user.id)
            if not prefs or not prefs.get("subscribed", False):
                await safe_send(interaction, "⚠️ You are not subscribed. Use `/onboard` in DMs to set your preferences.")
                return

            region_data = REGIONS.get(prefs.get("region"))
            if not region_data:
                await safe_send(interaction, "⚠️ Region not set. Please complete onboarding.")
                return

            tz = region_data["tz"]
            today = datetime.datetime.now(ZoneInfo(tz)).date()
            embed = discord.Embed(
                title=f"{region_data['emoji']} Daily Reminder",
                description=(
                    f"Good morning, {interaction.user.name}! 🌞\n"
                    f"Today is **{today.strftime('%-d %B %Y')}**\n"
                    f"Region: **{region_data['name']}** | Timezone: **{tz}**\n\n"
                    f"💫 Quote: {random.choice(await get_all_quotes())}\n"
                    f"📝 Journal Prompt: {random.choice(await get_all_journal_prompts())}"
                ),
                color=region_data["color"]
            )
            await safe_send(interaction, embed=embed, view=ReminderButtons(region_data))
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /reminder command failed\n{e}")
            await safe_send(interaction, "⚠️ Could not send your reminder. Try again later.")

    # -----------------------
    # /submit_quote Command
    # -----------------------
    @app_commands.command(name="submit_quote", description="Submit an inspirational quote")
    @app_commands.describe(quote="The quote text to submit")
    async def submit_quote(self, interaction: discord.Interaction, quote: str):
        try:
            await add_quote(quote, bot=self.bot)
            await safe_send(interaction, "✅ Quote submitted successfully.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /submit_quote failed\n{e}")
            await safe_send(interaction, "⚠️ Could not submit quote. Try again later.")

    # -----------------------
    # /submit_journal Command
    # -----------------------
    @app_commands.command(name="submit_journal", description="Submit a journal prompt")
    @app_commands.describe(prompt="The journal prompt text to submit")
    async def submit_journal(self, interaction: discord.Interaction, prompt: str):
        try:
            await add_journal_prompt(prompt, bot=self.bot)
            await safe_send(interaction, "✅ Journal prompt submitted successfully.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /submit_journal failed\n{e}")
            await safe_send(interaction, "⚠️ Could not submit journal prompt. Try again later.")

    # -----------------------
    # /unsubscribe Command
    # -----------------------
    @app_commands.command(name="unsubscribe", description="Stop receiving daily reminders")
    async def unsubscribe(self, interaction: discord.Interaction):
        try:
            await set_subscription(interaction.user.id, False, bot=self.bot)
            await safe_send(interaction, "❌ You have unsubscribed from daily reminders.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /unsubscribe failed\n{e}")
            await safe_send(interaction, "⚠️ Could not update subscription. Try again later.")

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
            embed.add_field(name="/onboarding_status", value="Check which members have completed onboarding.", inline=False)
            embed.add_field(name="/clear_onboarding", value="Clear your onboarding status to start again.", inline=False)
            embed.add_field(name="/version", value="Show the bot's current version.", inline=False)
            embed.add_field(name="/test", value="Test if the bot is responsive.", inline=False)
            embed.set_footer(text="Use `/onboard` in DMs to start your onboarding process.")
            await safe_send(interaction.user, embed=embed)
            await safe_send(interaction, "✅ Help sent to your DMs.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /help command failed\n{e}")
            await safe_send(interaction, "⚠️ Could not send help. Try again later.")

    # -----------------------
    # /onboarding_status Command
    # -----------------------
    @app_commands.command(name="onboarding_status", description="Check which members have completed onboarding")
    async def onboarding_status(self, interaction: discord.Interaction):
        try:
            onboarded = []
            not_onboarded = []
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
            await safe_send(interaction, embed=embed)
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /onboarding_status failed\n{e}")
            await safe_send(interaction, "⚠️ Could not fetch onboarding status. Try again later.")

    # -----------------------
    # /clear_onboarding Command
    # -----------------------
    @app_commands.command(name="clear_onboarding", description="Clear your onboarding status")
    async def clear_onboarding(self, interaction: discord.Interaction):
        try:
            await clear_user_preferences(interaction.user.id, bot=self.bot)
            await safe_send(interaction, "❌ Your onboarding status has been cleared. You can start `/onboard` again.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /clear_onboarding failed\n{e}")
            await safe_send(interaction, "⚠️ Could not clear onboarding status. Try again later.")

    # -----------------------
    # /version Command
    # -----------------------
    @app_commands.command(name="version", description="Show the bot's current version")
    async def version(self, interaction: discord.Interaction):
        try:
            bot_version = FILE_VERSIONS.get("bot.py", "unknown")
            commands_version = get_file_version("commands.py") or "unknown"

            embed = discord.Embed(
                title="🤖 GBPBot Version Info",
                color=0x9b59b6
            )
            embed.add_field(name="Bot Core Version", value=f"**{bot_version}**", inline=False)
            embed.add_field(name="Commands Cog Version", value=f"**{commands_version}**", inline=False)

            # All tracked files
            files_list = "\n".join(f"{f}: {v}" for f, v in FILE_VERSIONS.items())
            embed.add_field(name="All Tracked Files", value=files_list, inline=False)

            await safe_send(interaction, embed=embed)
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /version command failed\n{e}")
            await safe_send(interaction, "⚠️ Could not fetch version info.")

    # -----------------------
    # /test Command
    # -----------------------
    @app_commands.command(name="test", description="Test if the bot is working")
    async def test(self, interaction: discord.Interaction):
        try:
            await safe_send(interaction, "✅
mmand to reference DM onboarding
