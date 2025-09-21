# GBPBot - onboarding.py
# Version: 1.9.2.0
# Last Updated: 2025-09-21
# Notes:
# - Fully robust DM onboarding flow with buttons (region, zodiac, reminders).
# - Cancel support included; safe_send ensures no is_finished errors.
# - Emojis pulled from constants.py to keep onboarding & reminders in sync.
# - Syncs with db.py user preferences including 'daily'.
# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-21 15:30 BST] v1.9.2.0 - Updated onboarding to import REGIONS and ZODIAC_SIGNS from constants.py to stay synced with reminders.py
# [2025-09-21 14:00 BST] v1.9.1.0 - Added emojis to all onboarding buttons.
# [2025-09-21 12:00 BST] v1.9.0.0 - Fully integrated safe_send, cancel support, and daily preference handling.

import discord
from discord.ext import commands
from discord import app_commands
from utils.safe_send import safe_send
from db import save_user_preferences
from utils.logger import robust_log, LOG_CHANNEL_ID
from version_tracker import GBPBot_version, get_file_version
from constants import REGIONS, ZODIAC_SIGNS
import traceback

# -----------------------
# Onboarding DM Flow with Buttons
# -----------------------
class OnboardingDM(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.region = None
        self.zodiac = None
        self.subscribe_daily = False

    async def start(self):
        try:
            await safe_send(
                self.user,
                "🚀 Welcome! Let's set up your preferences. Click the buttons to proceed.",
                view=None
            )
            await self.select_region()
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] Onboarding start failed for {self.user.id}\n{tb}")

    async def select_region(self):
        view = discord.ui.View(timeout=None)
        for region, info in REGIONS.items():
            button = discord.ui.Button(label=region, style=discord.ButtonStyle.primary, emoji=info["emoji"])
            async def region_callback(interaction: discord.Interaction, r=region):
                self.region = r
                await safe_send(interaction, f"✅ Region set to **{r}**", ephemeral=True, view=None)
                self.clear_items()
                await self.select_zodiac()
            button.callback = region_callback
            view.add_item(button)

        cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
        async def cancel_callback(interaction: discord.Interaction):
            await self.cancel(interaction)
        cancel_btn.callback = cancel_callback
        view.add_item(cancel_btn)

        await safe_send(self.user, "🌎 Select your **Region**:", view=view)

    async def select_zodiac(self):
        view = discord.ui.View(timeout=None)
        for sign, emoji in ZODIAC_SIGNS.items():
            button = discord.ui.Button(label=sign, style=discord.ButtonStyle.secondary, emoji=emoji)
            async def zodiac_callback(interaction: discord.Interaction, s=sign):
                self.zodiac = s
                await safe_send(interaction, f"✅ Zodiac set to **{s}**", ephemeral=True, view=None)
                self.clear_items()
                await self.ask_subscription()
            button.callback = zodiac_callback
            view.add_item(button)

        cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
        async def cancel_callback(interaction: discord.Interaction):
            await self.cancel(interaction)
        cancel_btn.callback = cancel_callback
        view.add_item(cancel_btn)

        await safe_send(self.user, "🔮 Select your **Zodiac Sign**:", view=view)

    async def ask_subscription(self):
        view = discord.ui.View(timeout=None)

        yes_btn = discord.ui.Button(label="Yes", style=discord.ButtonStyle.success, emoji="✅")
        async def yes_callback(interaction: discord.Interaction):
            self.subscribe_daily = True
            await self.complete_onboarding(interaction)
        yes_btn.callback = yes_callback
        view.add_item(yes_btn)

        no_btn = discord.ui.Button(label="No", style=discord.ButtonStyle.danger, emoji="❌")
        async def no_callback(interaction: discord.Interaction):
            self.subscribe_daily = False
            await self.complete_onboarding(interaction)
        no_btn.callback = no_callback
        view.add_item(no_btn)

        cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="🛑")
        async def cancel_callback(interaction: discord.Interaction):
            await self.cancel(interaction)
        cancel_btn.callback = cancel_callback
        view.add_item(cancel_btn)

        await safe_send(self.user, "📩 Do you want to receive daily reminders?", view=view)

    async def complete_onboarding(self, interaction: discord.Interaction):
        try:
            await save_user_preferences(
                user_id=self.user.id,
                region=self.region,
                zodiac=self.zodiac,
                hour=None,
                days=None,
                daily=self.subscribe_daily,
                subscribed=True,
                bot=self.bot
            )

            await safe_send(interaction, "🎉 Onboarding complete! Your preferences have been saved.", ephemeral=True, view=None)
            self.stop()

            if LOG_CHANNEL_ID:
                channel = self.bot.get_channel(LOG_CHANNEL_ID)
                if not channel:
                    try:
                        channel = await self.bot.fetch_channel(LOG_CHANNEL_ID)
                    except Exception as e:
                        await robust_log(self.bot, f"[ERROR] Failed fetching onboarding log channel\n{e}")
                if channel:
                    await safe_send(
                        channel,
                        f"✅ **{self.user}** ({self.user.id}) completed onboarding.\n"
                        f"Region: **{self.region}** | Zodiac: **{self.zodiac}** | Daily Reminders: **{self.subscribe_daily}**",
                        view=None
                    )

        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] Completing onboarding failed for {self.user.id}\n{tb}")
            await safe_send(interaction, "⚠️ Failed to save preferences. Try again later.", ephemeral=True, view=None)

# -----------------------
# Cog
# -----------------------
class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="onboard")
    async def onboard_prefix(self, ctx):
        try:
            await safe_send(ctx, "📬 Check your DMs! Starting onboarding...")
            await OnboardingDM(self.bot, ctx.author).start()
        except discord.Forbidden:
            await safe_send(ctx, "⚠️ I cannot DM you. Enable DMs from server members.")
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] !onboard failed {ctx.author.id}\n{tb}")
            await safe_send(ctx, "⚠️ Failed to start onboarding.")

    @app_commands.command(name="onboard", description="Start onboarding to set your preferences")
    async def onboard(self, interaction: discord.Interaction):
        try:
            await safe_send(interaction, "📬 Check your DMs! Starting onboarding...", ephemeral=True)
            await OnboardingDM(self.bot, interaction.user).start()
        except discord.Forbidden:
            await safe_send(interaction, "⚠️ I cannot DM you. Enable DMs from server members.", ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] /onboard failed {interaction.user.id}\n{tb}")
            await safe_send(interaction, "⚠️ Failed to start onboarding.", ephemeral=True)

# -----------------------
# Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
    await robust_log(bot, f"✅ OnboardingCog loaded | version {get_file_version('onboarding.py')}")
