# safe_send.py
"""
GBPBot Safe Send Utility
-----------------------
Handles sending messages to users or interactions safely.
- Works for DMs and interactions.
- Handles views that may be finished or None.
- Avoids 'This interaction failed' errors.
- Logs all exceptions via robust_log.
"""

import traceback
import discord
from utils.logger import robust_log

# -----------------------
# Changelog
# -----------------------
# 2025-09-20: Initial robust safe_send for GBPBot
# 2025-09-20: Added interaction response lifecycle handling
# 2025-09-20: Added view None/type check to fix 'NoneType is_finished' error
# 2025-09-20: Logs all exceptions without crashing bot

async def safe_send(user_or_interaction, content=None, embed=None, view=None, ephemeral=False):
    try:
        # Handle discord.Interaction
        if isinstance(user_or_interaction, discord.Interaction):
            # Check if interaction has already responded
            responded = False
            try:
                responded = user_or_interaction.response.is_done()
            except Exception:
                # Fallback in case is_done fails
                responded = False

            # Ensure view is valid
            if view is not None and getattr(view, "is_finished", None):
                if view.is_finished():
                    view = None

            # Send message safely
            if not responded:
                await user_or_interaction.response.send_message(
                    content=content, embed=embed, view=view, ephemeral=ephemeral
                )
            else:
                # Follow-up if already responded
                await user_or_interaction.followup.send(
                    content=content, embed=embed, view=view, ephemeral=ephemeral
                )

        # Handle discord.User or discord.Member
        else:
            await user_or_interaction.send(content=content, embed=embed, view=view)

    except Exception as e:
        robust_log(
            f"Failed safe_send\nException: {e}\nTraceback:\n{traceback.format_exc()}"
        )
