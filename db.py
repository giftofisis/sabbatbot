# -----------------------
# Clear User Preferences
# -----------------------
async def clear_user_preferences(user_id: int, bot=None) -> None:
    """
    Deletes a user's preferences from the DB.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        if bot:
            await robust_log(bot, f"✅ Cleared preferences for user {user_id}.")
    except Exception as e:
        if bot:
            await robust_log(bot, f"❌ Failed to clear preferences for {user_id}: {e}", exc=traceback.format_exc())
        else:
            print(f"Clear user prefs error: {e}\n{traceback.format_exc()}")
    finally:
        conn.close()
