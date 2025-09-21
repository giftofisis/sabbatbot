# GBPBot - utils/safe_send.py
# Version: 1.9.0.0
# Last Updated: 2025-09-21
# Notes:
# - Provides robust safe_send for users and interactions.
# - Handles None views and already-responded interactions.
# - Fully integrated with all cogs including reminders and onboarding.
# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-21 12:00 BST] v1.9.0.0 - Robust safe_send fully integrated across all cogs; fixed is_finished errors.


import traceback
from discord import Interaction
from utils.logger import robust_log

async def safe_send(user_or_interaction, content=None, embed=None, view=None, ephemeral=False):
    """
    Safely send a message to a user or interaction.
    Handles:
        - None views
        - Interactions that may have already responded
        - Logs all exceptions without crashing
    """
    try:
        # Interaction handling
        if isinstance(user_or_interaction, Interaction):
            try:
                # Use view if provided and not finished
                if view and not getattr(view, "is_finished", lambda: False)():
                    await user_or_interaction.response.send_message(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
                else:
                    await user_or_interaction.response.send_message(
                        content=content, embed=embed, ephemeral=ephemeral
                    )
            except Exception:
                # Fallback if already responded
                try:
                    await user_or_interaction.followup.send(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
                except Exception as e2:
                    await robust_log(
                        message=f"[safe_send] followup.send failed\nOriginal Exception: {traceback.format_exc()}\nFollowup Exception: {e2}"
                    )
        # DM to user
        else:
            if hasattr(user_or_interaction, "send"):
                await user_or_interaction.send(content=content, embed=embed, view=view)
            else:
                await robust_log(
                    message=f"[safe_send] Object has no send method: {user_or_interaction}"
                )
    except Exception as e:
        await robust_log(
            message=f"[safe_send] Failed send\nException: {e}\nTraceback:\n{traceback.format_exc()}"
        )


# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-20 11:45 BST] v1.2.4b1 - Initial safe_send integration for GBPBot cogs
# [2025-09-20 11:55 BST] v1.2.4b2 - Added followup.send fallback for already-responded interactions
# [2025-09-20 12:05 BST] v1.2.4b3 - Fixed view=None and AttributeError in interaction send
# [2025-09-20 12:30 BST] v1.2.4b4 - Fully robust, compatible with onboarding.py, commands.py, reminders.py, and updated logging
# [2025-09-20 12:45 BST] v1.2.4b5 - Fixed robust_log missing argument and ensured safe_send works with None view
# [2025-09-20 12:35 BST] v1.2.4b6 - Finalized fix for MISSING import, robust_log argument errors, and ensured full compatibility
