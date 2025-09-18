import discord
from discord.ext import commands
from discord import app_commands
import traceback
from db import save_user_preferences, get_user_preferences
from utils.logger import robust_log

# -----------------------
# Regions & Zodiac Options
# -----------------------
REGIONS = ["North America", "South America", "Europe", "Africa", "Oceania & Asia"]
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# -----------------------
# Onboarding View
# -----------------------
class OnboardingView(discord.ui.View):
    def __init__(self, user_id, bot):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.bot = bot
        self.selected_region = None
        self.selected_zodiac = None

    # -----------------------
    # Cancel Button
    # -----------------------
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction, button):
        try:
            await interaction.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
            self.stop()
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] Onboarding cancel failed for user {self.user_id}\n{tb}")

    # -----------------------
    # Region Buttons
    # -----------------------
    @discord.ui.select(
        placeholder="Select your region",
        min_values=1,
        max_values=1,
        options=[discord.SelectOption(label=r) for r in REGIONS]
    )
    async def select_region(self, interaction, select):
        try:
            await interaction.response.defer(ephemeral=True)
            self.selected_region = select.values[0]
            await save_user_preferences(self.user_id, region=self.selected_region, bot=self.bot)
            await interaction.followup.send(f"✅ Region set to **{self.selected_region}**. Please select your Zodiac sign.", ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] Selecting region failed for user {self.user_id}\n{tb}")
            await interaction.followup.send("⚠️ Failed to save region.", ephemeral=True)

    # -----------------------
    # Zodiac Buttons
    # -----------------------
    @discord.ui.select(
        placeholder="Select your zodiac",
        min_values=1,
        max_values=1,
        options=[discord.SelectOption(label=z) for z in ZODIAC_SIGNS]
    )
    async def select_zodiac(self, interaction, select):
        try:
            await interaction.response.defer(ephemeral=True)
            self.selected_zodiac = select.values[0]
            await save_user_preferences(self.user_id, zodiac=self.selected_zodiac, bot=self.bot)
            await interaction.followup.send(f"✅ Zodiac set to **{self.selected_zodiac}**. Onboarding complete!", ephemeral=True)
            self.stop()
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] Selecting zodiac failed for user {self.user_id}\n{tb}")
            await interaction.followup.send("⚠️ Failed to save zodiac.", ephemeral=True)


# -----------------------
# Onboarding Cog
# -----------------------
class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # /onboard Command
    # -----------------------
    @app_commands.command(name="onboard", description="Start the onboarding process")
    async def onboard(self, interaction):
        user_id = interaction.user.id
        try:
            await interaction.response.send_message("🚀 Starting onboarding...", ephemeral=True)
            view = OnboardingView(user_id, self.bot)
            await interaction.followup.send("Please select your region:", view=view, ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] /onboard command failed for user {user_id}\n{tb}")
            await interaction.followup.send("⚠️ Failed to start onboarding.", ephemeral=True)


# -----------------------
# Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
