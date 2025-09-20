import traceback
from discord import MISSING
from utils.logger import robust_log

async def safe_send(user_or_interaction, content=None, embed=None, view=None, ephemeral=False):
    """
    Safely send a message to a user or interaction.
    - Handles None views.
    - Handles interactions that may already have responded.
    - Logs all exceptions without crashing.
    """
    try:
        # Check if the interaction has a response available
        if hasattr(user_or_interaction, "response") and user_or_interaction.response:
            # Only use the view if it exists and is not finished
            if view is not None and not view.is_finished():
                await user_or_interaction.response.send_message(
                    content=content, embed=embed, view=view, ephemeral=ephemeral
                )
            else:
                await user_or_interaction.response.send_message(
                    content=content, embed=embed, ephemeral=ephemeral
                )
        else:
            # fallback to sending directly to user (DM) or any messageable
            await user_or_interaction.send(content=content, embed=embed, view=view)
    except Exception as e:
        robust_log(f"Failed safe_send\nException: {e}\nTraceback:\n{traceback.format_exc()}")#endline28
