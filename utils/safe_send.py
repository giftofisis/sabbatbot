# utils/safe_send.py
# Version: 1.2.4 build 6
# Last Updated: 2025-09-20T12:35:00+01:00 (BST)
# Notes: Fully robust safe_send for GBPBot
#        - Handles view=None safely
#        - Uses getattr to prevent AttributeError
#        - Interaction fallback to followup.send
#        - Robust logging with single message
#        - Compatible with all cogs (onboarding, commands, reminders)

import traceback
from discord import Interaction, MISSING
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
        # Interaction
        if isinstance(user_or_interaction, Interaction):
            try:
                if view and not getattr(view, "is_finished", lambda: False)():
                    await user_or_interaction.response.send_message(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
                else:
                    await user_or_interaction.response.send_message(
                        content=content, embed=embed, ephemeral=ephemeral
                    )
            except Exception:
                # fallback to followup
                try:
                    await user_or_interaction.followup.send(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
                except Exception as e2:
                    await robust_log(
                        f"[safe_send] followup.send failed\nOriginal Exception: {traceback.format_exc()}\nFollowup Exception: {e2}"
                    )
        # DM to user
        else:
            if hasattr(user_or_interaction, "send"):
                await user_or_interaction.send(content=content, embed=embed, view=view)
            else:
                await robust_log(f"[safe_send] Object has no send method: {user_or_interaction}")
    except Exception as e:
        await robust_log(f"[safe_send] Failed send\nException: {e}\nTraceback:\n{traceback.format_exc()}")


# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-20 11:45 GMT] v1.2.4b1 - Initial safe_send integration for GBPBot cogs
# [2025-09-20 11:55 GMT] v1.2.4b2 - Added followup.send fallback for already-responded interactions
# [2025-09-20 12:05 GMT] v1.2.4b3 - Fixed view=None and AttributeError in interaction send
# [2025-09-20 12:30 GMT] v1.2.4b4 - Fully robust, compatible with onboarding.py, commands.py, reminders.py, and updated logging 
# [2025-09-20 12:45 GMT] v1.2.4b5 - Fixed robust_log missing argument and ensured safe_send works with None view
