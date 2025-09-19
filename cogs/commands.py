import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from zoneinfo import ZoneInfo

from db import (
    get_user_preferences, set_subscription,
    add_quote, add_journal_prompt,
    get_all_quotes, get_all_journal_prompts,
    clear_user_preferences
)
from .reminders import REGIONS, ReminderButtons
from utils.logger import robust_log


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Sync app commands when cog loads
    async def cog_load(self):
        try:
            guild_id = getattr(self.bot, "GUILD_ID", None)
            if guild_id is None:
                await robust_log(self.bot, "[WARN] GUILD_ID not found on bot; syncing globally.")
                synced = await self.bot.tree.sync()
                await robust_log(self.bot, f"[INFO] Globally synced {len(synced)} commands: {[c.name for c in synced]}")
                return

            guild = discord.Object(id=guild_id)

            # Add all commands explicitly to the guild
            self.bot.tree.add_command(self.reminder, guild=guild)
            self.bot.tree.add_command(self.submit_quote, guild=guild)
            self.bot.tree.add_command(self.submit_journal, guild=guild)
            self.bot.tree.add_command(self.unsubscribe, guild=guild)
            self.bot.tree.add_command(self.help_command, guild=guild)
            self.bot.tree.add_command(self.onboarding_status, guild=guild)
            self.bot.tree.add_command(self.clear_onboarding, guild=guild)
            self.bot.tree.add_command(self.test, guild=guild)

            # Sync commands to the guild
            synced = await self.bot.tree.sync(guild=guild)
            await robust_log(
                self.bot,
                f"[INFO] Synced {len(synced)} commands to guild {guild_id}: {[c.name for c in synced]}"
            )

            # Check if some commands are missing
            if not synced:
                await robust_log(self.bot, f"[WARN] No commands were synced to guild {guild_id}.")
            else:
                expected = [
                    "reminder", "submit_quote", "submit_journal",
                    "unsubscribe", "help", "onboarding_status",
                    "clear_onboarding", "test"
                ]
                missing = [cmd for cmd in expected if cmd not in [c.name for c in synced]]
                if missing:
                    await robust_log(self.bot, f"[WARN] Missing commands after sync: {missing}")

        except Exception as e:
            await robust_log(self.bot, "[ERROR] Failed to sync commands", e)

    # -----------------------
    # Safe send helper
    # -----------------------
    async def safe_send(self, user_or_interaction, content=None, embed=None, view=None, ephemeral=True):
        try:
            if isinstance(user_or_interaction, (discord.User, discord.Member)):
                await user_or_interaction.send(content=content, embed=embed, view=view)
            elif hasattr(user_or_interaction, "response") and not user_or_interaction.response.is_done():
                await user_or_interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=ephemeral)
            else:
                await user_or_interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
        except discord.Forbidden:
            await robust_log(self.bot, f"[WARN] Could not DM {getattr(user_or_interaction, 'user', user_or_interaction).id}")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] Failed safe_send", e)

    # -----------------------
    # /reminder Command
    # -----------------------
    @app_commands.command(name="reminder", description="Get an interactive reminder")
    async def reminder(self, interaction: discord.Interaction):
        try:
            prefs = get_user_preferences(interaction.user.id)
            if not prefs or not prefs.get("subscribed", False):
                await self.safe_send(interaction, "⚠️ You are not subscribed. Use `/onboard` to set your preferences.")
                return

            region_data = REGIONS.get(prefs.get("region"))
            if not region_data:
                await self.safe_send(interaction, "⚠️ Region not set. Please complete onboarding.")
                return

            tz = region_data["tz"]
            today = datetime.datetime.now(ZoneInfo(tz)).date()
            embed = discord.Embed(
                title=f"{region_data['emoji']} Daily Reminder",
                description=(
                    f"Good morning, {interaction.user.name}! 🌞\n"
                    f"Today is **{today.strftime('%-d %B %Y')}**\n"
                    f"Region: **{region_data['name']}** | Timezone: **{tz}**\n\n"
                    f"💫 Quote: {random.choice(get_all_quotes())}\n"
                    f"📝 Journal Prompt: {random.choice(get_all_journal_prompts())}"
                ),
                color=region_data["color"]
            )
            await self.safe_send(interaction, embed=embed, view=ReminderButtons(region_data))
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /reminder command failed", e)
            await self.safe_send(interaction, "⚠️ Could not send your reminder. Try again later.")

    # -----------------------
    # /submit_quote Command
    # -----------------------
    @app_commands.command(name="submit_quote", description="Submit an inspirational quote")
    @app_commands.describe(quote="The quote text to submit")
    async def submit_quote(self, interaction: discord.Interaction, quote: str):
        try:
            add_quote(quote)
            await self.safe_send(interaction, "✅ Quote submitted successfully.")
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /submit_quote failed", e)
            await self.safe_send(interaction, "⚠️ Could not submit quote. Try again later.")

    # -----------------------
    # /submit_journal Command
    # -----------------------
    @app_commands.command(name="submit_journal", description="Submit a journal prompt")
    @app_commands.describe(prompt="The journal prompt text to submit")
    async def submit_journal(self, interaction: discord.Interaction, prompt: str):
        try:
            add_journal_prompt(prompt)
            await self.safe_send(interaction, "✅ Journal prompt submitted successfully.")
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /submit_journal failed", e)
            await self.safe_send(interaction, "⚠️ Could not submit journal prompt. Try again later.")

    # -----------------------
    # /unsubscribe Command
    # -----------------------
    @app_commands.command(name="unsubscribe", description="Stop receiving daily reminders")
    async def unsubscribe(self, interaction: discord.Interaction):
        try:
            set_subscription(interaction.user.id, False)
            await self.safe_send(interaction, "❌ You have unsubscribed from daily reminders.")
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /unsubscribe failed", e)
            await self.safe_send(interaction, "⚠️ Could not update subscription. Try again later.")

    # -----------------------
    # /help Command
    # -----------------------
    @app_commands.command(name="help", description="Shows all available commands")
    async def help_command(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title="🌙 Bot Help", color=0x9b59b6)
            embed.add_field(name="/onboard", value="Start onboarding to select region, zodiac, and reminders.", inline=False)
            embed.add_field(name="/reminder", value="Receive your daily interactive reminder immediately.", inline=False)
            embed.add_field(name="/status", value="Show bot status, next Sabbat, full moon, and user counts.", inline=False)
            embed.add_field(name="/submit_quote <text>", value="Submit an inspirational quote for reminders.", inline=False)
            embed.add_field(name="/submit_journal <text>", value="Submit a journal prompt for daily reminders.", inline=False)
            embed.add_field(name="/unsubscribe", value="Stop receiving daily DM reminders.", inline=False)
            embed.add_field(name="/onboarding_status", value="Check which members have completed onboarding.", inline=False)
            embed.add_field(name="/clear_onboarding", value="Clear your onboarding status to start again.", inline=False)
            embed.add_field(name="/test", value="Test if the bot is responsive.", inline=False)
            await self.safe_send(interaction.user, embed=embed)
            await self.safe_send(interaction, "✅ Help sent to your DMs.")
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /help command failed", e)
            await self.safe_send(interaction, "⚠️ Could not send help. Try again later.")

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
                prefs = get_user_preferences(member.id)
                if prefs:
                    onboarded.append(member.name)
                else:
                    not_onboarded.append(member.name)

            embed = discord.Embed(title="📝 Onboarding Status", color=0x3498db)
            embed.add_field(name="✅ Completed Onboarding", value="\n".join(onboarded) or "None", inline=False)
            embed.add_field(name="❌ Not Completed", value="\n".join(not_onboarded) or "None", inline=False)
            await self.safe_send(interaction, embed=embed)
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /onboarding_status failed", e)
            await self.safe_send(interaction, "⚠️ Could not fetch onboarding status. Try again later.")

    # -----------------------
    # /clear_onboarding Command
    # -----------------------
    @app_commands.command(name="clear_onboarding", description="Clear your onboarding status")
    async def clear_onboarding(self, interaction: discord.Interaction):
        try:
            clear_user_preferences(interaction.user.id)
            await self.safe_send(interaction, "❌ Your onboarding status has been cleared. You can start `/onboard` again.")
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /clear_onboarding failed", e)
            await self.safe_send(interaction, "⚠️ Could not clear onboarding status. Try again later.")

    # -----------------------
    # /test Command
    # -----------------------
    @app_commands.command(name="test", description="Test if the bot is working")
    async def test(self, interaction: discord.Interaction):
        try:
            await self.safe_send(interaction, "✅ Test successful! Bot is responsive.")
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /test command failed", e)


async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
