import os
import discord
from discord.ext import commands
from discord import app_commands
from db import save_user_preferences

# -----------------------
# Config
# -----------------------
GUILD_ID = int(os.getenv("GUILD_ID"))
LOG_CHANNEL_ID = 1418171996583366727  # central error log channel

REGIONS = {
    "North America": {"role_id": 1416438886397251768, "emoji": "🇺🇸"},
    "South America": {"role_id": 1416438925140164809, "emoji": "🌴"},
    "Europe": {"role_id": 1416439011517534288, "emoji": "🍀"},
    "Africa": {"role_id": 1416439116043649224, "emoji": "🌍"},
    "Oceania & Asia": {"role_id": 1416439141339758773, "emoji": "🌺"},
}

ZODIACS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
}


# -----------------------
# Helpers
# -----------------------
async def log_error(bot, message: str):
    print(message)
    try:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            channel = guild.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(f"⚠️ {message}")
    except Exception as e:
        print(f"[LOGGING ERROR] Failed to send log to channel: {e}")


async def safe_send(channel, content=None, embed=None, view=None):
    """Safely send a message to a channel or DM."""
    try:
        return await channel.send(content=content, embed=embed, view=view)
    except discord.Forbidden:
        return None


# -----------------------
# Onboarding Cog
# -----------------------
class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------------------
    # Region Selection
    # -------------------
    class RegionButton(discord.ui.Button):
        def __init__(self, region_name, emoji, member, bot):
            super().__init__(label=region_name, emoji=emoji, style=discord.ButtonStyle.primary)
            self.region_name = region_name
            self.member = member
            self.bot = bot

        async def callback(self, interaction: discord.Interaction):
            try:
                save_user_preferences(self.member.id, region=self.region_name)

                # Move to Zodiac selection
                dm = self.member.dm_channel or await self.member.create_dm()
                await safe_send(dm, "🌟 Please choose your zodiac:", view=OnboardingCog.ZodiacView(self.member))

                await interaction.response.send_message(f"✅ Region **{self.region_name}** saved!", ephemeral=True)
            except Exception as e:
                await log_error(self.bot, f"[ERROR] Failed saving region: {e}")
                await interaction.response.send_message("⚠️ Could not save your region. Try again later.", ephemeral=True)

    class RegionView(discord.ui.View):
        def __init__(self, member, bot):
            super().__init__(timeout=None)
            for name, data in REGIONS.items():
                self.add_item(OnboardingCog.RegionButton(region_name=name, emoji=data["emoji"], member=member, bot=bot))

    # -------------------
    # Zodiac Selection
    # -------------------
    class ZodiacButton(discord.ui.Button):
        def __init__(self, zodiac, emoji, member):
            super().__init__(label=zodiac, emoji=emoji, style=discord.ButtonStyle.secondary)
            self.zodiac = zodiac
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            try:
                save_user_preferences(self.member.id, zodiac=self.zodiac)

                # Move to Subscription
                dm = self.member.dm_channel or await self.member.create_dm()
                await safe_send(dm, "📅 Would you like to receive daily notifications?", view=OnboardingCog.SubscriptionView(self.member))

                await interaction.response.send_message(f"✅ Zodiac **{self.zodiac}** saved!", ephemeral=True)
            except Exception as e:
                await log_error(interaction.client, f"[ERROR] Failed saving zodiac: {e}")
                await interaction.response.send_message("⚠️ Could not save your zodiac. Try again later.", ephemeral=True)

    class ZodiacView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=None)
            for name, emoji in ZODIACS.items():
                self.add_item(OnboardingCog.ZodiacButton(zodiac=name, emoji=emoji, member=member))

    # -------------------
    # Subscription Selection
    # -------------------
    class SubscriptionButton(discord.ui.Button):
        def __init__(self, label, subscribed, member):
            style = discord.ButtonStyle.success if subscribed else discord.ButtonStyle.danger
            super().__init__(label=label, style=style)
            self.subscribed = subscribed
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            try:
                save_user_preferences(self.member.id, subscribed=1 if self.subscribed else 0)
                status_msg = "✅ You’re subscribed to reminders!" if self.subscribed else "❌ You opted out."
                await interaction.response.send_message(status_msg, ephemeral=True)

                # Final thank-you message
                dm = self.member.dm_channel or await self.member.create_dm()
                await safe_send(dm, "🎉 Thank you for completing your onboarding! Enjoy our community! 🌙")
            except Exception as e:
                await log_error(interaction.client, f"[ERROR] Failed saving subscription: {e}")
                await interaction.response.send_message("⚠️ Could not save your preference. Try again later.", ephemeral=True)

    class SubscriptionView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=None)
            self.add_item(OnboardingCog.SubscriptionButton("Subscribe", True, member))
            self.add_item(OnboardingCog.SubscriptionButton("Unsubscribe", False, member))

    # -------------------
    # Start Onboarding
    # -------------------
    async def start_onboarding(self, member):
        try:
            dm = member.dm_channel or await member.create_dm()
            welcome_msg = (
                "✨ Welcome to the Circle! ✨\n"
                "Greetings, seeker! 🌙\n\n"
                "Please select your region below so you can access region-specific channels "
                "and receive updates tailored for you.\n\n"
                "You can manage daily DM reminders via the buttons in the following steps."
            )
            await safe_send(dm, welcome_msg, view=OnboardingCog.RegionView(member, self.bot))
        except discord.Forbidden:
            await log_error(self.bot, f"[WARN] Could not DM {member} ({member.id}) during onboarding.")
            channel = member.guild.system_channel
            if channel:
                await safe_send(channel, f"⚠️ {member.mention}, I couldn’t DM you. Please enable DMs and run `/onboard`.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.start_onboarding(member)

    @app_commands.command(name="onboard", description="Start onboarding manually")
    async def onboard(self, interaction: discord.Interaction):
        await self.start_onboarding(interaction.user)
        await interaction.response.send_message("✅ Check your DMs for onboarding!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
