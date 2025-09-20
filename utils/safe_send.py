import traceback
from discord import MISSING, Interaction
from utils.logger import robust_log

async def safe_send(user_or_interaction, content=None, embed=None, view=None, ephemeral=False):
    """
    Safely send a message to a user or interaction.
    - Handles None views.
    - Handles interactions that may already have responded.
    - Logs all exceptions without crashing.
    """
    try:
        # Interaction handling
        if isinstance(user_or_interaction, Interaction):
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
        await robust_log(client_info, f"[ERROR] Failed safe_send\nException: {e}\nTraceback:\n{traceback.format_exc()}")  #endline26
