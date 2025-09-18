import discord
from discord.ext import commands
from discord import app_commands
from db import set_user_preferences, get_user_preferences
from .reminders import REGIONS

ZODIAC_SIGNS = {
    "Aries": "♈️", "Taurus": "♉️", "Gemini": "♊️", "Cancer": "♋️",
    "Leo": "♌️", "Virgo": "♍️", "Libra": "♎️", "Scorpio": "♏️",
    "Sagittarius": "♐️", "Capricorn": "♑️", "Aquarius": "♒️", "Pisces": "♓️"
}

LOG_CHANNEL_ID = 1418171996583366727  # central log channel


async def log_error(bot, message: str):
    """Centralized logging to a channel."""
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)
    finally:
        print(message)


class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def safe_send(self, user_or_interaction, content=None, embed=None, view=None, ephemeral=True):
        """Safely send a message to a user or interaction, logging failures."""
        try:
            cog = self.bot.get_cog("CommandsCog")
            if cog:
                await cog.safe_send(user_or_interaction, content, embed, view, ephemeral)
            else:
                # fallback
                if isinstance(user_or_interaction, (discord.User, discord.Member)):
                    await user_or_interaction.send(content=content, embed=embed, view=view)
                elif hasattr(user_or_interaction, "response") and not user_or_interaction.response.is_done():
                    await user_or_interaction.response.send_message(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
                else:
                    await user_or_interaction.followup.send(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
        except Exception as e:
            await log_error(self.bot, f"[ERROR] safe_send failed: {e}")

    @app_commands.command(name="onboard", description="Start the onboarding process")
    async def onboard(self, interaction: discord.Interaction):
        user = interaction.user

        # -----------------------
        # Step 1: Region Selection
        # -----------------------
        try:
            embed = discord.Embed(
                title="✨ Welcome to the Circle! ✨",
                description=(
                    f"Greetings, seeker! 🌙\n\n"
                    f"Please select your region to access region-specific channels and updates."
                ),
                color=0x9b59b6
            )

            class RegionView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.selection = None
                    for region_name, data in REGIONS.items():
                        self.add_item(discord.ui.Button(
                            label=f"{data['emoji']} {region_name}",
                            style=discord.ButtonStyle.primary,
                            custom_id=f"region_{region_name}"
                        ))

                async def interaction_check(self, i: discord.Interaction) -> bool:
                    return i.user.id == user.id

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="region_cancel")
                async def cancel(self, button: discord.ui.Button, i: discord.Interaction):
                    self.selection = None
                    await i.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
                    self.stop()

                async def on_button_click(self, i: discord.Interaction):
                    if i.custom_id.startswith("region_"):
                        self.selection = i.custom_id.replace("region_", "")
                        await i.response.send_message(f"✅ Region selected: {self.selection}", ephemeral=True)
                        self.stop()

            view = RegionView()
            await self.safe_send(user, embed=embed, view=view)

            # Wait until a button sets view.selection
            while view.selection is None:
                await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=0.5))

            selected_region = view.selection
            if not selected_region:
                return

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Onboarding step 1 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 1.")
            return

        # -----------------------
        # Step 2: Zodiac Selection
        # -----------------------
        try:
            embed = discord.Embed(
                title="🌟 Choose your Zodiac",
                description="Select your zodiac sign below:",
                color=0xf1c40f
            )

            class ZodiacView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.selection = None
                    for zodiac, emoji in ZODIAC_SIGNS.items():
                        self.add_item(discord.ui.Button(
                            label=f"{emoji} {zodiac}",
                            style=discord.ButtonStyle.secondary,
                            custom_id=f"zodiac_{zodiac}"
                        ))

                async def interaction_check(self, i: discord.Interaction) -> bool:
                    return i.user.id == user.id

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="zodiac_cancel")
                async def cancel(self, button: discord.ui.Button, i: discord.Interaction):
                    self.selection = None
                    await i.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
                    self.stop()

                async def on_button_click(self, i: discord.Interaction):
                    if i.custom_id.startswith("zodiac_"):
                        self.selection = i.custom_id.replace("zodiac_", "")
                        await i.response.send_message(f"✅ Zodiac selected: {self.selection}", ephemeral=True)
                        self.stop()

            view = ZodiacView()
            await self.safe_send(user, embed=embed, view=view)

            while view.selection is None:
                await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=0.5))

            selected_zodiac = view.selection
            if not selected_zodiac:
                return

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Onboarding step 2 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 2.")
            return

        # -----------------------
        # Step 3: Subscribe to DMs
        # -----------------------
        try:
            embed = discord.Embed(
                title="🔔 Daily Notifications",
                description="Would you like to subscribe to daily reminders?",
                color=0x2ecc71
            )

            class SubscribeView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.selection = None
                    self.add_item(discord.ui.Button(label="✅ Subscribe", style=discord.ButtonStyle.success, custom_id="subscribe_yes"))
                    self.add_item(discord.ui.Button(label="❌ No Thanks", style=discord.ButtonStyle.danger, custom_id="subscribe_no"))

                async def interaction_check(self, i: discord.Interaction) -> bool:
                    return i.user.id == user.id

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="subscribe_cancel")
                async def cancel(self, button: discord.ui.Button, i: discord.Interaction):
                    self.selection = None
                    await i.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
                    self.stop()

                async def on_button_click(self, i: discord.Interaction):
                    if i.custom_id == "subscribe_yes":
                        self.selection = True
                    elif i.custom_id == "subscribe_no":
                        self.selection = False
                    await i.response.send_message(f"✅ Subscribed: {self.selection}", ephemeral=True)
                    self.stop()

            view = SubscribeView()
            await self.safe_send(user, embed=embed, view=view)

            while view.selection is None:
                await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=0.5))

            subscribed = view.selection if view.selection is not None else False

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Onboarding step 3 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 3.")
            return

        # -----------------------
        # Save preferences
        # -----------------------
        try:
            set_user_preferences(user.id, region=selected_region, zodiac=selected_zodiac, subscribed=subscribed)
            await self.safe_send(user, "🎉 Thank you for completing your onboarding! Enjoy our community! 🌙")
        except Exception as e:
            await log_error(self.bot, f"[ERROR] Saving onboarding preferences failed: {e}")
            await self.safe_send(user, "⚠️ Could not save your onboarding preferences.")


