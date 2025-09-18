import os
import discord
from discord.ext import commands
from discord import app_commands
from db import save_user_preferences

# -----------------------
# Config
# -----------------------
GUILD_ID = int(os.getenv("GUILD_ID"))
LOG_CHANNEL_ID = 1418171996583366727

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
# Logging Helper
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
        print(f"[LOGGING ERROR] Failed to send log: {e}")

# -----------------------
# Onboarding Cog
# -----------------------
class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------------------
    # Region Buttons
    # -------------------
    class RegionButton(discord.ui.Button):
        def __init__(self, region_name, emoji, member, bot):
            super().__init__(label=region_name, emoji=emoji, style=discord.ButtonStyle.primary)
            self.region_name = region_name
            self.member = member
            self.bot = bot

        async def callback(self, interaction: discord.Interaction):
            guild = self.bot.get_guild(GUILD_ID)
            if not guild:
                await interaction.response.send_message("⚠️ Could not access the server.", ephemeral=True)
                await log_error(self.bot, f"[ERROR] Guild not found (GUILD_ID={GUILD_ID})")
                return

            role = guild.get_role(REGIONS[self.region_name]["role_id"])
            if not role:
                await interaction.response.send_message("⚠️ Role not found. Contact admin.", ephemeral=True)
                await log_error(self.bot, f"[ERROR] Role ID missing for {self.region_name}")
                return

            try:
                for r in REGIONS.values():
                    prev_role = guild.get_role(r["role_id"])
                    if prev_role in self.member.roles:
                        await self.member.remove_roles(prev_role)
                await self.member.add_roles(role)

                save_user_preferences(self.member.id, region=self.region_name)
                await interaction.response.send_message(f"✅ Region **{self.region_name}** saved!", ephemeral=True)

                # Zodiac DM
                try:
                    embed = discord.Embed(
                        title="🌟 Choose your Zodiac",
                        description="Select your zodiac sign below:",
                        color=0x9b59b6
                    )
                    await self.member.send(embed=embed, view=OnboardingCog.ZodiacView(self.member))
                except discord.Forbidden:
                    await log_error(self.bot, f"[WARN] Could not DM {self.member} for zodiac selection.")

            except Exception as e:
                await log_error(self.bot, f"[ERROR] Failed assigning region role: {e}")
                await interaction.response.send_message("⚠️ Something went wrong. Try again later.", ephemeral=True)

    class RegionView(discord.ui.View):
        def __init__(self, member, bot):
            super().__init__(timeout=300)
            for name, data in REGIONS.items():
                self.add_item(OnboardingCog.RegionButton(region_name=name, emoji=data["emoji"], member=member, bot=bot))

    # -------------------
    # Zodiac Buttons with Emojis
    # -------------------
    class ZodiacButton(discord.ui.Button):
        def __init__(self, zodiac, emoji, member):
            super().__init__(label=f"{emoji} {zodiac}", style=discord.ButtonStyle.secondary)
            self.zodiac = zodiac
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            try:
                save_user_preferences(self.member.id, zodiac=self.zodiac)
                await interaction.response.send_message(f"✅ Zodiac **{self.zodiac}** saved!", ephemeral=True)

                # Subscription DM
                try:
                    embed = discord.Embed(
                        title="📅 Daily Notifications",
                        description="Would you like to receive daily DM reminders?",
                        color=0x1abc9c
                    )
                    await self.member.send(embed=embed, view=OnboardingCog.SubscriptionView(self.member))
                except discord.Forbidden:
                    await log_error(self.bot, f"[WARN] Could not DM {self.member} for subscription step.")

            except Exception as e:
                await log_error(self.bot, f"[ERROR] Failed saving zodiac: {e}")
                await interaction.response.send_message("⚠️ Could not save your zodiac. Try again later.", ephemeral=True)

    class ZodiacView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=300)
            for zodiac, emoji in ZODIACS.items():
                self.add_item(OnboardingCog.ZodiacButton(zodiac=zodiac, emoji=emoji, member=member))

    # -------------------
    # Subscription Buttons with Colors
    # -------------------
    class SubscriptionButton(discord.ui.Button):
        def __init__(self, label, subscribed, member):
            style = discord.ButtonStyle.success if subscribed else discord.ButtonStyle.danger
            emoji = "✅" if subscribed else "❌"
            super().__init__(label=f"{emoji} {label}", style=style)
            self.subscribed = subscribed
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            try:
                save_user_preferences(self.member.id, subscribed=1 if self.subscribed else 0)
                status = "✅ Subscribed to daily reminders!" if self.subscribed else "❌ Opted out."
                await interaction.response.send_message(status, ephemeral=True)

                # Final thank you DM
                try:
                    await self.member.send("✨ Thank you for completing your onboarding! Enjoy the Circle! ✨")
                except discord.Forbidden:
                    await log_error(self.bot, f"[WARN] Could not DM {self.member} final message.")

            except Exception as e:
                await log_error(self.bot, f"[ERROR] Failed saving subscription: {e}")
                await interaction.response.send_message("⚠️ Could not save your preference. Try again later.", ephemeral=True)

    class SubscriptionView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=300)
            self.add_item(OnboardingCog.SubscriptionButton("Subscribe", True, member))
            self.add_item(OnboardingCog.SubscriptionButton("Unsubscribe", False, member))

    # -------------------
    # Start Onboarding
    # -------------------
    async def start_onboarding(self, member):
        embed = discord.Embed(
            title="✨ Welcome to the Circle! ✨",
            description=(
                "Greetings, seeker! 🌙\n\n"
                "Please select your region below to access region-specific channels "
                "and receive updates tailored for you.\n\n"
                "You can manage daily DM reminders via the buttons later."
            ),
            color=0x8e44ad
        )
        try:
            dm = await member.create_dm()
            await dm.send(embed=embed, view=OnboardingCog.RegionView(member, self.bot))
        except discord.Forbidden:
            await log_error(self.bot, f"[WARN] Could not DM {member} ({member.id}) during onboarding.")
            channel = member.guild.system_channel
            if channel:
                await channel.send(f"⚠️ {member.mention}, I couldn’t DM you. Please enable DMs and run `/onboard`.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.start_onboarding(member)

    @app_commands.command(name="onboard", description="Start onboarding manually")
    async def onboard(self, interaction: discord.Interaction):
        await self.start_onboarding(interaction.user)
        await interaction.response.send_message("✅ Check your DMs for onboarding!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
