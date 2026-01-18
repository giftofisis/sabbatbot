# GBPBot - constants.py
# Version: 1.0.2
# Last Updated: 2026-01-18
# Notes:
# - Centralized constants for regions, zodiac signs, emojis, and other shared references.
# - Includes hemisphere support for sabbat reminders.
# - Adds "name" field inside each region for consistent display usage across cogs.
# -----------------------
# CHANGE LOG
# -----------------------
# [2026-01-18] v1.0.2 - Added "name" field to each region entry (prevents KeyError in reminder buttons/embeds).
# [2025-09-21] v1.0.1 - Fixed missing commas in REGIONS, added hemisphere field for all regions.
# [2025-09-21] v1.0.0 - Initial creation of constants.py with regions, zodiac signs, emojis, and related references.

# -----------------------
# Regions
# -----------------------
REGIONS = {
    "North America": {
        "name": "North America",
        "emoji": "🗽",
        "tz": "America/New_York",
        "role_id": 1416438886397251768,
        "color": 0x2ecc71,
        "hemisphere": "north"
    },
    "South America": {
        "name": "South America",
        "emoji": "🌴",
        "tz": "America/Sao_Paulo",
        "role_id": 1416438925140164809,
        "color": 0xe67e22,
        "hemisphere": "south"
    },
    "Europe": {
        "name": "Europe",
        "emoji": "🍀",
        "tz": "Europe/London",
        "role_id": 1416439011517534288,
        "color": 0x3498db,
        "hemisphere": "north"
    },
    "Africa": {
        "name": "Africa",
        "emoji": "🌍",
        "tz": "Africa/Johannesburg",
        "role_id": 1416439116043649224,
        "color": 0xf1c40f,
        "hemisphere": "south"
    },
    "Oceania & Asia": {
        "name": "Oceania & Asia",
        "emoji": "🌺",
        "tz": "Australia/Sydney",
        "role_id": 1416439141339758773,
        "color": 0x9b59b6,
        "hemisphere": "south"
    }
}

# Quick access dict for onboarding buttons (label -> emoji)
REGION_EMOJIS = {name: data["emoji"] for name, data in REGIONS.items()}

# -----------------------
# Zodiac Signs
# -----------------------
ZODIAC_SIGNS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
}

# -----------------------
# Sabbats
# -----------------------
SABBATS_HEMISPHERES = {
    "north": {
        "Yule": (12, 21),
        "Imbolc": (2, 1),
        "Ostara": (3, 21),
        "Beltane": (5, 1),
        "Litha": (6, 21),
        "Lammas": (8, 1),
        "Mabon": (9, 21),
        "Samhain": (10, 31),
    },
    "south": {
        "Yule": (6, 21),
        "Imbolc": (8, 1),
        "Ostara": (9, 21),
        "Beltane": (11, 1),
        "Litha": (12, 21),
        "Lammas": (2, 1),
        "Mabon": (3, 21),
        "Samhain": (4, 30),
    }
}
