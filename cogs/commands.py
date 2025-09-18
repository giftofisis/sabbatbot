import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from zoneinfo import ZoneInfo

from db import (
    get_user_preferences, set_subscription,
    add_quote, add_journal_prompt,
    get_all_quotes, get_all_journal_prompts
)
from .reminders import REGIONS, ReminderButtons, get_sabbat_dates, next_full_moon_for_tz
from .onboarding import log_error  # centralized logging

LOG_CHANNEL_ID = 1418171996583366727  # central error log channel


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # Safe send helper
    # -----------------------
    async def safe_send(self, user_or_interaction, content=None, embed=None, view=None, ephemeral=True):
        """Safely send a message to a user or interaction, logging failures."""
        try:
            if isinstance(user_or_interaction, (discord.User, discord.Member)):
                await user_or_interaction.send(content=content, embed=embed, view=view)
            else:
                # interaction
                if not user_or_interaction.response.is_done():
                    await user_or_interaction.response.send_message(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
                else:
                    await user_or_interaction.followup.send(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
        except discord.Forbidden:
            await log_error(
                self.bot,
                f"[WARN] Could not DM {getattr(user_or_interaction, 'user', user_or_interaction).id}"
            )
        except Exception as e:
            await log_error(self.bot, f"[ERROR] Failed safe_send: {e}")

    # -----------------------
    # /reminder Command
    # -----------------------
    @app_commands.command(name="reminder", description="Get an interactive reminder")
    async def reminder(self, interaction: discord.Interaction):
        try:
            prefs = get_user_preferences(interaction.user.id)
            if not prefs or not prefs["subscribed"]:
                await self.safe_send(interaction, "⚠️ You are not subscribed. Use `/onboard` to set your preferences.")
                return

            region_data = REGIONS.get(prefs["region"])
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
            await log_error(self.bot, f"[ERROR] /reminder command failed: {e}")
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
            await log_error(self.bot, f"[ERROR] /submit_quote failed: {e}")
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
            await log_error(self.bot, f"[ERROR] /submit_journal failed: {e}")
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
            await log_error(self.bot, f"[ERROR] /unsubscribe failed: {e}")
            await self.safe_send(interaction, "⚠️ Could not update subscription. Try again later.")

    # -----------------------
    # /status Command
    # -----------------------
    @app_commands.command(name="status", description="Shows bot status and upcoming events")
    async def status(self, interaction: discord.Interaction):
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            embed = discord.Embed(title="🌙 Bot Status", color=0x1abc9c)
            embed.add_field(name="Current UTC Time", value=now.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)

            guild = interaction.guild
            for region_name, data in REGIONS.items():
                tz = ZoneInfo(data["tz"])
                today = datetime.datetime.now(tz).date()
                sabbats = get_sabbat_dates(today.year)
                upcoming_sabbat = min((d for d in sabbats.values() if d >= today), default=None)
                next_moon = next_full_moon_for_tz(data["tz"])
                users_count = sum(1 for member in guild.members if any(role.id == data["role_id"] for role in member.roles))
                embed.add_field(
                    name=f"{data['emoji']} {region_name} ({data['tz']})",
                    value=(
                        f"Next Sabbat: {upcoming_sabbat.strftime('%-d %B %Y') if upcoming_sabbat else 'N/A'}\n"
                        f"Next Full Moon: {next_moon.strftime('%-d %B %Y')}\n"
                        f"Users in region: {users_count}"
                    ),
                    inline=False
                )

            await self.safe_send(interaction, embed=embed)
        except Exception as e:
            await log_error(self.bot, f"[ERROR] /status command failed: {e}")
            await self.safe_send(interaction, "⚠️ Could not fetch status. Try again later.")

    # -----------------------
    # /onboarding_status Command
    # -----------------------
    @app_commands.command(name="onboarding_status", description="Shows which members have completed onboarding")
    async def onboarding_status(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            if not guild:
                await self.safe_send(interaction, "⚠️ Could not access the guild.")
                return

            completed = []
            incomplete = []

            for member in guild.members:
                prefs = get_user_preferences(member.id)
                if prefs and prefs["region"] and prefs["zodiac"]:
                    completed.append(member.mention)
                else:
                    incomplete.append(member.mention)

            embed = discord.Embed(title="🌙 Onboarding Status", color=0x1abc9c)
            embed.add_field(
                name="✅ Completed Onboarding",
                value="\n".join(completed) if completed else "None",
                inline=False
            )
            embed.add_field(
                name="❌ Incomplete Onboarding",
                value="\n".join(incomplete) if incomplete else "None",
                inline=False
            )

            await self.safe_send(interaction, embed=embed)
        except Exception as e:
            await log_error(self.bot, f"[ERROR] /onboarding_status failed: {e}")
            await self.safe_send(interaction, "⚠️ Could not fetch onboarding status. Try again later.")

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
            await self.safe_send(interaction.user, embed=embed)
            await self.safe_send(interaction, "✅ Help sent to your DMs.")
        except Exception as e:
            await log_error(self.bot, f"[ERROR] /help command failed: {e}")
            await self.safe_send(interaction, "⚠️ Could not send help. Try again later.")

    # -----------------------
    # /test Command
    # -----------------------
    @app_commands.command(name="test", description="Test your daily reminder and list all commands")
    async def test_command(self, interaction: discord.Interaction):
        try:
            prefs = get_user_preferences(interaction.user.id)
            if not prefs:
                await self.safe_send(interaction, "⚠️ You need to complete onboarding first.")
                return

            cog = self.bot.get_cog("RemindersCog")
            if cog:
                await cog.send_daily_reminder(interaction.user.id, prefs)

            commands_list = [cmd.name for cmd in self.bot.tree.walk_commands()]
            await self.safe_send(interaction, f"✅ All commands are available: {', '.join(commands_list)}")
        except Exception as e:
            await log_error(self.bot, f"[ERROR] /test command failed: {e}")
            await self.safe_send(interaction, "⚠️ Test command failed. Try again later.")

# -----------------------
# Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
