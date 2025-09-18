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
        print(f"[LOGGING ERROR] Failed to send log to channel: {e}")

# -----------------------
# Safe Send Helper
# -----------------------
async def safe_send(target, *args, view=None, **kwargs):
    """Safely send a message or DM, ignoring finished views or forbidden errors."""
    try:
        if view is not None and getattr(view, "is_finished", False):
            view = None
        return await target.send(*args, view=view, **kwargs)
    except discord.Forbidden:
        print(f"⚠️ Could not send message to {target}.")
    except Exception as e:
        print(f"[ERROR] Failed safe_send: {e}")

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
                await safe_send(interaction.response, content="⚠️ Could not access server.", ephemeral=True)
                await log_error(self.bot, f"[ERROR] Guild not found (GUILD_ID={GUILD_ID})")
                return

            region_data = REGIONS[self.region_name]
            role = guild.get_role(region_data["role_id"])
            if not role:
                await safe_send(interaction.response, content="⚠️ Role not found in server.", ephemeral=True)
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

                await safe_send(interaction.response, content=f"✅ Region **{self.region_name}** assigned!", ephemeral=True)

                # Next step: Zodiac
                try:
                    await safe_send(self.member, "🌟 Please choose your Zodiac sign:", view=OnboardingCog.ZodiacView(self.member))
                except discord.Forbidden:
                    await log_error(self.bot, f"[WARN] Could not DM {self.member} for zodiac step.")

            except Exception as e:
                await log_error(self.bot, f"[ERROR] Failed assigning region role: {e}")
                await safe_send(interaction.response, content="⚠️ Something went wrong. Try again later.", ephemeral=True)

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
                await safe_send(interaction.response, content=f"✅ Zodiac **{self.zodiac}** saved!", ephemeral=True)

                # Next step: Subscription
                try:
                    await safe_send(self.member, "📅 Would you like to receive daily notifications?", view=OnboardingCog.SubscriptionView(self.member))
                except discord.Forbidden:
                    await log_error(self.bot, f"[WARN] Could not DM {self.member} for subscription step.")
            except Exception as e:
                await log_error(self.bot, f"[ERROR] Failed saving zodiac: {e}")
                await safe_send(interaction.response, content="⚠️ Could not save your zodiac. Try again later.", ephemeral=True)

    class ZodiacView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=None)
            for name, emoji in ZODIACS.items():
                self.add_item(OnboardingCog.ZodiacButton(name, emoji, member))

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
                save_user_preferences(self.member.id, subscribed=int(self.subscribed))
                status = "✅ You’re subscribed to reminders!" if self.subscribed else "❌ You opted out."
                await safe_send(interaction.response, content=status, ephemeral=True)

                # Final step message
                await safe_send(self.member, "🎉 Thank you for completing onboarding! Enjoy our community!")
            except Exception as e:
                await log_error(self.bot, f"[ERROR] Failed saving subscription: {e}")
                await safe_send(interaction.response, content="⚠️ Could not save your preference. Try again later.", ephemeral=True)

    class SubscriptionView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=None)
            self.add_item(OnboardingCog.SubscriptionButton("Subscribe", True, member))
            self.add_item(OnboardingCog.SubscriptionButton("Unsubscribe", False, member))

    # -------------------
    # Start Onboarding
    # -------------------
    async def start_onboarding(self, member):
        welcome_message = (
            "✨ Welcome to the Circle! ✨\n"
            "Greetings, seeker! 🌙\n\n"
            "Please select your region below so you can access region-specific channels "
            "and receive updates tailored for you.\n"
            "You can manage daily DM reminders via the buttons."
        )
        try:
            await safe_send(member, welcome_message, view=self.RegionView(member, self.bot))
        except discord.Forbidden:
            await log_error(self.bot, f"[WARN] Could not DM {member} during onboarding.")
            channel = member.guild.system_channel
            if channel:
                await safe_send(channel, f"⚠️ {member.mention}, please enable DMs to start onboarding.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.start_onboarding(member)

    @app_commands.command(name="onboard", description="Start onboarding manually")
    async def onboard(self, interaction: discord.Interaction):
        await self.start_onboarding(interaction.user)
        await safe_send(interaction.response, content="✅ Check your DMs for onboarding!", ephemeral=True)

# -----------------------
# Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
