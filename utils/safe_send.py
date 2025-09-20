import traceback
from discord import Interaction
from utils.logger import robust_log

async def safe_send(user_or_interaction, content=None, embed=None, view=None, ephemeral=False):
    """
    Safely send a message to a user or interaction.
    - Handles None or finished views.
    - Handles interactions that may already have responded.
    - Logs all exceptions without crashing.
    """
    try:
        # Interaction handling
        if isinstance(user_or_interaction, Interaction):
            # Prevent passing a finished view
            if view is not None and getattr(view, "is_finished", lambda: False)():
                view = None

            if not user_or_interaction.response.is_done():
                # Interaction not responded yet
                await user_or_interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=ephemeral)
            else:
                # Already responded, use followup
                await user_or_interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
        else:
            # Direct DM or channel
            await user_or_interaction.send(content=content, embed=embed, view=view)
    except Exception as e:
        client_info = getattr(user_or_interaction, "client", None)
        await robust_log(client_info, f"[ERROR] Failed safe_send\nException: {e}\nTraceback:\n{traceback.format_exc()}")

# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-20 12:50] v1.0.1b1 - Removed deprecated 'MISSING' import from discord
# [2025-09-20 12:51] v1.0.1b2 - Updated function defaults to use None instead of MISSING
# [2025-09-20 12:52] v1.0.1b3 - Ensured compatibility with current discord.py Interaction typing
# [2025-09-20 12:53] v1.0.1b4 - Minor cleanups and removed unused imports
# [2025-09-20 13:10] v1.0.1b5 - Fixed AttributeError when view is None or finished
