# GBPBot - constants.py
# Version: 1.0.0
# Last Updated: 2025-09-21
# Notes:
# - Centralized constants for regions, zodiac signs, emojis, and other shared references.
# - To be imported by onboarding.py, reminders.py, and other cogs.
# -----------------------
# CHANGE LOG
# -----------------------
# [2025-09-21 14:30 BST] v1.0.0 - Initial creation of constants.py with regions, zodiac signs, emojis, and related references.

# -----------------------
# Regions
# -----------------------
REGIONS = {
    "North America": {
        "emoji": "🗽",
        "tz": "America/New_York",
        "role_id": 1416438886397251768,
        "color": 0x2ecc71
    },
    "South America": {
        "emoji": "🌴",
        "tz": "America/Sao_Paulo",
        "role_id": 1416438925140164809,
        "color": 0xe67e22
    },
    "Europe": {
        "emoji": "🍀",
        "tz": "Europe/London",
        "role_id": 1416439011517534288,
        "color": 0x3498db
    },
    "Africa": {
        "emoji": "🌍",
        "tz": "Africa/Johannesburg",
        "role_id": 1416439116043649224,
        "color": 0xf1c40f
    },
    "Oceania & Asia": {
        "emoji": "🌺",
        "tz": "Australia/Sydney",
        "role_id": 1416439141339758773,
        "color": 0x9b59b6
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
SABBATS = {
    "Imbolc": (2, 1),
    "Ostara": (3, 20),
    "Beltane": (5, 1),
    "Litha": (6, 21),
    "Lughnasadh": (8, 1),
    "Mabon": (9, 22),
    "Samhain": (10, 31),
    "Yule": (12, 21)
}
