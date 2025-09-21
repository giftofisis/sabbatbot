# GBPBot - MASTER CHANGE LOG
# -----------------------
# [2025-09-21 16:10 BST] v1.9.2.0
# - Onboarding.py fully synced to use constants.py for REGIONS and ZODIAC_SIGNS.
# - Reminders.py synced to constants.py, uses shared region data for emoji, tz, and color.
# - Daily loop respects 'daily' flag and unpacking now compatible with DB.
# - All emoji usage in onboarding and reminders standardized.
# - Version_tracker.py updated to reflect latest core file versions (v1.0.3).

# [2025-09-21 15:45 BST] v1.9.1.0
# - Added emojis to all onboarding buttons.

# [2025-09-21 12:00 BST] v1.9.0.0
# - Fully integrated safe_send, cancel support, and daily preference handling in onboarding.

# [2025-09-21 11:42 BST] v1.0.1b5 (reminders.py)
# - Updated daily_loop to use 'daily' flag from DB and unpack correct values.

# [2025-09-21 10:40 BST] v1.0.1b5 (reminders.py)
# - Synced with db.py changes: reminders loop now unpacks 6 values including 'daily' flag and respects prefs["daily"].

# [2025-09-21 15:00 BST] v1.0.2 (version_tracker.py)
# - Added 'constants.py' to file version tracking.

# [2025-09-21 14:30 BST] v1.0.0 (constants.py)
# - Initial creation with regions, zodiac signs, emojis, and sabbats.

# [2025-09-20 14:25 BST] v1.0.2b4 (onboarding.py)
# - Added logging of completed onboardings to central LOG_CHANNEL_ID

# [2025-09-20 14:10 BST] v1.0.2b3 (onboarding.py)
# - Fixed cancel buttons to be async callbacks to prevent TypeError

# [2025-09-20 13:55 BST] v1.0.2b2 (onboarding.py)
# - Added cancel support for all steps and centralized logging

# [2025-09-20 13:50 BST] v1.0.2b1 (onboarding.py)
# - Updated to modern button callbacks and robust safe_send for NoneType is_finished fix

# [2025-09-20 13:25 BST] v1.0.1b4 (reminders.py)
# - Fixed ephem.Moon input type, ensured view=None in all safe_send calls

# [2025-09-20 13:12 BST] v1.0.1b3 (reminders.py)
# - Fully integrated robust safe_send fix for NoneType is_finished errors in all sends

# [2025-09-20 12:50 BST] v1.0.1b2 (reminders.py)
# - Updated safe_send calls and logging for all buttons and daily loop

# [2025-09-20 12:45 BST] v1.0.0b1 (reminders.py)
# - Initial version with reminders, buttons, safe_send, and robust logging

# [2025-09-20 12:10 BST] v1.8.0.0 (onboarding.py)
# - Initial robust DM onboarding flow with emoji buttons and region/zodiac/reminder selection

# [2025-09-20 12:50 BST] v1.0.0 (version_tracker.py)
# - Initial creation of version_tracker.py for onboarding, reminders, db, commands, and bot.py
