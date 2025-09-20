# -----------------------
# GBPBot Version Tracker
# -----------------------
# Versioning follows: major.minor.patch.build
# Build increments with each deployment or hotfix

GBPBot_version = {
    "major": 1,
    "minor": 2,
    "patch": 4,  # incremented due to fixes and improvements
    "build": 6,  # incremented for this deployment
    "date": "2025-09-20T12:50:00Z",
    "notes": (
        "v1.2.4.6 - Safe_send import fixed, onboarding flow fully robust, "
        "daily reminders loop fixed, version tracking added to all cogs."
    )
}

# -----------------------
# File Version Tracker
# -----------------------
file_versions = {
    "bot.py": "1.2.4.6",
    "db.py": "1.2.4.6",
    "cogs/commands.py": "1.2.4.6",
    "cogs/onboarding.py": "1.2.4.6",
    "cogs/reminders.py": "1.2.4.6",
    "utils/safe_send.py": "1.2.4.6"
}

def get_file_version(filename: str) -> str:
    """
    Returns the current version string for a given file.
    """
    return file_versions.get(filename, "unknown")