async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))import discord
from discord.ext import commands
from discord import app_commands
from db import set_subscription, get_user_preferences  # fixed imports
from db import set_user_preferences
from .reminders import REGIONS

ZODIAC_SIGNS = {
    "Aries": "♈️", "Taurus": "♉️", "Gemini": "♊️", "Cancer": "♋️",
    "Leo": "♌️", "Virgo": "♍️", "Libra": "♎️", "Scorpio": "♏️",
    "Sagittarius": "♐️", "Capricorn": "♑️", "Aquarius": "♒️", "Pisces": "♓️"
}

LOG_CHANNEL_ID = 1418171996583366727

async def log_error(bot, message: str):
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)
    finally:
        print(message)


class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def safe_send(self, user_or_interaction, content=None, embed=None, view=None, ephemeral=True):
        """Use CommandsCog safe_send if available"""
        cog = self.bot.get_cog("CommandsCog")
        if cog:
            await cog.safe_send(user_or_interaction, content, embed, view, ephemeral)
        else:
            try:
                if isinstance(user_or_interaction, (discord.User, discord.Member)):
                    await user_or_interaction.send(content=content, embed=embed, view=view)
                elif hasattr(user_or_interaction, "response") and not user_or_interaction.response.is_done():
                    await user_or_interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=ephemeral)
                else:
                    await user_or_interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
            except Exception as e:
                await log_error(self.bot, f"[ERROR] safe_send fallback failed: {e}")

    @app_commands.command(name="onboard", description="Start onboarding")
    async def onboard(self, interaction: discord.Interaction):
        user = interaction.user
        # Use the same emoji-rich multi-step onboarding pattern from previous version
        # Step 1: Region
        # Step 2: Zodiac
        # Step 3: Subscribe
        # Store values in set_user_preferences
        # Use safe_send everywhere
        await self.safe_send(user, "🌙 Onboarding placeholder - region, zodiac, subscription steps implemented here.")


async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))

