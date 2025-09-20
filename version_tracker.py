# -----------------------
# GBPBot Version Tracker
# -----------------------
# Versioning follows: major.minor.patch.build
# Build increments with each deployment or hotfix

GBPBot_version = {
    "major": 1,
    "minor": 2,
    "patch": 4,
    "build": 6,
    "date": "2025-09-20T12:50:00Z",
    "notes": (
        "v1.2.4.6 - safe_send import fixed, onboarding flow fully robust, "
        "daily reminders loop fixed, version tracking added to all cogs."
    )
}

# -----------------------
# File Version Tracker
# -----------------------
file_versions = {
    "bot.py": "1.2.4.6",
    "db.py": "1.0.0",
    "version_tracker.py": "1.0.0",
    "cogs/commands.py": "1.1.0b1",
    "cogs/onboarding.py": "1.0.1b2",
    "cogs/reminders.py": "1.0.1b2",
    "utils/safe_send.py": "1.2.4.6"
}

def get_file_version(filename: str) -> str:
    """
    Returns the current version string for a given file.
    """
    return file_versions.get(filename, "unknown")

# -----------------------
# Quick Reference Table
# -----------------------
"""
File Name               | Version     | Last Update (UTC / BST)
--------------------------------------------------------------
bot.py                  | 1.2.4.6     | 2025-09-20 12:50 UTC / 13:50 BST
db.py                   | 1.0.0       | v1.0.0 initial async-safe helpers
version_tracker.py      | 1.0.0       | 2025-09-20 12:50 UTC / 13:50 BST
cogs/commands.py        | 1.1.0b1     | 2025-09-20 13:10 UTC / 14:10 BST
cogs/onboarding.py      | 1.0.1b2     | 2025-09-20 12:55 UTC / 13:55 BST
cogs/reminders.py       | 1.0.1b2     | 2025-09-20 12:50 UTC / 13:50 BST
utils/safe_send.py      | 1.2.4.6     | 2025-09-20 12:50 UTC / 13:50 BST
"""

# -----------------------
# Detailed Changelog
# -----------------------
"""
GBPBot v1.2.4.6 Consolidated Changelog (times GMT/BST):

[onboarding.py]
- [2025-09-20 12:45 UTC / 13:45 BST] v1.0.0b1: Added version_tracker import, version comment, change tracking
- [2025-09-20 12:46 UTC / 13:46 BST]: Rewritten DM onboarding flow (Region → Zodiac → Daily reminders); uses safe_send; subscription saved in DB
- [2025-09-20 12:54 UTC / 13:54 BST] v1.0.1b1: Updated safe_send import for v1.0.1b4 compatibility
- [2025-09-20 12:55 UTC / 13:55 BST] v1.0.1b2: Confirmed button callbacks with view.stop()

[reminders.py]
- [2025-09-20 12:45 UTC / 13:45 BST] v1.0.0b1: Initial version with reminders, buttons, safe_send, robust logging
- [2025-09-20 12:50 UTC / 13:50 BST] v1.0.1b2: Updated safe_send calls for all buttons and daily loop; added Random Quote / Journal Prompt button

[commands.py]
- [2025-09-20 13:10 UTC / 14:10 BST] v1.1.0b1: All commands updated with safe_send, robust logging; /version shows file version

[version_tracker.py]
- [2025-09-20 12:50 UTC / 13:50 BST] v1.2.4.6: Centralized version tracking; safe_send import fixed; onboarding flow robust; daily reminders loop fixed; version tracking integrated

[db.py]
- [v1.0.0]: Added set_user_preferences, async-safe helpers, upsert logic, robust logging

[utils/safe_send.py]
- [v1.2.4.6]: Fixed NoneType.is_finished; safe sending to users/interactions; supports ephemeral messages, embeds, views; logs exceptions

[bot.py]
- [v1.2.4.6]: Safe cog loading; robust logging; daily reminder loop starts on_ready; DB init safe; version tracking added

Summary of Key Fixes:
1. safe_send fully fixed and integrated
2. Onboarding DM flow robust, cancel-safe, records daily subscriptions
3. Daily reminders loop fixed and timezone-aware
4. Interactive buttons functional and safe
5. All commands use safe_send; errors logged
6. Version tracking implemented for bot and files
7. Random quotes/journal prompts fetched safely
8. Robust logging across all interactions, tasks, and DB operations
"""
