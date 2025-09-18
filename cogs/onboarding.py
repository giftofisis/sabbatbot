import os
import discord
from discord.ext import commands
from discord import app_commands
from db import save_user_preferences

# -----------------------
# Config
# -----------------------
GUILD_ID = int(os.getenv("GUILD_ID"))
LOG_CHANNEL_ID = 1418171996583366727  # Central error log channel

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
# Logging
# -----------------------
async def log_error(bot, message: str):
    print(message)  # Railway logs
    try:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            channel = guild.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(f"⚠️ {message}")
    except Exception as e:
        print(f"[LOGGING ERROR] Failed to send log to channel: {e}")


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
            guild = self.bot.get_guild(GUILD_ID)
            if not guild:
                await interaction.response.send_message(
                    "⚠️ Could not access server. Please contact an admin.", ephemeral=True
                )
                await log_error(self.bot, f"[ERROR] Guild not found (GUILD_ID={GUILD_ID})")
                return

            region_data = REGIONS[self.region_name]
            role = guild.get_role(region_data["role_id"])
            if not role:
                await interaction.response.send_message(
                    "⚠️ Role not found. Please contact an admin.", ephemeral=True
                )
                await log_error(self.bot, f"[ERROR] Role ID {region_data['role_id']} missing in guild {guild.name}")
                return

            try:
                # Remove previous region roles
                for r in REGIONS.values():
                    prev_role = guild.get_role(r["role_id"])
                    if prev_role and prev_role in self.member.roles:
                        await self.member.remove_roles(prev_role)

                await self.member.add_roles(role)
                save_user_preferences(self.member.id, region=self.region_name)

                await interaction.response.send_message(
                    f"✅ Region **{self.region_name}** assigned!", ephemeral=True
                )

                # Proceed to Zodiac selection
                try:
                    await interaction.user.send(
                        "🌟 Now choose your Zodiac sign:",
                        view=OnboardingCog.ZodiacView(self.member)
                    )
                except discord.Forbidden:
                    await log_error(self.bot, f"[WARN] Could not DM {interaction.user} for zodiac step.")
                    await interaction.followup.send(
                        "⚠️ I couldn’t DM you. Please enable DMs.", ephemeral=True
                    )
            except Exception as e:
                await log_error(self.bot, f"[ERROR] Failed assigning region: {e}")
                await interaction.response.send_message(
                    "⚠️ Something went wrong. Try again later.", ephemeral=True
                )

    class RegionView(discord.ui.View):
        def __init__(self, member, bot):
            super().__init__(timeout=None)
            for name, data in REGIONS.items():
                self.add_item(OnboardingCog.RegionButton(name, data["emoji"], member, bot))

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
                await interaction.response.send_message(f"✅ Zodiac **{self.zodiac}** saved!", ephemeral=True)

                # Proceed to Subscription
                try:
                    await interaction.user.send(
                        "📅 Do you want to receive daily reminders?",
                        view=OnboardingCog.SubscriptionView(self.member)
                    )
                except discord.Forbidden:
                    await log_error(interaction.client, f"[WARN] Could not DM {interaction.user} for subscription step.")
                    await interaction.followup.send(
                        "⚠️ I couldn’t DM you. Please enable DMs.", ephemeral=True
                    )
            except Exception as e:
                await log_error(interaction.client, f"[ERROR] Failed saving zodiac: {e}")
                await interaction.response.send_message(
                    "⚠️ Could not save your zodiac. Try again later.", ephemeral=True
                )

    class ZodiacView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=None)
            for name, emoji in ZODIACS.items():
                self.add_item(OnboardingCog.ZodiacButton(name, emoji, member))

    # -------------------
    # Subscription
    # -------------------
    class SubscriptionButton(discord.ui.Button):
        def __init__(self, label, subscribe, member):
            style = discord.ButtonStyle.success if subscribe else discord.ButtonStyle.danger
            super().__init__(label=label, style=style)
            self.subscribe = subscribe
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            try:
                save_user_preferences(self.member.id, subscribed=1 if self.subscribe else 0)
                status_msg = "✅ Subscribed to daily reminders!" if self.subscribe else "❌ Opted out of reminders."
                await interaction.response.send_message(status_msg, ephemeral=True)
            except Exception as e:
                await log_error(interaction.client, f"[ERROR] Failed saving subscription: {e}")
                await interaction.response.send_message(
                    "⚠️ Could not save your preference. Try again later.", ephemeral=True
                )

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
            dm = await member.create_dm()
            await dm.send(
                "👋 Welcome! Let’s get started. First, choose your region:",
                view=self.RegionView(member, self.bot)
            )
        except discord.Forbidden:
            await log_error(self.bot, f"[WARN] Could not DM {member} ({member.id}) during onboarding.")
            if member.guild.system_channel:
                await member.guild.system_channel.send(
                    f"⚠️ {member.mention}, I couldn’t DM you. Please enable DMs and run `/onboard`."
                )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.start_onboarding(member)

    @app_commands.command(name="onboard", description="Start onboarding manually")
    async def onboard(self, interaction: discord.Interaction):
        await self.start_onboarding(interaction.user)
        await interaction.response.send_message(
            "✅ Check your DMs for onboarding!", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
