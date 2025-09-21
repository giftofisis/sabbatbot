# GBPBot - version_tracker.py
# Version: 1.0.2
# Last Updated: 2025-09-21
# Notes:
# - Centralized file version tracking for GBPBot.
# - Can be imported by cogs and utils to get the version of any core file.
# - Updated to reflect latest onboarding.py, reminders.py, and constants.py versions.
# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-21 15:45 BST] v1.0.2 - Updated versions for onboarding.py (1.9.1.0), reminders.py (1.0.1b5), and constants.py (1.0.0)
# [2025-09-21 15:00 BST] v1.0.1 - Added 'constants.py' to file version tracking.
# [2025-09-20 12:50 BST] v1.0.0 - Initial creation of version_tracker.py for onboarding, reminders, db, commands, and bot.py

# Core file versions
GBPBot_version = "1.9.2.0"

FILE_VERSIONS = {
    "bot.py": "1.9.0.0",
    "db.py": "1.0.3 build 1",
    "onboarding.py": "1.9.1.0",
    "reminders.py": "1.0.1b5",
    "commands.py": "1.0.2",
    "constants.py": "1.0.0"
}

def get_file_version(filename: str) -> str:
    """
    Returns the current version of a core GBPBot file.
    If file is not listed, returns 'Unknown'.
    """
    return FILE_VERSIONS.get(filename, "Unknown")
