# GBPBot - onboarding.py
# Version: 1.0.0 build 1
# Last Updated: 2025-09-20
# Notes: Multi-step DM onboarding with safe_send, cancel support, robust logging

import discord
from discord.ext import commands
from discord import app_commands
from utils.safe_send import safe_send
from db import save_user_preferences
from utils.logger import robust_log
from version_tracker import GBPBot_version, file_versions, get_file_version  # version tracker
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
class OnboardingDM:
    def __init__(self, bot, user):
        self.bot = bot
        self.user = user
        self.region = None
        self.zodiac = None
        self.subscribe_daily = False

    async def start(self):
        try:
            dm = self.user.dm_channel or await self.user.create_dm()
            await safe_send(dm, "🚀 Welcome! Let's set up your preferences. Click the buttons to proceed.")

            await self.select_region(dm)
            await self.select_zodiac(dm)
            await self.ask_subscription(dm)

            await save_user_preferences(
                self.user.id,
                region=self.region,
                zodiac=self.zodiac,
                daily=self.subscribe_daily,
                bot=self.bot
            )
            await safe_send(dm, "🎉 Onboarding complete! Your preferences have been saved.")

        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] Onboarding failed for {self.user.id}\n{tb}")

    # -----------------------
    # Step 1: Select Region
    # -----------------------
    async def select_region(self, dm):
        view = discord.ui.View(timeout=None)
        for region in REGIONS:
            async def region_callback(interaction, r=region):
                self.region = r
                await safe_send(interaction, f"✅ Region set to **{r}**", ephemeral=True)
                view.stop()
            view.add_item(discord.ui.Button(label=region, style=discord.ButtonStyle.primary, custom_id=f"region_{region}"))
            button = view.children[-1]
            button.callback = region_callback
        await safe_send(dm, "Select your **Region**:", view=view)
        await view.wait()

    # -----------------------
    # Step 2: Select Zodiac
    # -----------------------
    async def select_zodiac(self, dm):
        view = discord.ui.View(timeout=None)
        for sign in ZODIAC_SIGNS:
            async def zodiac_callback(interaction, s=sign):
                self.zodiac = s
                await safe_send(interaction, f"✅ Zodiac set to **{s}**", ephemeral=True)
                view.stop()
            view.add_item(discord.ui.Button(label=sign, style=discord.ButtonStyle.secondary, custom_id=f"zodiac_{sign}"))
            button = view.children[-1]
            button.callback = zodiac_callback
        await safe_send(dm, "Select your **Zodiac Sign**:", view=view)
        await view.wait()

    # -----------------------
    # Step 3: Daily Reminder Subscription
    # -----------------------
    async def ask_subscription(self, dm):
        view = discord.ui.View(timeout=None)
        async def yes_callback(interaction):
            self.subscribe_daily = True
            await safe_send(interaction, "✅ You will receive daily reminders.", ephemeral=True)
            view.stop()
        async def no_callback(interaction):
            self.subscribe_daily = False
            await safe_send(interaction, "❌ You will not receive daily reminders.", ephemeral=True)
            view.stop()
        view.add_item(discord.ui.Button(label="Yes", style=discord.ButtonStyle.success, custom_id="daily_yes", callback=yes_callback))
        view.add_item(discord.ui.Button(label="No", style=discord.ButtonStyle.danger, custom_id="daily_no", callback=no_callback))
        await safe_send(dm, "Do you want to receive daily reminders?", view=view)
        await view.wait()

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
# [2025-09-20 12:45] v1.0.0b1 - Added version_tracker import, version comment, and change tracking
# [2025-09-20 12:46] Rewritten onboarding flow with interactive buttons:
#             Region → Zodiac → Daily reminders subscription.
#             Uses safe_send for all messages. Daily subscription now recorded in DB
# [2025-09-20 12:54] v1.0.1b1 - Updated safe_send import for v1.0.1b4 compatibility
# [2025-09-20 12:55] v1.0.1b2 - Confirmed callbacks correctly set for Discord buttons with view.stop()
