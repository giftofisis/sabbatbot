import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from zoneinfo import ZoneInfo

# Import helpers from cogs.db
from .db import (
    get_user_preferences,
    set_subscription,
    add_quote,
    add_journal_prompt,
    get_all_quotes,
    get_all_journal_prompts,
)

# Import helpers from reminders
from .reminders import REGIONS, ReminderButtons, get_sabbat_dates, next_full_moon_for_tz, count_users_in_role


class CommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -----------------------
    # /reminder
    # -----------------------
    @app_commands.command(name="reminder", description="Get an interactive reminder")
    async def reminder(self, interaction: discord.Interaction):
        prefs = get_user_preferences(interaction.user.id)
        if not prefs or not prefs["subscribed"]:
            await interaction.response.send_message(
                "⚠️ You are not subscribed. Use `/onboard` to set your preferences.",
                ephemeral=True,
            )
            return

        region_data = REGIONS.get(prefs["region"])
        if not region_data:
            await interaction.response.send_message(
                "⚠️ Region not set. Please complete onboarding.", ephemeral=True
            )
            return

        emoji = region_data["emoji"]
        color = region_data["color"]
        tz = region_data["tz"]
        today = datetime.datetime.now(ZoneInfo(tz)).date()

        embed = discord.Embed(
            title=f"{emoji} Daily Reminder",
            description=(
                f"Good morning, {interaction.user.name}! 🌞\n"
                f"Today is **{today.strftime('%-d %B %Y')}**\n"
                f"Region: **{region_data['name']}** | Timezone: **{tz}**\n\n"
                f"💫 Quote: {random.choice(get_all_quotes())}\n"
                f"📝 Journal Prompt: {random.choice(get_all_journal_prompts())}"
            ),
            color=color,
        )

        await interaction.response.send_message(
            embed=embed, view=ReminderButtons(region_data)
        )

    # -----------------------
    # /submit_quote
    # -----------------------
    @app_commands.command(name="submit_quote", description="Submit an inspirational quote")
    async def submit_quote(self, interaction: discord.Interaction, quote: str):
        add_quote(quote)
        await interaction.response.send_message(
            "✅ Quote submitted successfully.", ephemeral=True
        )

    # -----------------------
    # /submit_journal
    # -----------------------
    @app_commands.command(name="submit_journal", description="Submit a journal prompt")
    async def submit_journal(self, interaction: discord.Interaction, prompt: str):
        add_journal_prompt(prompt)
        await interaction.response.send_message(
            "✅ Journal prompt submitted successfully.", ephemeral=True
        )

    # -----------------------
    # /unsubscribe
    # -----------------------
    @app_commands.command(name="unsubscribe", description="Stop receiving daily reminders")
    async def unsubscribe(self, interaction: discord.Interaction):
        set_subscription(interaction.user.id, False)
        await interaction.response.send_message(
            "❌ You have unsubscribed from daily reminders.", ephemeral=True
        )

    # -----------------------
    # /status
    # -----------------------
    @app_commands.command(name="status", description="Shows bot status and upcoming events")
    async def status(self, interaction: discord.Interaction):
        now = datetime.datetime.now(datetime.timezone.utc)
        embed = discord.Embed(title="🌙 Bot Status", color=0x1abc9c)
        embed.add_field(
            name="Current UTC Time",
            value=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            inline=False,
        )

        guild = interaction.guild
        for data in REGIONS.values():
            tz = ZoneInfo(data["tz"])
            today = datetime.datetime.now(tz).date()
            sabbats = get_sabbat_dates(today.year)
            upcoming_sabbat = min((d for d in sabbats.values() if d >= today), default=None)
            next_moon = next_full_moon_for_tz(data["tz"])
            users_count = count_users_in_role(guild, data["role_id"])

            embed.add_field(
                name=f"{data['emoji']} {data['name']} ({data['tz']})",
                value=(
                    f"Next Sabbat: {upcoming_sabbat.strftime('%-d %B %Y') if upcoming_sabbat else 'N/A'}\n"
                    f"Next Full Moon: {next_moon.strftime('%-d %B %Y') if next_moon else 'N/A'}\n"
                    f"Users in region: {users_count}"
                ),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    # -----------------------
    # /help
    # -----------------------
    @app_commands.command(name="help", description="Shows all available commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🌙 Bot Help", color=0x9b59b6)
        embed.add_field(
            name="/onboard",
            value="Start onboarding to select region, zodiac, and reminders.",
            inline=False,
        )
        embed.add_field(
            name="/reminder",
            value="Receive your daily interactive reminder immediately.",
            inline=False,
        )
        embed.add_field(
            name="/status",
            value="Show bot status, next Sabbat, full moon, and user counts.",
            inline=False,
        )
        embed.add_field(
            name="/submit_quote <text>",
            value="Submit an inspirational quote for reminders.",
            inline=False,
        )
        embed.add_field(
            name="/submit_journal <text>",
            value="Submit a journal prompt for daily reminders.",
            inline=False,
        )
        embed.add_field(
            name="/unsubscribe",
            value="Stop receiving daily DM reminders.",
            inline=False,
        )

        # safer: respond in-channel + DM
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message(
                "✅ Help sent to your DMs.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=embed, ephemeral=True
            )

    # -----------------------
    # /test
    # -----------------------
    @app_commands.command(name="test", description="Test your daily reminder and list all commands")
    async def test_command(self, interaction: discord.Interaction):
        prefs = get_user_preferences(interaction.user.id)
        if not prefs:
            await interaction.response.send_message(
                "⚠️ You need to complete onboarding first.", ephemeral=True
            )
            return

        cog = self.bot.get_cog("RemindersCog")
        if cog:
            await cog.send_daily_reminder(interaction.user.id, prefs)

        commands_list = [cmd.name for cmd in self.bot.tree.walk_commands()]
        commands_text = ", ".join(commands_list)
        await interaction.followup.send(
            f"✅ All commands are available: {commands_text}", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(CommandsCog(bot))
