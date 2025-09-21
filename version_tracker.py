# -----------------------
# GBPBot Version Tracker
# -----------------------
# Versioning follows: major.minor.patch.build
# Build increments with each deployment or hotfix

GBPBot_version = {
    "major": 1,
    "minor": 9,      # updated to reflect latest history
    "patch": 0,
    "build": 0,
    "date": "2025-09-21T12:00:00+01:00",  # BST
    "notes": (
        "v1.9.0.0 - Fully robust safe_send, daily flag handling, ephem.Moon fix, "
        "daily_loop updated, reminders and DB fully synced with version history."
    )
}

# -----------------------
# File Version Tracker
# -----------------------
file_versions = {
    "bot.py": "1.9.0.0",
    "db.py": "1.0.3b4",
    "cogs/commands.py": "1.9.0.0",
    "cogs/onboarding.py": "1.9.0.0",
    "cogs/reminders.py": "1.0.1b5",
    "utils/safe_send.py": "1.9.0.0",
    "version_tracker.py": "1.9.0.0"
}

def get_file_version(filename: str) -> str:
    """
    Returns the current version string for a given file.
    """
    return file_versions.get(filename, "unknown")
