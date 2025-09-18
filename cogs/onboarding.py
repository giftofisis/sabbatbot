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

LOG_CHANNEL_ID = 1418171996583366727

async def log_error(bot, message: str):
    """Centralized logging to a channel and console."""
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
                    await user_or_interaction.response.send_message(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
                else:
                    await user_or_interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
            except Exception as e:
                await log_error(self.bot, f"[ERROR] safe_send fallback failed: {e}")

    @app_commands.command(name="onboard", description="Start the onboarding process")
    async def onboard(self, interaction: discord.Interaction):
        user = interaction.user

        # -----------------------
        # Step 1: Select Region
        # -----------------------
        try:
            embed = discord.Embed(
                title="✨ Welcome to GBPBot! ✨",
                description="Please select your **region** below to access region-specific channels and reminders.",
                color=0x9b59b6
            )

            class RegionSelect(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.selected_region = None

                    for region_name, data in REGIONS.items():
                        self.add_item(discord.ui.Button(
                            label=f"{data['emoji']} {region_name}",
                            style=discord.ButtonStyle.primary,
                            custom_id=f"region_{region_name}"
                        ))

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="region_cancel")
                async def cancel(self, button: discord.ui.Button, interaction_: discord.Interaction):
                    await self.safe_send(interaction_, "❌ Onboarding cancelled.")
                    self.stop()

                async def interaction_check(self, interaction_: discord.Interaction) -> bool:
                    return interaction_.user.id == user.id

                async def on_timeout(self):
                    await self.safe_send(user, "⌛ Onboarding timed out.")
                    self.stop()

            view = RegionSelect()
            await self.safe_send(user, embed=embed, view=view)
            await view.wait()

            # Detect selected button
            selected_region = None
            for child in view.children:
                if getattr(child, "custom_id", "").startswith("region_") and getattr(child, "clicked", False):
                    selected_region = child.custom_id.replace("region_", "")
            if not selected_region:
                selected_region = list(REGIONS.keys())[0]  # fallback

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Onboarding Step 1 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 1. Try again later.")
            return

        # -----------------------
        # Step 2: Select Zodiac
        # -----------------------
        try:
            embed = discord.Embed(
                title="🌟 Choose your Zodiac",
                description="Select your **zodiac sign** below:",
                color=0xf1c40f
            )

            class ZodiacSelect(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.selected_zodiac = None

                    for zodiac, emoji in ZODIAC_SIGNS.items():
                        self.add_item(discord.ui.Button(
                            label=f"{emoji} {zodiac}",
                            style=discord.ButtonStyle.secondary,
                            custom_id=f"zodiac_{zodiac}"
                        ))

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="zodiac_cancel")
                async def cancel(self, button: discord.ui.Button, interaction_: discord.Interaction):
                    await self.safe_send(interaction_, "❌ Onboarding cancelled.")
                    self.stop()

                async def interaction_check(self, interaction_: discord.Interaction) -> bool:
                    return interaction_.user.id == user.id

                async def on_timeout(self):
                    await self.safe_send(user, "⌛ Onboarding timed out.")
                    self.stop()

            view = ZodiacSelect()
            await self.safe_send(user, embed=embed, view=view)
            await view.wait()

            selected_zodiac = None
            for child in view.children:
                if getattr(child, "custom_id", "").startswith("zodiac_") and getattr(child, "clicked", False):
                    selected_zodiac = child.custom_id.replace("zodiac_", "")
            if not selected_zodiac:
                selected_zodiac = list(ZODIAC_SIGNS.keys())[0]  # fallback

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Onboarding Step 2 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 2. Try again later.")
            return

        # -----------------------
        # Step 3: Subscribe to Daily Reminders
        # -----------------------
        try:
            embed = discord.Embed(
                title="🔔 Daily Notifications",
                description="Would you like to **subscribe** to daily DM reminders?",
                color=0x2ecc71
            )

            class SubscribeSelect(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.subscribed = True  # default

                    self.add_item(discord.ui.Button(label="✅ Subscribe", style=discord.ButtonStyle.success, custom_id="subscribe_yes"))
                    self.add_item(discord.ui.Button(label="❌ No Thanks", style=discord.ButtonStyle.danger, custom_id="subscribe_no"))

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="subscribe_cancel")
                async def cancel(self, button: discord.ui.Button, interaction_: discord.Interaction):
                    await self.safe_send(interaction_, "❌ Onboarding cancelled.")
                    self.stop()

                async def interaction_check(self, interaction_: discord.Interaction) -> bool:
                    return interaction_.user.id == user.id

                async def on_timeout(self):
                    await self.safe_send(user, "⌛ Onboarding timed out.")
                    self.stop()

            view = SubscribeSelect()
            await self.safe_send(user, embed=embed, view=view)
            await view.wait()

            # Detect choice
            subscribed = True
            for child in view.children:
                if getattr(child, "custom_id", "").startswith("subscribe_") and getattr(child, "clicked", False):
                    subscribed = child.custom_id == "subscribe_yes"

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Onboarding Step 3 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 3. Try again later.")
            return

        # -----------------------
        # Save Preferences
        # -----------------------
        try:
            set_user_preferences(user.id, region=selected_region, zodiac=selected_zodiac, subscribed=subscribed)
            await self.safe_send(user, f"🎉 Onboarding complete! Welcome, {user.name} 🌙")
        except Exception as e:
            await log_error(self.bot, f"[ERROR] Saving onboarding preferences failed: {e}")
            await self.safe_send(user, "⚠️ Could not save your onboarding preferences. Try again later.")


async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
