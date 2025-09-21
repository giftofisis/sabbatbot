# GBPBot - version_tracker.py
# Version: 1.0.5
# Last Updated: 2025-09-21
# Notes:
# - Centralized file version tracking for GBPBot.
# - Can be imported by cogs and utils to get the version of any core file.
# - Updated to include logger.py and hemisphere-aware sabbat reminders.
# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-21] v1.0.5 - Added logger.py to file version tracking; current version "1.0.0".
# [2025-09-21] v1.0.4 - Updated reminders.py to v1.10.0 (hemisphere-aware sabbat reminders); constants.py to v1.0.1 (added hemisphere field and SABBATS_HEMISPHERES)
# [2025-09-21] v1.0.3 - Updated onboarding.py and reminders.py to v1.9.2.0; master GBPBot_version 1.9.2.0
# [2025-09-21] v1.0.2 - Updated versions for onboarding.py (1.9.1.0), reminders.py (1.0.1b5), and constants.py (1.0.0)
# [2025-09-21] v1.0.1 - Added 'constants.py' to file version tracking.
# [2025-09-20] v1.0.0 - Initial creation of version_tracker.py for onboarding, reminders, db, commands, and bot.py

# Core file versions
GBPBot_version = "1.10.0"

FILE_VERSIONS = {
    "bot.py": "1.9.2.0",
    "db.py": "1.0.3b4",
    "onboarding.py": "1.9.2.1",
    "reminders.py": "1.10.0",
    "commands.py": "1.9.0.0",
    "constants.py": "1.0.1",
    "safe_send.py": "1.9.0.0",
    "logger.py": "1.0.0"
}

# Alias for backward compatibility
file_versions = FILE_VERSIONS

def get_file_version(filename: str) -> str:
    """
    Returns the current version of a core GBPBot file.
    If file is not listed, returns 'Unknown'.
    """
    return FILE_VERSIONS.get(filename, "Unknown")
