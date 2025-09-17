import discord
from discord.ext import commands
from utils import get_user_preferences, REGIONS, format_date, next_full_moon_for_tz, get_sabbat_dates, moon_phase_emoji, get_all_quotes, get_all_journal_prompts, add_quote, add_journal_prompt, set_subscription
from cogs.reminders import ReminderButtons
import datetime
from zoneinfo import ZoneInfo
import random

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="reminder", description="Get interactive reminder")
    async def reminder(self, interaction: discord.Interaction):
        prefs = get_user_preferences(interaction.user.id)
        if not prefs or not prefs["subscribed"]:
            await interaction.response.send_message("⚠️ Not subscribed.", ephemeral=True)
            return
        region_data = REGIONS.get(prefs["region"])
        tz = ZoneInfo(region_data["tz"])
        today = datetime.datetime.now(tz).date()
        embed = discord.Embed(
            title=f"{region_data['emoji']} Daily Reminder",
            description=f"Good morning, {interaction.user.name}!\nToday is **{format_date(today)}**\n💫 Quote: {random.choice(get_all_quotes())}\n📝 Journal Prompt: {random.choice(get_all_journal_prompts())}",
            color=region_data["color"]
        )
        await interaction.response.send_message(embed=embed, view=ReminderButtons(region_data))

    @discord.app_commands.command(name="status", description="Show bot status")
    async def status(self, interaction: discord.Interaction):
        now = datetime.datetime.now(datetime.timezone.utc)
        embed = discord.Embed(title="🌙 Bot Status", color=0x1abc9c)
        embed.add_field(name="Current UTC Time", value=now.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
        for data in REGIONS.values():
            tz = ZoneInfo(data["tz"])
            today = datetime.datetime.now(tz).date()
            sabbats = get_sabbat_dates(today.year)
            next_sabbat = min((d for d in sabbats.values() if d>=today), default=None)
            next_moon = next_full_moon_for_tz(data["tz"])
            embed.add_field(name=f"{data['emoji']} {data['name']}", value=f"Next Sabbat: {format_date(next_sabbat)}\nNext Full Moon: {format_date(next_moon)}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="submit_quote", description="Submit a quote")
    async def submit_quote(self, interaction: discord.Interaction, quote: str):
        add_quote(quote)
        await interaction.response.send_message("✅ Quote submitted", ephemeral=True)

    @discord.app_commands.command(name="submit_journal", description="Submit a journal prompt")
    async def submit_journal(self, interaction: discord.Interaction, prompt: str):
        add_journal_prompt(prompt)
        await interaction.response.send_message("✅ Journal prompt submitted", ephemeral=True)

    @discord.app_commands.command(name="unsubscribe", description="Stop daily reminders")
    async def unsubscribe(self, interaction: discord.Interaction):
        set_subscription(interaction.user.id, False)
        await interaction.response.send_message("❌ Unsubscribed from daily reminders", ephemeral=True)

    @discord.app_commands.command(name="help", description="Show all commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🌙 Bot Help", color=0x9b59b6)
        embed.add_field(name="/onboard", value="Start onboarding", inline=False)
        embed.add_field(name="/reminder", value="Get interactive reminder", inline=False)
        embed.add_field(name="/status", value="Show bot status", inline=False)
        embed.add_field(name="/submit_quote", value="Submit inspirational quote", inline=False)
        embed.add_field(name="/submit_journal", value="Submit journal prompt", inline=False)
        embed.add_field(name="/unsubscribe", value="Stop daily reminders", inline=False)
        await interaction.user.send(embed=embed)
        await interaction.response.send_message("✅ Help sent to your DMs", ephemeral=True)

    @discord.app_commands.command(name="test", description="Test all features")
    async def test(self, interaction: discord.Interaction):
        prefs = get_user_preferences(interaction.user.id)
        if prefs:
            region_data = REGIONS.get(prefs["region"])
            embed = discord.Embed(title="🧪 Test Reminder", description=f"Good morning, {interaction.user.name}!\n💫 Quote: {random.choice(get_all_quotes())}\n📝 Journal Prompt: {random.choice(get_all_journal_prompts())}", color=region_data["color"])
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Complete onboarding first.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Commands(bot))
