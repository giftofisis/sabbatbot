import traceback
from datetime import datetime

LOG_CHANNEL_ID = 1418171996583366727  # your logging channel ID

async def robust_log(bot, message: str, error: Exception = None):
    """
    Robust logging function:
    - Prints logs to console
    - Sends logs to LOG_CHANNEL_ID
    - Includes exception traceback if provided
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp} UTC] {message}"
    if error:
        log_msg += f"\nException: {error}\nTraceback:\n{traceback.format_exc()}"
    print(log_msg)
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        try:
            await channel.send(f"```{log_msg}```")
        except Exception as e:
            print(f"[ERROR] Failed to send log to channel: {e}")
