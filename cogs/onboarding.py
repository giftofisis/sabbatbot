import os
import discord
from discord.ext import commands
from discord import app_commands
from cogs.db import save_user_preferences

GUILD_ID = int(os.getenv("GUILD_ID"))

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

class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class RegionButton(discord.ui.Button):
        def __init__(self, label, emoji, member, bot):
            super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
            self.member = member
            self.bot = bot

        async def callback(self, interaction: discord.Interaction):
            # Use known GUILD_ID to get the guild object even from DMs
            guild = self.bot.get_guild(GUILD_ID)
            if guild is None:
                await interaction.response.send_message("❌ Guild not found. Contact an admin.", ephemeral=True)
                return

            region_data = REGIONS[self.label]
            role = guild.get_role(region_data["role_id"])
            if role is None:
                await interaction.response.send_message("❌ Role not found on the server. Contact an admin.", ephemeral=True)
                return

            # Remove previous region roles (if present)
            remove_roles = []
            for r in REGIONS.values():
                prev_role = guild.get_role(r["role_id"])
                if prev_role and prev_role in self.member.roles:
                    remove_roles.append(prev_role)
            if remove_roles:
                try:
                    await self.member.remove_roles(*remove_roles)
                except Exception as e:
                    print(f"Failed to remove old region roles for {self.member}: {e}")

            try:
                await self.member.add_roles(role)
            except Exception as e:
                print(f"Failed to add role {role} to {self.member}: {e}")
                await interaction.response.send_message("❌ Failed to assign role. Contact an admin.", ephemeral=True)
                return

            # Save region (preserve other prefs)
            save_user_preferences(self.member.id, region=self.label)

            await interaction.response.send_message(f"✅ Region **{region_data['name']}** assigned!", ephemeral=True)

            # Prompt zodiac selection via DM
            try:
                await self.member.send("Choose your Zodiac sign:", view=OnboardingCog.ZodiacView(self.member))
            except discord.Forbidden:
                print(f"⚠️ Cannot DM {self.member} for zodiac selection.")

            self.view.stop()

    class RegionView(discord.ui.View):
        def __init__(self, member, bot):
            super().__init__(timeout=300)
            for key, data in REGIONS.items():
                self.add_item(OnboardingCog.RegionButton(label=key, emoji=data["emoji"], member=member, bot=bot))

    class ZodiacButton(discord.ui.Button):
        def __init__(self, label, emoji, member):
            super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.secondary)
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            save_user_preferences(self.member.id, zodiac=self.label)
            await interaction.response.send_message(f"✅ Zodiac **{self.label}** saved!", ephemeral=True)
            self.view.stop()

    class ZodiacView(discord.ui.View):
        def __init__(self, member):
            super().__init__(timeout=300)
            for name, emoji in ZODIACS.items():
                self.add_item(OnboardingCog.ZodiacButton(label=name, emoji=emoji, member=member))

    async def start_onboarding(self, member: discord.Member):
        try:
            await member.send("Welcome! Select your region:", view=OnboardingCog.RegionView(member, self.bot))
        except discord.Forbidden:
            print(f"⚠️ Cannot DM {member} for onboarding.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # auto-run onboarding for members who join the guild with GUILD_ID
        if member is None:
            return
        # Only trigger if member joined the target guild
        guild = self.bot.get_guild(GUILD_ID)
        if guild and guild.get_member(member.id):
            await self.start_onboarding(member)

    @app_commands.command(name="onboard", description="Start onboarding manually")
    async def onboard(self, interaction: discord.Interaction):
        await self.start_onboarding(interaction.user)
        await interaction.response.send_message("✅ Check your DMs for onboarding!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
