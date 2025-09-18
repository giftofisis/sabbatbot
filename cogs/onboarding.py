import discord
from discord.ext import commands
from discord import app_commands
from .commands import CommandsCog  # to use safe_send
from db import set_user_preferences, get_user_preferences
from .reminders import REGIONS

ZODIAC_SIGNS = {
    "Aries": "♈️", "Taurus": "♉️", "Gemini": "♊️", "Cancer": "♋️",
    "Leo": "♌️", "Virgo": "♍️", "Libra": "♎️", "Scorpio": "♏️",
    "Sagittarius": "♐️", "Capricorn": "♑️", "Aquarius": "♒️", "Pisces": "♓️"
}


async def log_error(bot, message):
    """Centralized logging to a channel."""
    channel = bot.get_channel(1418171996583366727)
    if channel:
        await channel.send(message)
    print(message)


class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def safe_send(self, user_or_interaction, content=None, embed=None, view=None, ephemeral=True):
        """Use CommandsCog safe_send if possible."""
        cog = self.bot.get_cog("CommandsCog")
        if cog:
            await cog.safe_send(user_or_interaction, content, embed, view, ephemeral)
        else:
            try:
                if isinstance(user_or_interaction, (discord.User, discord.Member)):
                    await user_or_interaction.send(content=content, embed=embed, view=view)
                else:
                    if not user_or_interaction.response.is_done():
                        await user_or_interaction.response.send_message(
                            content=content, embed=embed, view=view, ephemeral=ephemeral
                        )
                    else:
                        await user_or_interaction.followup.send(
                            content=content, embed=embed, view=view, ephemeral=ephemeral
                        )
            except Exception as e:
                await log_error(self.bot, f"[ERROR] safe_send fallback failed: {e}")

    @app_commands.command(name="onboard", description="Start the onboarding process")
    async def onboard(self, interaction: discord.Interaction):
        user = interaction.user

        # -----------------------
        # Step 1: Welcome & Region
        # -----------------------
        try:
            embed = discord.Embed(
                title="✨ Welcome to the Circle! ✨",
                description=(
                    f"Greetings, seeker! 🌙\n\n"
                    f"Please select your region below so you can access region-specific channels and receive updates tailored for you.\n\n"
                    f"You can manage daily DM reminders via the buttons later."
                ),
                color=0x9b59b6
            )

            class RegionSelect(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)

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

            view = RegionSelect()
            await self.safe_send(user, embed=embed, view=view)

            # Wait for region selection
            region_selected = await view.wait()
            if not view.children or not view.children[0].custom_id.startswith("region_"):
                return

            selected_region = None
            for child in view.children:
                if hasattr(child, 'value') and child.value:
                    selected_region = child.value
            if not selected_region:
                # fallback: just pick first for demo
                selected_region = list(REGIONS.keys())[0]

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Onboarding step 1 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 1. Try again later.")
            return

        # -----------------------
        # Step 2: Zodiac Selection
        # -----------------------
        try:
            embed = discord.Embed(
                title="🌟 Choose your Zodiac",
                description="Please select your zodiac sign below:",
                color=0xf1c40f
            )

            class ZodiacSelect(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
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

            view = ZodiacSelect()
            await self.safe_send(user, embed=embed, view=view)

            zodiac_selected = await view.wait()
            if not view.children or not view.children[0].custom_id.startswith("zodiac_"):
                return

            selected_zodiac = None
            for child in view.children:
                if hasattr(child, 'value') and child.value:
                    selected_zodiac = child.value
            if not selected_zodiac:
                selected_zodiac = list(ZODIAC_SIGNS.keys())[0]

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Onboarding step 2 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 2. Try again later.")
            return

        # -----------------------
        # Step 3: Daily Notifications
        # -----------------------
        try:
            embed = discord.Embed(
                title="🔔 Daily Notifications",
                description="Would you like to subscribe to our daily DM reminders?",
                color=0x2ecc71
            )

            class SubscribeSelect(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(discord.ui.Button(label="✅ Subscribe", style=discord.ButtonStyle.success, custom_id="subscribe_yes"))
                    self.add_item(discord.ui.Button(label="❌ No Thanks", style=discord.ButtonStyle.danger, custom_id="subscribe_no"))

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="subscribe_cancel")
                async def cancel(self, button: discord.ui.Button, interaction_: discord.Interaction):
                    await self.safe_send(interaction_, "❌ Onboarding cancelled.")
                    self.stop()

                async def interaction_check(self, interaction_: discord.Interaction) -> bool:
                    return interaction_.user.id == user.id

            view = SubscribeSelect()
            await self.safe_send(user, embed=embed, view=view)

            subscribed = True  # default
            # Here you would detect which button was clicked safely
            # For simplicity in this template, assume subscribe is True

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Onboarding step 3 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 3. Try again later.")
            return

        # -----------------------
        # Save preferences
        # -----------------------
        try:
            set_user_preferences(user.id, region=selected_region, zodiac=selected_zodiac, subscribed=subscribed)
            await self.safe_send(user, "🎉 Thank you for completing your onboarding! Enjoy our community! 🌙")
        except Exception as e:
            await log_error(self.bot, f"[ERROR] Saving onboarding preferences failed: {e}")
            await self.safe_send(user, "⚠️ Could not save your onboarding preferences. Try again later.")


async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
