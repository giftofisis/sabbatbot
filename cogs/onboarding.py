import discord
from discord.ext import commands
from discord import app_commands
from .db import save_user_preferences

# -----------------------
# Regions & Zodiac
# -----------------------
REGIONS = {
    "NA": {"name": "North America", "role_id": 1416438886397251768, "emoji": "🇺🇸"},
    "SA": {"name": "South America", "role_id": 1416438925140164809, "emoji": "🌴"},
    "EU": {"name": "Europe", "role_id": 1416439011517534288, "emoji": "🍀"},
    "AF": {"name": "Africa", "role_id": 1416439116043649224, "emoji": "🌍"},
    "OC": {"name": "Oceania & Asia", "role_id": 1416439141339758773, "emoji": "🌺"},
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

    # -------------------
    # Region Buttons
    # -------------------
    class RegionButton(discord.ui.Button):
        def __init__(self, label, emoji, member, bot):
            super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
            self.member = member
            self.bot = bot

        async def callback(self, interaction: discord.Interaction):
            guild = self.bot.get_guild(interaction.guild_id)
            region_data = REGIONS[self.label]
            role = guild.get_role(region_data["role_id"])

            # Remove previous region roles
            for r in REGIONS.values():
                prev_role = guild.get_role(r["role_id"])
                if prev_role in self.member.roles:
                    await self.member.remove_roles(prev_role)

            await self.member.add_roles(role)
            save_user_preferences(self.member.id, region=self.label)

            await interaction.response.send_message(
                f"✅ Region **{region_data['name']}** assigned!", ephemeral=True
            )

            # Prompt zodiac selection
            try:
                dm = await self.member.create_dm()
                await dm.send("Choose your Zodiac sign:", view=OnboardingCog.ZodiacView(self.member))
            except discord.Forbidden:
                print(f"⚠️ Cannot DM {self.member}")

            self.view.stop()

    class RegionView(discord.ui.View):
        def __init__(self, member, bot):
            super().__init__(timeout=300)
            for key, data in REGIONS.items():
                self.add_item(OnboardingCog.RegionButton(label=key, emoji=data["emoji"], member=member, bot=bot))

    # -------------------
    # Zodiac Buttons
    # -------------------
    class ZodiacButton(discord.ui.Button):
        def __init__(self, label, emoji, member):
            super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.secondary)
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            save_user_preferences(self.member.id, zodiac=self.label)
            await interaction.response.send_message(
                f"✅ Zodiac **{self.label}** saved!", ephemeral=True
            )
            self.view.stop()

    class ZodiacView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=300)
            for name, emoji in ZODIACS.items():
                self.add_item(OnboardingCog.ZodiacButton(label=name, emoji=emoji, member=member))

    # -------------------
    # Start Onboarding
    # -------------------
    async def start_onboarding(self, member: discord.Member):
        try:
            dm = await member.create_dm()
            await dm.send("Welcome! Select your region:", view=OnboardingCog.RegionView(member, self.bot))
        except discord.Forbidden:
            print(f"⚠️ Cannot DM {member}")

    # -------------------
    # Auto Onboarding on Join
    # -------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.start_onboarding(member)

    # -------------------
    # Manual /onboard Command
    # -------------------
    @app_commands.command(name="onboard", description="Start onboarding manually")
    async def onboard(self, interaction: discord.Interaction):
        await self.start_onboarding(interaction.user)
        await interaction.response.send_message("✅ Check your DMs for onboarding!", ephemeral=True)

# -----------------------
# Setup
# -----------------------
async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
