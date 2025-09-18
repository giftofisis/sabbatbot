import discord
from discord.ext import commands
from discord import app_commands
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
        await interaction.response.defer(ephemeral=True)

        # --- Step 1: Region ---
        try:
            embed = discord.Embed(
                title="✨ Welcome to GBPBot! ✨",
                description="Select your **region** below:",
                color=0x9b59b6
            )

            class RegionView(discord.ui.View):
                def __init__(self, user_id):
                    super().__init__(timeout=None)
                    self.selected_region = None
                    self.user_id = user_id
                    for region_name, data in REGIONS.items():
                        self.add_item(discord.ui.Button(
                            label=f"{data['emoji']} {region_name}",
                            style=discord.ButtonStyle.primary,
                            custom_id=f"region_{region_name}"
                        ))

                async def interaction_check(self, inter):
                    return inter.user.id == self.user_id

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="region_cancel")
                async def cancel(self, button, inter):
                    await inter.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
                    self.stop()

                async def on_timeout(self):
                    self.stop()

            # Assign dynamic callbacks
            def make_region_callback(region_name):
                async def callback(button, inter):
                    view.selected_region = region_name
                    await inter.response.send_message(f"✅ Selected region: {region_name}", ephemeral=True)
                    view.stop()
                return callback

            view = RegionView(user.id)
            for child in view.children:
                if isinstance(child, discord.ui.Button) and child.custom_id.startswith("region_") and child.custom_id != "region_cancel":
                    region_name = child.custom_id.split("_")[1]
                    child.callback = make_region_callback(region_name)

            await self.safe_send(user, embed=embed, view=view)
            await view.wait()
            selected_region = view.selected_region or list(REGIONS.keys())[0]

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
                def __init__(self, user_id):
                    super().__init__(timeout=None)
                    self.selected_zodiac = None
                    self.user_id = user_id
                    for zodiac, emoji in ZODIAC_SIGNS.items():
                        self.add_item(discord.ui.Button(
                            label=f"{emoji} {zodiac}",
                            style=discord.ButtonStyle.secondary,
                            custom_id=f"zodiac_{zodiac}"
                        ))

                async def interaction_check(self, inter):
                    return inter.user.id == self.user_id

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="zodiac_cancel")
                async def cancel(self, button, inter):
                    await inter.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
                    self.stop()

                async def on_timeout(self):
                    self.stop()

            # Assign dynamic callbacks
            def make_zodiac_callback(zodiac):
                async def callback(button, inter):
                    view.selected_zodiac = zodiac
                    await inter.response.send_message(f"✅ Selected zodiac: {zodiac}", ephemeral=True)
                    view.stop()
                return callback

            view = ZodiacView(user.id)
            for child in view.children:
                if isinstance(child, discord.ui.Button) and child.custom_id.startswith("zodiac_") and child.custom_id != "zodiac_cancel":
                    zodiac_name = child.custom_id.split("_")[1]
                    child.callback = make_zodiac_callback(zodiac_name)

            await self.safe_send(user, embed=embed, view=view)
            await view.wait()
            selected_zodiac = view.selected_zodiac or list(ZODIAC_SIGNS.keys())[0]

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
                def __init__(self, user_id):
                    super().__init__(timeout=None)
                    self.subscribed = None
                    self.user_id = user_id

                async def interaction_check(self, inter):
                    return inter.user.id == self.user_id

                @discord.ui.button(label="✅ Subscribe", style=discord.ButtonStyle.success, custom_id="subscribe_yes")
                async def subscribe_yes(self, button, inter):
                    self.subscribed = True
                    await inter.response.send_message("✅ Subscribed to daily reminders!", ephemeral=True)
                    self.stop()

                @discord.ui.button(label="❌ No Thanks", style=discord.ButtonStyle.danger, custom_id="subscribe_no")
                async def subscribe_no(self, button, inter):
                    self.subscribed = False
                    await inter.response.send_message("❌ You opted out of daily reminders.", ephemeral=True)
                    self.stop()

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="subscribe_cancel")
                async def cancel(self, button, inter):
                    await inter.response.send_message("❌ Onboarding cancelled.", ephemeral=True)
                    self.stop()

            view = SubscribeView(user.id)
            await self.safe_send(user, embed=embed, view=view)
            await view.wait()
            subscribed = view.subscribed if view.subscribed is not None else True

        except Exception as e:
            await log_error(self.bot, f"[ERROR] Step 3 failed: {e}")
            await self.safe_send(user, "⚠️ Onboarding failed at step 3.")
            await interaction.followup.send("⚠️ Onboarding failed.", ephemeral=True)
            return

        # --- Save to SQLite DB ---
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
