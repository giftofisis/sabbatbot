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
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)
    finally:
        print(message)


class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def safe_send(self, user: discord.User, content=None, embed=None, view=None):
        try:
            await user.send(content=content, embed=embed, view=view)
        except discord.Forbidden:
            await log_error(self.bot, f"[ERROR] Cannot DM user {user.id}")
        except Exception as e:
            await log_error(self.bot, f"[ERROR] safe_send failed: {e}")

    @app_commands.command(name="onboard", description="Start the onboarding process")
    async def onboard(self, interaction: discord.Interaction):
        user = interaction.user

        # Defer the interaction to avoid "This interaction failed"
        await interaction.response.defer(ephemeral=True)

        # --- Step 1: Region ---
        try:
            embed = discord.Embed(
                title="✨ Welcome to GBPBot! ✨",
                description="Select your **region** below:",
                color=0x9b59b6
            )

            class RegionView(discord.ui.View):
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
                async def cancel(self, button, inter):
                    await inter.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
                    self.stop()

                async def interaction_check(self, inter):
                    return inter.user.id == user.id

                async def on_timeout(self):
                    self.stop()

            region_view = RegionView()
            await self.safe_send(user, embed=embed, view=region_view)
            await region_view.wait()
            selected_region = region_view.selected_region or list(REGIONS.keys())[0]

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Step 1 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 1.")
            await interaction.followup.send("⚠️ Onboarding failed.", ephemeral=True)
            return

        # --- Step 2: Zodiac ---
        try:
            embed = discord.Embed(
                title="🌟 Choose your Zodiac",
                description="Select your zodiac sign:",
                color=0xf1c40f
            )

            class ZodiacView(discord.ui.View):
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
                async def cancel(self, button, inter):
                    await inter.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
                    self.stop()

                async def interaction_check(self, inter):
                    return inter.user.id == user.id

            zodiac_view = ZodiacView()
            await self.safe_send(user, embed=embed, view=zodiac_view)
            await zodiac_view.wait()
            selected_zodiac = zodiac_view.selected_zodiac or list(ZODIAC_SIGNS.keys())[0]

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Step 2 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 2.")
            await interaction.followup.send("⚠️ Onboarding failed.", ephemeral=True)
            return

        # --- Step 3: Daily Reminders ---
        try:
            embed = discord.Embed(
                title="🔔 Daily Notifications",
                description="Subscribe to daily DM reminders?",
                color=0x2ecc71
            )

            class SubscribeView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.subscribed = None
                    self.add_item(discord.ui.Button(label="✅ Subscribe", style=discord.ButtonStyle.success, custom_id="subscribe_yes"))
                    self.add_item(discord.ui.Button(label="❌ No Thanks", style=discord.ButtonStyle.danger, custom_id="subscribe_no"))

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="subscribe_cancel")
                async def cancel(self, button, inter):
                    await inter.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
                    self.stop()

                async def interaction_check(self, inter):
                    return inter.user.id == user.id

            subscribe_view = SubscribeView()
            await self.safe_send(user, embed=embed, view=subscribe_view)
            await subscribe_view.wait()
            subscribed = subscribe_view.subscribed if subscribe_view.subscribed is not None else True

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Step 3 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 3.")
            await interaction.followup.send("⚠️ Onboarding failed.", ephemeral=True)
            return

        # --- Save Preferences ---
        try:
            set_user_preferences(user.id, region=selected_region, zodiac=selected_zodiac, subscribed=subscribed)
            await self.safe_send(user, f"🎉 Onboarding complete! Welcome, {user.name} 🌙")
            await interaction.followup.send("✅ Onboarding complete! Check your DMs.", ephemeral=True)
        except Exception as e:
            await log_error(self.bot, f"[ERROR] Saving preferences failed: {e}")
            await self.safe_send(user, "⚠️ Could not save preferences.")
            await interaction.followup.send("⚠️ Onboarding failed at final step.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
