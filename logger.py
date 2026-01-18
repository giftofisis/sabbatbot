# GBPBot - logger.py
# Version: 1.1.0
# Last Updated: 2026-01-18
# Notes:
# - Centralized logging utilities for GBPBot.
# - Provides robust_log function for consistent error/info logging across all cogs and bot events.
# - Logs to console and optionally to a Discord log channel (LOG_CHANNEL_ID from env).
# - Safe: never crashes if LOG_CHANNEL_ID is missing/invalid or if bot/channel isn't available.
# -----------------------
# CHANGE LOG
# -----------------------
# [2026-01-18] v1.1.0 - Read LOG_CHANNEL_ID from env (no hardcoding).
#                    - Support both error= and exc= args for backward compatibility.
#                    - Safer formatting and sending (won't crash if bot/channel missing).
# [2025-09-21] v1.0.0 - Initial creation with robust_log function for centralized logging.

import os
import traceback
from datetime import datetime


def _get_env(name: str):
    v = os.getenv(name)
    if v is None:
        return None
    v = v.strip()
    return v if v else None


def _get_log_channel_id():
    raw = _get_env("LOG_CHANNEL_ID")
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


async def robust_log(bot, message: str, error: Exception = None, exc: Exception = None):
    """
    Robust logging function:
    - Prints logs to console
    - Optionally sends logs to LOG_CHANNEL_ID (from env)
    - Includes traceback if an exception is provided

    Args:
        bot: discord.Client / commands.Bot (or None)
        message: log message
        error: optional exception (legacy param)
        exc: optional exception (preferred param)
    """
    # Prefer exc if provided, else fall back to error
    exception = exc or error

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp} UTC] {message}"

    if exception:
        # If we're inside an exception handler, format_exc() will include the active traceback.
        # Otherwise, we still show the exception string.
        tb = traceback.format_exc()
        if tb.strip() == "NoneType: None":
            tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        log_msg += f"\nException: {exception}\nTraceback:\n{tb}"

    print(log_msg)

    # Discord channel logging (optional)
    channel_id = _get_log_channel_id()
    if not channel_id or bot is None:
        return

    try:
        channel = bot.get_channel(channel_id)
        if channel is None:
            # Try fetching if cache misses (requires guild intents and permissions)
            try:
                channel = await bot.fetch_channel(channel_id)
            except Exception:
                channel = None

        if channel:
            # Prevent extremely long messages from failing
            payload = log_msg
            if len(payload) > 1900:
                payload = payload[:1900] + "\n...[truncated]"

            await channel.send(f"```{payload}```")

    except Exception as send_exc:
        print(f"[ERROR] Failed to send log to channel: {send_exc}")
