# GBPBot - commands.py
# Version: 1.1.0 build 2
# Last Updated: 2025-09-20T13:15:00+01:00 (BST)
# Notes: All slash commands and helper commands updated with safe_send, robust logging, and file version tracking
#        Fully integrated safe_send fix for NoneType is_finished errors.

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
from cogs.onboarding import OnboardingDM
from utils.logger import robust_log
from version_tracker import GBPBot_version, get_file_version

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
                await safe_send(interaction, "⚠️ You are not subscribed. Use `/onboard` to set your preferences.")
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
            embed.add_field(name="/onboard", value="Start onboarding to select region, zodiac, and reminders.", inline=False)
            embed.add_field(name="/reminder", value="Receive your daily interactive reminder immediately.", inline=False)
            embed.add_field(name="/submit_quote <text>", value="Submit an inspirational quote for reminders.", inline=False)
            embed.add_field(name="/submit_journal <text>", value="Submit a journal prompt for daily reminders.", inline=False)
            embed.add_field(name="/unsubscribe", value="Stop receiving daily DM reminders.", inline=False)
            embed.add_field(name="/onboarding_status", value="Check which members have completed onboarding.", inline=False)
            embed.add_field(name="/clear_onboarding", value="Clear your onboarding status to start again.", inline=False)
            embed.add_field(name="/version", value="Show the bot's current version.", inline=False)
            embed.add_field(name="/test", value="Test if the bot is responsive.", inline=False)
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
            version_str = f"{GBPBot_version['major']}.{GBPBot_version['minor']}.{GBPBot_version['patch']}.{GBPBot_version['build']}"
            file_ver = get_file_version("commands.py")
            await safe_send(interaction, f"🤖 Bot Version: **{version_str}**\n📄 commands.py Version: **{file_ver}**")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /version command failed\n{e}")

    # -----------------------
    # /test Command
    # -----------------------
    @app_commands.command(name="test", description="Test if the bot is working")
    async def test(self, interaction: discord.Interaction):
        try:
            await safe_send(interaction, "✅ Test successful! Bot is responsive.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /test command failed\n{e}")


# -----------------------
# Cog Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(CommandsCog(bot))


# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-20 13:10 BST] v1.1.0b1 - Added safe_send to all commands, robust logging, and file version display for /version
# [2025-09-20 13:15 BST] v1.1.0b2 - Fully integrated robust safe_send fix for NoneType is_finished errors in all commands
