# GBPBot - onboarding.py
# Version: 1.0.2 build 4
# Last Updated: 2025-09-20
# Notes: Fully robust DM onboarding with safe_send, cancel support, modern button callbacks, fixed view is_finished bug
#        Now logs onboarding completion to central LOG_CHANNEL_ID

import discord
from discord.ext import commands
from discord import app_commands
from utils.safe_send import safe_send
from db import save_user_preferences
from utils.logger import robust_log, LOG_CHANNEL_ID
from version_tracker import GBPBot_version, get_file_version
import traceback

# -----------------------
# Onboarding Config
# -----------------------
REGIONS = ["North America", "South America", "Europe", "Africa", "Oceania & Asia"]
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

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
            await safe_send(self.user, "🚀 Welcome! Let's set up your preferences. Click the buttons to proceed.", view=None)
            await self.select_region()
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] Onboarding start failed for {self.user.id}\n{tb}")

    async def select_region(self):
        view = discord.ui.View(timeout=None)
        for region in REGIONS:
            button = discord.ui.Button(label=region, style=discord.ButtonStyle.primary)
            async def region_callback(interaction: discord.Interaction, r=region):
                self.region = r
                await safe_send(interaction, f"✅ Region set to **{r}**", ephemeral=True, view=None)
                self.clear_items()
                await self.select_zodiac()
            button.callback = region_callback
            view.add_item(button)

        cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
        async def cancel_callback(interaction: discord.Interaction):
            await self.cancel(interaction)
        cancel_btn.callback = cancel_callback
        view.add_item(cancel_btn)

        await safe_send(self.user, "🌎 Select your **Region**:", view=view)

    async def select_zodiac(self):
        view = discord.ui.View(timeout=None)
        for sign in ZODIAC_SIGNS:
            button = discord.ui.Button(label=sign, style=discord.ButtonStyle.secondary)
            async def zodiac_callback(interaction: discord.Interaction, s=sign):
                self.zodiac = s
                await safe_send(interaction, f"✅ Zodiac set to **{s}**", ephemeral=True, view=None)
                self.clear_items()
                await self.ask_subscription()
            button.callback = zodiac_callback
            view.add_item(button)

        cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
        async def cancel_callback(interaction: discord.Interaction):
            await self.cancel(interaction)
        cancel_btn.callback = cancel_callback
        view.add_item(cancel_btn)

        await safe_send(self.user, "🔮 Select your **Zodiac Sign**:", view=view)

    async def ask_subscription(self):
        view = discord.ui.View(timeout=None)

        yes_btn = discord.ui.Button(label="Yes", style=discord.ButtonStyle.success)
        async def yes_callback(interaction: discord.Interaction):
            self.subscribe_daily = True
            await self.complete_onboarding(interaction)
        yes_btn.callback = yes_callback
        view.add_item(yes_btn)

        no_btn = discord.ui.Button(label="No", style=discord.ButtonStyle.danger)
        async def no_callback(interaction: discord.Interaction):
            self.subscribe_daily = False
            await self.complete_onboarding(interaction)
        no_btn.callback = no_callback
        view.add_item(no_btn)

        cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        async def cancel_callback(interaction: discord.Interaction):
            await self.cancel(interaction)
        cancel_btn.callback = cancel_callback
        view.add_item(cancel_btn)

        await safe_send(self.user, "📩 Do you want to receive daily reminders?", view=view)

    async def complete_onboarding(self, interaction: discord.Interaction):
        try:
            # Save preferences to DB
            await save_user_preferences(
                user_id=self.user.id,
                region=self.region,
                zodiac=self.zodiac,
                hour=None,               # default value; will preserve existing or DB default
                days=None,               # default value; will preserve existing or DB default
                daily=self.subscribe_daily,
                subscribed=True,
                bot=self.bot
            )

            # Confirm to user
            await safe_send(interaction, "🎉 Onboarding complete! Your preferences have been saved.", ephemeral=True, view=None)
            self.stop()

            # Log completion to central LOG_CHANNEL_ID
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

# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-20 13:50] v1.0.2b1 - Updated to modern button callbacks and robust safe_send for NoneType is_finished fix
# [2025-09-20 13:55] v1.0.2b2 - Added cancel support for all steps and centralized logging
# [2025-09-20 14:10] v1.0.2b3 - Fixed cancel buttons to be async callbacks to prevent TypeError
# [2025-09-20 14:25] v1.0.2b4 - Added logging of completed onboardings to central LOG_CHANNEL_ID
