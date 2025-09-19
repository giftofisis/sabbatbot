import discord
from discord.ext import commands
import traceback
from db import save_user_preferences, get_user_preferences
from utils.logger import robust_log

REGIONS = ["North America", "South America", "Europe", "Africa", "Oceania & Asia"]
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

class OnboardingDM:
    def __init__(self, bot, user):
        self.bot = bot
        self.user = user
        self.selected_region = None
        self.selected_zodiac = None

    async def start(self):
        try:
            dm_channel = self.user.dm_channel or await self.user.create_dm()
            await dm_channel.send("🚀 Welcome to onboarding! Let's get started. You can type `cancel` anytime to stop.")

            # Step 1: Select Region
            await self.select_region(dm_channel)

            # Step 2: Select Zodiac
            await self.select_zodiac(dm_channel)

            # Finish
            await dm_channel.send("🎉 Onboarding complete! Thank you for setting your preferences.")
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] Onboarding failed for user {self.user.id}\n{tb}")

    async def select_region(self, channel):
        options_text = "\n".join(f"{i+1}. {region}" for i, region in enumerate(REGIONS))
        await channel.send(f"Please select your **region** by typing the number:\n{options_text}")

        def check(m):
            return m.author == self.user and m.channel == channel

        while True:
            msg = await self.bot.wait_for("message", check=check)
            if msg.content.lower() == "cancel":
                await channel.send("❌ Onboarding cancelled.")
                raise Exception("User cancelled onboarding")
            if msg.content.isdigit() and 1 <= int(msg.content) <= len(REGIONS):
                self.selected_region = REGIONS[int(msg.content)-1]
                await save_user_preferences(self.user.id, region=self.selected_region, bot=self.bot)
                await channel.send(f"✅ Region set to **{self.selected_region}**.")
                break
            else:
                await channel.send("⚠️ Invalid selection. Please type the number corresponding to your region.")

    async def select_zodiac(self, channel):
        options_text = "\n".join(f"{i+1}. {zodiac}" for i, zodiac in enumerate(ZODIAC_SIGNS))
        await channel.send(f"Please select your **Zodiac sign** by typing the number:\n{options_text}")

        def check(m):
            return m.author == self.user and m.channel == channel

        while True:
            msg = await self.bot.wait_for("message", check=check)
            if msg.content.lower() == "cancel":
                await channel.send("❌ Onboarding cancelled.")
                raise Exception("User cancelled onboarding")
            if msg.content.isdigit() and 1 <= int(msg.content) <= len(ZODIAC_SIGNS):
                self.selected_zodiac = ZODIAC_SIGNS[int(msg.content)-1]
                await save_user_preferences(self.user.id, zodiac=self.selected_zodiac, bot=self.bot)
                await channel.send(f"✅ Zodiac set to **{self.selected_zodiac}**.")
                break
            else:
                await channel.send("⚠️ Invalid selection. Please type the number corresponding to your Zodiac sign.")


class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="onboard")
    async def onboard(self, ctx):
        try:
            await ctx.send("📬 Check your DMs! Starting onboarding...")
            onboarding = OnboardingDM(self.bot, ctx.author)
            await onboarding.start()
        except discord.Forbidden:
            await ctx.send("⚠️ I couldn't DM you. Please enable DMs from server members.")
        except Exception:
            tb = traceback.format_exc()
            await robust_log(self.bot, f"[ERROR] /onboard command failed for user {ctx.author.id}\n{tb}")
            await ctx.send("⚠️ Failed to start onboarding.")


async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
