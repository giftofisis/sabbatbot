import discord
from discord import app_commands
from discord.ext import commands
import traceback
import random

from db import (
    get_user_preferences,
    set_subscription,
    add_quote,
    add_journal_prompt,
    get_all_quotes,
    get_all_journal_prompts
)
from utils.logger import robust_log

# -----------------------
# Commands Cog
# -----------------------
class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # /onboarding_status
    # -----------------------
    @app_commands.command(
        name="onboarding_status",
        description="Check which members have completed onboarding"
    )
    async def onboarding_status(self, interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            # Example: fetch some data from DB, here we just mock
            await interaction.followup.send("✅ Onboarding status fetched.", ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] /onboarding_status failed\n{tb}")
            await interaction.followup.send("⚠️ Failed to fetch onboarding status.", ephemeral=True)

    # -----------------------
    # /reminder
    # -----------------------
    @app_commands.command(name="reminder", description="Manage your daily reminder settings")
    async def reminder(self, interaction):
        try:
            await interaction.response.send_message("📌 Reminder settings here.", ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] /reminder failed\n{tb}")
            await interaction.followup.send("⚠️ Failed to access reminder settings.", ephemeral=True)

    # -----------------------
    # /submit_quote
    # -----------------------
    @app_commands.command(name="submit_quote", description="Submit a new inspirational quote")
    async def submit_quote(self, interaction, quote: str):
        try:
            await add_quote(quote, bot=self.bot)
            await interaction.response.send_message("💫 Quote submitted successfully!", ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] /submit_quote failed\n{tb}")
            await interaction.response.send_message("⚠️ Failed to submit quote.", ephemeral=True)

    # -----------------------
    # /submit_journal
    # -----------------------
    @app_commands.command(name="submit_journal", description="Submit a new journal prompt")
    async def submit_journal(self, interaction, prompt: str):
        try:
            await add_journal_prompt(prompt, bot=self.bot)
            await interaction.response.send_message("📝 Journal prompt submitted successfully!", ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] /submit_journal failed\n{tb}")
            await interaction.response.send_message("⚠️ Failed to submit journal prompt.", ephemeral=True)

    # -----------------------
    # /unsubscribe
    # -----------------------
    @app_commands.command(name="unsubscribe", description="Unsubscribe from daily reminders")
    async def unsubscribe(self, interaction):
        try:
            user_id = interaction.user.id
            await set_subscription(user_id, False, bot=self.bot)
            await interaction.response.send_message("✅ You have been unsubscribed from daily reminders.", ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] /unsubscribe failed\n{tb}")
            await interaction.response.send_message("⚠️ Failed to unsubscribe.", ephemeral=True)

    # -----------------------
    # /help
    # -----------------------
    @app_commands.command(name="help", description="Get help and available commands")
    async def help(self, interaction):
        try:
            help_text = (
                "📜 **Available Commands:**\n"
                "/onboarding_status - Check onboarding status\n"
                "/reminder - Manage your daily reminders\n"
                "/submit_quote - Submit a new quote\n"
                "/submit_journal - Submit a new journal prompt\n"
                "/unsubscribe - Unsubscribe from reminders\n"
                "/help - Show this help message"
            )
            await interaction.response.send_message(help_text, ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] /help failed\n{tb}")
            await interaction.response.send_message("⚠️ Failed to display help.", ephemeral=True)

    # -----------------------
    # /clear_onboarding Command
    # -----------------------
    @app_commands.command(name="clear_onboarding", description="Clear your onboarding status")
    async def clear_onboarding(self, interaction: discord.Interaction):
        try:
            from db import clear_user_preferences  # import here to avoid circular issues
            clear_user_preferences(interaction.user.id)
            await self.safe_send(interaction, "❌ Your onboarding status has been cleared. You can start `/onboard` again.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /clear_onboarding failed", e)
            await self.safe_send(interaction, "⚠️ Could not clear onboarding status. Try again later.")

# -----------------------
# Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
