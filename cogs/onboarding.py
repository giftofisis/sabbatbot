import discord
from discord.ext import commands
from discord import app_commands
from db import set_user_preferences
from .reminders import REGIONS
from utils.logger import robust_log  # <- centralized logger import

ZODIAC_SIGNS = {
    "Aries": "♈️", "Taurus": "♉️", "Gemini": "♊️", "Cancer": "♋️",
    "Leo": "♌️", "Virgo": "♍️", "Libra": "♎️", "Scorpio": "♏️",
    "Sagittarius": "♐️", "Capricorn": "♑️", "Aquarius": "♒️", "Pisces": "♓️"
}


class OnboardingCog(commands.Cog):
    """Full onboarding with DM buttons, SQLite saving, and robust logging."""

    def __init__(self, bot):
        self.bot = bot

    async def safe_dm(self, user: discord.User, content=None, embed=None, view=None):
        """Send a DM safely with exception handling."""
        try:
            await user.send(content=content, embed=embed, view=view)
        except discord.Forbidden:
            await robust_log(self.bot, f"Cannot DM user {user.id}")
        except Exception as e:
            await robust_log(self.bot, f"Failed to send DM to user {user.id}", e)

    async def log_step(self, user_id, step, detail=None):
        """Log user step to log channel."""
        msg = f"User {user_id} - {step}"
        if detail:
            msg += f": {detail}"
        await robust_log(self.bot, msg)

    @app_commands.command(name="onboard", description="Start the onboarding process")
    async def onboard(self, interaction: discord.Interaction):
        user = interaction.user

        try:
            await interaction.response.defer(ephemeral=True)
            await self.log_step(user.id, "Started onboarding")

            selected_region = await self.region_step(user)
            selected_zodiac = await self.zodiac_step(user)
            subscribed = await self.subscribe_step(user)

            try:
                set_user_preferences(user.id, region=selected_region, zodiac=selected_zodiac, subscribed=subscribed)
                await self.safe_dm(user, f"🎉 Onboarding complete! Welcome, {user.name} 🌙")
                await interaction.followup.send("✅ Onboarding complete! Check your DMs.", ephemeral=True)
                await self.log_step(user.id, "Onboarding complete", f"Region: {selected_region}, Zodiac: {selected_zodiac}, Subscribed: {subscribed}")
            except Exception as e:
                await self.safe_dm(user, "⚠️ Could not save preferences.")
                await interaction.followup.send("⚠️ Onboarding failed at final step.", ephemeral=True)
                await robust_log(self.bot, f"Failed to save preferences for user {user.id}", e)

        except Exception as e:
            await interaction.followup.send("⚠️ Onboarding failed unexpectedly. Please try again.", ephemeral=True)
            await robust_log(self.bot, f"Unexpected onboarding error for user {user.id}", e)

    # ---------------- Step functions ---------------- #

    async def region_step(self, user):
        embed = discord.Embed(title="✨ Welcome to GBPBot! ✨",
                              description="Select your **region** below:",
                              color=0x9b59b6)

        view = discord.ui.View(timeout=None)
        selected = {"region": None}

        async def make_callback(region_name):
            async def callback(interaction: discord.Interaction):
                selected["region"] = region_name
                await interaction.response.send_message(f"✅ Selected region: {region_name}", ephemeral=True)
                await robust_log(self.bot, f"User {interaction.user.id} selected region: {region_name}")
                view.stop()
            return callback

        for region_name, data in REGIONS.items():
            button = discord.ui.Button(label=f"{data['emoji']} {region_name}", style=discord.ButtonStyle.primary)
            button.callback = await make_callback(region_name)
            view.add_item(button)

        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
        async def cancel_callback(interaction: discord.Interaction):
            await interaction.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
            await robust_log(self.bot, f"User {interaction.user.id} cancelled onboarding at Region step")
            view.stop()
        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)

        await self.safe_dm(user, embed=embed, view=view)
        await view.wait()
        return selected["region"] or list(REGIONS.keys())[0]

    async def zodiac_step(self, user):
        embed = discord.Embed(title="🌟 Choose your Zodiac",
                              description="Select your zodiac sign:",
                              color=0xf1c40f)

        view = discord.ui.View(timeout=None)
        selected = {"zodiac": None}

        async def make_callback(zodiac):
            async def callback(interaction: discord.Interaction):
                selected["zodiac"] = zodiac
                await interaction.response.send_message(f"✅ Selected zodiac: {zodiac}", ephemeral=True)
                await robust_log(self.bot, f"User {interaction.user.id} selected zodiac: {zodiac}")
                view.stop()
            return callback

        for zodiac, emoji in ZODIAC_SIGNS.items():
            button = discord.ui.Button(label=f"{emoji} {zodiac}", style=discord.ButtonStyle.secondary)
            button.callback = await make_callback(zodiac)
            view.add_item(button)

        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
        async def cancel_callback(interaction: discord.Interaction):
            await interaction.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
            await robust_log(self.bot, f"User {interaction.user.id} cancelled onboarding at Zodiac step")
            view.stop()
        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)

        await self.safe_dm(user, embed=embed, view=view)
        await view.wait()
        return selected["zodiac"] or list(ZODIAC_SIGNS.keys())[0]

    async def subscribe_step(self, user):
        embed = discord.Embed(title="🔔 Daily Notifications",
                              description="Subscribe to daily DM reminders?",
                              color=0x2ecc71)

        view = discord.ui.View(timeout=None)
        selected = {"subscribed": True}

        async def subscribe_callback(interaction: discord.Interaction, subscribed: bool):
            selected["subscribed"] = subscribed
            msg = "✅ Subscribed to daily reminders!" if subscribed else "❌ You opted out of daily reminders."
            await interaction.response.send_message(msg, ephemeral=True)
            await robust_log(self.bot, f"User {interaction.user.id} subscription choice: {subscribed}")
            view.stop()

        yes_button = discord.ui.Button(label="✅ Subscribe", style=discord.ButtonStyle.success)
        yes_button.callback = lambda inter: subscribe_callback(inter, True)
        no_button = discord.ui.Button(label="❌ No Thanks", style=discord.ButtonStyle.danger)
        no_button.callback = lambda inter: subscribe_callback(inter, False)

        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        async def cancel_callback(interaction: discord.Interaction):
            await interaction.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
            await robust_log(self.bot, f"User {interaction.user.id} cancelled onboarding at Subscribe step")
            view.stop()
        cancel_button.callback = cancel_callback

        view.add_item(yes_button)
        view.add_item(no_button)
        view.add_item(cancel_button)

        await self.safe_dm(user, embed=embed, view=view)
        await view.wait()
        return selected["subscribed"]


# ---------------- Setup ---------------- #

async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
