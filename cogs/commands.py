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

LOG_CHANNEL_ID = 1418171996583366727


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # Safe send helper
    # -----------------------
    async def safe_send(self, user_or_interaction, content=None, embed=None, view=None, ephemeral=True):
        try:
            if isinstance(user_or_interaction, (discord.User, discord.Member)):
                await user_or_interaction.send(content=content, embed=embed, view=view)
            else:
                if hasattr(user_or_interaction.response, "is_done") and not user_or_interaction.response.is_done():
                    await user_or_interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=ephemeral)
                else:
                    await user_or_interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
        except discord.Forbidden:
            await log_error(self.bot, f"[WARN] Could not DM {getattr(user_or_interaction, 'user', user_or_interaction).id}")
        except Exception as e:
            await log_error(self.bot, f"[ERROR] Failed safe_send: {e}")

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


async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
