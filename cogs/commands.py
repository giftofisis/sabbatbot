import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from zoneinfo import ZoneInfo

from .db import (
    get_user_preferences, set_subscription,
    add_quote, add_journal_prompt,
    get_all_quotes, get_all_journal_prompts,
    clear_user_preferences
)
from .reminders import REGIONS, ReminderButtons
from .onboarding import OnboardingDM
from ..utils.logger import robust_log  # adjust path if utils is at root

# -----------------------
# Bot Version
# -----------------------
BOT_VERSION = "1.2.3.4"

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
                return

            guild = discord.Object(id=guild_id)
            for cmd in [
                self.onboard, self.reminder, self.submit_quote, self.submit_journal,
                self.unsubscribe, self.help_command, self.onboarding_status,
                self.clear_onboarding, self.test, self.version
            ]:
                self.bot.tree.add_command(cmd, guild=guild)

            synced = await self.bot.tree.sync(guild=guild)
            await robust_log(self.bot, f"[INFO] Synced {len(synced)} commands to guild {guild_id}")

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
            await robust_log(self.bot, "[ERROR] Failed safe_send", e)

    # -----------------------
    # /onboard Command
    # -----------------------
    @app_commands.command(name="onboard", description="Start onboarding")
    async def onboard(self, interaction: discord.Interaction):
        try:
            await self.safe_send(interaction, "📬 Check your DMs! Starting onboarding...")
            onboarding = OnboardingDM(self.bot, interaction.user)
            await onboarding.start()
        except discord.Forbidden:
            await self.safe_send(interaction, "⚠️ I couldn't DM you. Please enable DMs from server members.")
        except Exception as e:
            await robust_log(self.bot, f"[ERROR] /onboard failed for {interaction.user.id}", e)
            await self.safe_send(interaction, "⚠️ Failed to start onboarding.")

    # -----------------------
    # /reminder Command
    # -----------------------
    @app_commands.command(name="reminder", description="Get an interactive reminder")
    async def reminder(self, interaction: discord.Interaction):
        try:
            prefs = await get_user_preferences(interaction.user.id)
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
                    f"💫 Quote: {random.choice(await get_all_quotes())}\n"
                    f"📝 Journal Prompt: {random.choice(await get_all_journal_prompts())}"
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
            await add_quote(quote, bot=self.bot)
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
            await add_journal_prompt(prompt, bot=self.bot)
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
            await set_subscription(interaction.user.id, False, bot=self.bot)
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
            embed.add_field(name="/submit_quote <text>", value="Submit an inspirational quote for reminders.", inline=False)
            embed.add_field(name="/submit_journal <text>", value="Submit a journal prompt for daily reminders.", inline=False)
            embed.add_field(name="/unsubscribe", value="Stop receiving daily DM reminders.", inline=False)
            embed.add_field(name="/onboarding_status", value="Check which members have completed onboarding.", inline=False)
            embed.add_field(name="/clear_onboarding", value="Clear your onboarding status to start again.", inline=False)
            embed.add_field(name="/version", value="Show the bot's current version.", inline=False)
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
                prefs = await get_user_preferences(member.id)
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
            await clear_user_preferences(interaction.user.id, bot=self.bot)
            await self.safe_send(interaction, "❌ Your onboarding status has been cleared. You can start `/onboard` again.")
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /clear_onboarding failed", e)
            await self.safe_send(interaction, "⚠️ Could not clear onboarding status. Try again later.")

    # -----------------------
    # /version Command
    # -----------------------
    @app_commands.command(name="version", description="Show the bot's current version")
    async def version(self, interaction: discord.Interaction):
        try:
            await self.safe_send(interaction, f"🤖 Bot Version: **{BOT_VERSION}**")
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /version command failed", e)

    # -----------------------
    # /test Command
    # -----------------------
    @app_commands.command(name="test", description="Test if the bot is working")
    async def test(self, interaction: discord.Interaction):
        try:
            await self.safe_send(interaction, "✅ Test successful! Bot is responsive.")
        except Exception as e:
            await robust_log(self.bot, "[ERROR] /test command failed", e)


# -----------------------
# Cog Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
