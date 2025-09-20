# -----------------------
# GBPBot Version Info
# -----------------------
GBPBot_version = {
    "major": 1,
    "minor": 2,
    "patch": 3,
    "build": 5,  # increment on every build
    "date": "2025-09-19T09:05:00Z",
    "notes": "current build with fixed bot.py and cogs"
}

# -----------------------
# File Version Tracker
# -----------------------
file_versions = {
    "bot.py": "1.2.3.5",
    "commands.py": "1.0.0.0",
    "reminders.py": "1.0.0.0",
    "onboarding.py": "1.0.0.0",
    "db.py": "1.0.0.0"
}

# -----------------------
# Helper Functions
# -----------------------
def get_file_version(filename: str) -> str:
    """
    Returns the version string of the specified file.
    If the file is not tracked, returns "unknown".
    """
    return file_versions.get(filename, "unknown")


def increment_build():
    """
    Increments the build number of GBPBot_version.
    """
    GBPBot_version["build"] += 1
    from datetime import datetime
    GBPBot_version["date"] = datetime.utcnow().isoformat() + "Z"


def set_file_version(filename: str, version_str: str):
    """
    Updates the version for a specific file.
    """
    file_versions[filename] = version_str
