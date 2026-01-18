# GBPBot - safe_send.py
# Version: 1.9.1.0
# Last Updated: 2026-01-18
# Notes:
# - Flat-structure refactor of utils/safe_send.py -> safe_send.py
# - Uses logger.robust_log (flat import)
# - Handles already-responded interactions safely (response -> followup fallback)
# - Allows optional bot= for reliable log channel posting
# -----------------------
# CHANGE LOG
# -----------------------
# [2026-01-18] v1.9.1.0 - Flat-structure import changes + fixed robust_log call signature.
#                      - Added optional bot= passthrough and interaction.client fallback.
# [2025-09-21] v1.9.0.0 - Robust safe_send fully integrated across all cogs; fixed is_finished errors.

import traceback
import discord
from discord import Interaction

from logger import robust_log


async def safe_send(
    target,
    content=None,
    embed=None,
    view=None,
    ephemeral: bool = False,
    bot=None
):
    """
    Safely send a message to a user/channel or interaction.

    Supports:
      - discord.Interaction (response -> followup fallback if already responded)
      - discord.abc.Messageable objects (User/Member/TextChannel/Thread/etc)
      - view may be None

    Args:
        target: Interaction OR any object with .send()
        content: message content
        embed: discord.Embed
        view: discord.ui.View
        ephemeral: only applies to interactions
        bot: optional commands.Bot/client for robust_log channel posting
    """
    try:
        # Interaction handling
        if isinstance(target, Interaction):
            # Prefer a bot reference for logging
            if bot is None:
                bot = getattr(target, "client", None)

            try:
                await target.response.send_message(
                    content=content,
                    embed=embed,
                    view=view,
                    ephemeral=ephemeral
                )
                return
            except Exception:
                # If already responded or response failed, try followup
                try:
                    await target.followup.send(
                        content=content,
                        embed=embed,
                        view=view,
                        ephemeral=ephemeral
                    )
                    return
                except Exception as e2:
                    await robust_log(
                        bot,
                        "[safe_send] followup.send failed",
                        exc=e2
                    )
                    return

        # Non-interaction: DM/channel/etc
        if hasattr(target, "send"):
            await target.send(content=content, embed=embed, view=view)
            return

        # Unknown target
        await robust_log(
            bot,
            f"[safe_send] Target has no send() method: {target!r}"
        )

    except Exception as e:
        await robust_log(
            bot,
            f"[safe_send] Failed send: {e}",
            exc=e
        )
