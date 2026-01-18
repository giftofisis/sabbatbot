# GBPBot - version_tracker.py
# Version: 1.0.9
# Last Updated: 2026-01-18
# Notes:
# - Centralized file version tracking for GBPBot.
# - Backward-compatible aliases included (VERSIONS, file_versions).
# - Flat-structure friendly: tracks the core .py files expected in the main directory.
# -----------------------
# CHANGE LOG
# -----------------------
# [2026-01-18] v1.0.9
# - Updated tracked versions for db.py (1.0.5.0) and commands.py (1.9.4.0) for /profile edit buttons + set_daily helper.
# [2026-01-18] v1.0.8
# - Flat-structure alignment: updated bot.py version and trimmed tracking to core flat-directory files.
# [2026-01-18] v1.0.7
# - Updated tracked version for commands.py to 1.9.3.0 (added /profile DM-only command and admin-only restrictions).
# [2026-01-18] v1.0.6
# - Updated tracked versions for bot.py/db.py/reminders.py/logger.py/commands.py based on Discloud + compatibility fixes.
# - Added `VERSIONS` alias to prevent ImportError in older code paths.
# [2025-09-20] v1.0.0 - Initial creation of version_tracker.py for onboarding, reminders, db, commands, and bot.py

# Master version (overall bot release)
GBPBot_version = "1.10.1"

# Core files expected in the flat (single-directory) Discloud layout
FILE_VERSIONS = {
    "bot.py": "1.9.5.1",
    "db.py": "1.0.5.0",
    "onboarding.py": "1.9.2.1",
    "reminders.py": "1.10.1",
    "commands.py": "1.9.4.0",
    "logger.py": "1.1.0",
    "version_tracker.py": "1.0.9",
}

# Aliases for backward compatibility (older code may import these names)
file_versions = FILE_VERSIONS
VERSIONS = FILE_VERSIONS


def get_file_version(filename: str) -> str:
    """
    Returns the current version of a core GBPBot file.
    If file is not listed, returns 'Unknown'.
    """
    return FILE_VERSIONS.get(filename, "Unknown")
