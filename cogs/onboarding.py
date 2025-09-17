import discord
from discord.ext import commands
from discord import app_commands
from ..db import save_user_preferences, set_subscription

# -----------------------
# Region & Zodiac Data
# -----------------------
REGIONS = {
    "North America": {"name": "North America", "role_id": 1416438886397251768, "emoji": "🇺🇸"},
    "South America": {"name": "South America", "role_id": 1416438925140164809, "emoji": "🌴"},
    "Europe": {"name": "Europe", "role_id": 1416439011517534288, "emoji": "🍀"},
    "Africa": {"name": "Africa", "role_id": 1416439116043649224, "emoji": "🌍"},
    "Oceania & Asia": {"name": "Oceania & Asia", "role_id": 1416439141339758773, "emoji": "🌺"},
}

ZODIACS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
}

# -----------------------
# Onboarding Cog
# -----------------------
class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # Region Selection Buttons
    # -----------------------
    class RegionButton(discord.ui.Button):
        def __init__(self, label, emoji, member, bot):
            super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
            self.member = member
            self.bot = bot

        async def callback(self, interaction: discord.Interaction):
            guild = self.bot.get_guild(interaction.guild_id)
            if not guild:
                await interaction.response.send_message("⚠️ Could not find your server.", ephemeral=True)
                return

            region_data = REGIONS[self.label]
            role = guild.get_role(region_data["role_id"])
            if not role:
                await interaction.response.send_message(f"⚠️ Role for {region_data['name']} not found.", ephemeral=True)
                return

            try:
                # Remove previous region roles
                for r in REGIONS.values():
                    prev_role = guild.get_role(r["role_id"])
                    if prev_role in self.member.roles:
                        await self.member.remove_roles(prev_role)
                await self.member.add_roles(role)
                save_user_preferences(self.member.id, region=self.label)
                await interaction.response.send_message(f"✅ Region **{region_data['name']}** assigned!", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("⚠️ Bot cannot assign roles. Check permissions.", ephemeral=True)
                return

            # Proceed to zodiac selection
            try:
                await self.member.send("Choose your Zodiac sign:", view=OnboardingCog.ZodiacView(self.member))
            except discord.Forbidden:
                print(f"⚠️ Cannot DM {self.member.name} for zodiac selection.")

    class RegionView(discord.ui.View):
        def __init__(self, member, bot):
            super().__init__(timeout=300)
            for name, data in REGIONS.items():
                self.add_item(OnboardingCog.RegionButton(label=name, emoji=data["emoji"], member=member, bot=bot))

    # -----------------------
    # Zodiac Selection Buttons
    # -----------------------
    class ZodiacButton(discord.ui.Button):
        def __init__(self, label, emoji, member):
            super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.secondary)
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            save_user_preferences(self.member.id, zodiac=self.label)
            await interaction.response.send_message(f"✅ Zodiac **{self.label}** saved!", ephemeral=True)

            # Proceed to subscription selection
            try:
                await self.member.send("Do you want to receive daily reminders?", view=OnboardingCog.SubscriptionView(self.member))
            except discord.Forbidden:
                print(f"⚠️ Cannot DM {self.member.name} for subscription selection.")

    class ZodiacView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=300)
            for name, emoji in ZODIACS.items():
                self.add_item(OnboardingCog.ZodiacButton(label=name, emoji=emoji, member=member))

    # -----------------------
    # Subscription Selection Buttons
    # -----------------------
    class SubscriptionButton(discord.ui.Button):
        def __init__(self, label, member):
            super().__init__(label=label, style=discord.ButtonStyle.success if label=="Subscribe" else discord.ButtonStyle.danger)
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            status = self.label == "Subscribe"
            set_subscription(self.member.id, status)
            await interaction.response.send_message(f"✅ You have {'subscribed' if status else 'unsubscribed'} to daily reminders.", ephemeral=True)

    class SubscriptionView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=300)
            self.add_item(OnboardingCog.SubscriptionButton("Subscribe", member))
            self.add_item(OnboardingCog.SubscriptionButton("Unsubscribe", member))

    # -----------------------
    # Start Onboarding
    # -----------------------
    async def start_onboarding(self, member):
        try:
            dm = await member.create_dm()
            await dm.send("Welcome! Select your region:", view=self.RegionView(member, self.bot))
        except discord.Forbidden:
            print(f"⚠️ Cannot DM {member.name} to start onboarding.")

    # -----------------------
    # Events & Commands
    # -----------------------
    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.start_onboarding(member)

    @app_commands.command(name="onboard", description="Start onboarding manually")
    async def onboard(self, interaction: discord.Interaction):
        await self.start_onboarding(interaction.user)
        await interaction.response.send_message("✅ Check your DMs for onboarding!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
