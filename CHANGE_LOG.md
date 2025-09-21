# GBPBot - MASTER CHANGE LOG
# -----------------------
# [2025-09-21] v1.10.0
# - Reminders.py updated to hemisphere-aware sabbat reminders; SABBATS_HEMISPHERES used for north/south hemispheres.
# - Constants.py updated to add 'hemisphere' field for regions and SABBATS_HEMISPHERES.
# - Version_tracker.py updated to reflect logger.py inclusion and hemisphere-aware sabbat reminders.
# - GBPBot_version updated to 1.10.0.

# [2025-09-21] v1.9.2.1
# - Onboarding.py: Fixed loop variable capture for buttons; emojis now display correctly.
# - Fully robust DM onboarding flow; safe_send prevents is_finished errors; daily preference synced.

# [2025-09-21] v1.9.2.0
# - Onboarding.py fully synced to use constants.py for REGIONS and ZODIAC_SIGNS.
# - Reminders.py synced to constants.py; uses shared region data for emoji, tz, color.
# - Daily loop respects 'daily' flag and unpacking now compatible with DB.
# - All emoji usage in onboarding and reminders standardized.
# - Version_tracker.py updated to reflect latest core file versions.

# [2025-09-21] v1.9.1.0
# - Added emojis to all onboarding buttons.

# [2025-09-21] v1.9.0.0
# - Fully integrated safe_send, cancel support, and daily preference handling in onboarding.

# [2025-09-21] v1.0.1b5
# - Reminders.py: Daily loop updated to use 'daily' flag from DB and unpack correct values.

# [2025-09-21] v1.0.2
# - Version_tracker.py: Added 'constants.py' to file version tracking.

# [2025-09-21] v1.0.0
# - Initial creation of core files and version tracking.
