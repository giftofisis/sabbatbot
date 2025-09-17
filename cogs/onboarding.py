import discord
from discord.ext import commands
from utils import REGIONS, ZODIACS, save_user_preferences

class OnboardingButton(discord.ui.Button):
    def __init__(self, label, emoji, member, key, is_zodiac=False):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
        self.member = member
        self.key = key
        self.is_zodiac = is_zodiac

    async def callback(self, interaction: discord.Interaction):
        if self.is_zodiac:
            save_user_preferences(self.member.id, zodiac=self.key)
            await interaction.response.send_message(f"✅ Zodiac set to **{self.key}**.", ephemeral=True)
        else:
            guild = interaction.guild or interaction.client.get_guild(interaction.guild_id)
            role = guild.get_role(REGIONS[self.key]["role_id"])
            # Remove previous roles
            for r in REGIONS.values():
                prev_role = guild.get_role(r["role_id"])
                if prev_role in self.member.roles:
                    await self.member.remove_roles(prev_role)
            await self.member.add_roles(role)
            save_user_preferences(self.member.id, region=self.key)
            await interaction.response.send_message(f"✅ Region set to **{REGIONS[self.key]['name']}**.", ephemeral=True)
        self.view.stop()

class OnboardingView(discord.ui.View):
    def __init__(self, member, options, is_zodiac=False):
        super().__init__(timeout=300)
        self.member = member
        for key, val in options.items() if not is_zodiac else {z:z for z in options}.items():
            self.add_item(OnboardingButton(label=val if is_zodiac else val["name"], emoji="" if is_zodiac else val["emoji"], member=member, key=key, is_zodiac=is_zodiac))

class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def start_onboarding(self, member):
        try:
            dm = await member.create_dm()
            embed = discord.Embed(title="Welcome! 🌙", description="Select your region:", color=0x9b59b6)
            await dm.send(embed=embed, view=OnboardingView(member, REGIONS))
            # After region, prompt zodiac
            embed2 = discord.Embed(title="Select your Zodiac", description="Choose your zodiac sign:", color=0x9b59b6)
            await dm.send(embed=embed2, view=OnboardingView(member, ZODIACS, is_zodiac=True))
        except Exception as e:
            print(f"Failed to DM {member}: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.start_onboarding(member)

    @discord.app_commands.command(name="onboard", description="Start onboarding manually")
    async def onboard(self, interaction: discord.Interaction):
        await self.start_onboarding(interaction.user)
        await interaction.response.send_message("✅ Check your DMs to complete onboarding!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Onboarding(bot))
