# GBPBot — Your Mystical Discord Companion

Welcome to GBPBot.

GBPBot is a Discord bot designed for community engagement with a mystical,
astrology-inspired experience. It provides personalized onboarding, daily
reminders, region-aware features, zodiac profiles, and journaling prompts —
all delivered safely via direct messages.

---

## Current Version

Version: 1.10.1  
Release: Discloud Migration & Stability Release

Highlights:
- Flat file structure (single directory)
- Discloud-compatible deployment
- Robust logging and interaction safety
- No breaking changes for users

See CHANGE_LOG.md for full history  
See RELEASE.md for deployment notes

---

## Features

### Interactive Onboarding (DM-Based)
- Step-by-step flow: Region → Zodiac → Daily reminders
- Emoji-enhanced buttons
- Cancel support at every stage
- Safe DM delivery with graceful fallbacks

### Region & Hemisphere Awareness
- Timezone-aware scheduling
- Hemisphere-aware Sabbat reminders
- Shared region data across onboarding, reminders, and profiles

### Daily Reminders
- Optional daily DM reminders
- Includes inspirational quotes
- Includes journal prompts
- Includes moon phase emoji
- Fully respects user preferences (daily flag, days, hour)

### Sabbat & Moon Features
- Next Sabbat button
- Next Full Moon button
- Optional public Sabbat announcements (configurable)

### User Profile
- /profile (DM-only)
- Displays:
  - Region and timezone
  - Hemisphere
  - Zodiac
  - Subscription status
  - Daily reminder status

### Admin & Utility Commands
- /onboarding_status (admin only)
- /test (admin only)
- /version

---

## Commands Overview

| Command | Description |
|--------|-------------|
| /onboard | Start onboarding (DM-based) |
| /profile | View your settings (DM-only) |
| /reminder | Get an interactive reminder |
| /submit_quote | Submit an inspirational quote |
| /submit_journal | Submit a journal prompt |
| /unsubscribe | Stop daily reminders |
| /help | Receive command help via DM |
| /onboarding_status | Admin: onboarding overview |
| /test | Admin: test bot responsiveness |
| /version | Show current bot version |

---

## Project Structure (Required)

GBPBot uses a flat file structure.  
This is required for Discloud deployments.

All files must exist at the root level:

    bot.py
    logger.py
    version_tracker.py
    db.py
    safe_send.py
    constants.py
    onboarding.py
    reminders.py
    commands.py

Do not use subfolders such as utils/ or cogs/.

---

## Configuration (.env)

Create a file named .env in the project root.

Required variable:

    DISCORD_TOKEN=your_bot_token

Optional variables:

    GUILD_ID=your_server_id
    LOG_CHANNEL_ID=your_log_channel_id
    DB_FILE=bot_data.db
    SABBAT_CHANNEL_ID=optional_public_channel_id

Notes:
- Missing optional variables never crash the bot
- .env is loaded early at startup (Discloud-safe)

---

## Installation (Local Development)

Clone the repository:

    git clone https://github.com/yourusername/gbpbot.git
    cd gbpbot

Create and activate a virtual environment:

    python -m venv .venv
    source .venv/bin/activate   (Linux / macOS)
    .venv\Scripts\activate      (Windows)

Install dependencies:

    pip install -r requirements.txt

Run the bot:

    python bot.py

---

## Deployment (Discloud)

Important notes:
- Upload files one at a time
- Restart the bot after each update
- Ensure .env exists before starting
- Watch logs immediately after boot
- Test /version and /test after deployment

---

## Logging & Stability

- Centralized logging via logger.py
- Console logging always enabled
- Optional Discord logging channel
- All interaction errors handled safely
- No “This interaction failed” errors

---

## Versioning

GBPBot follows Semantic Versioning:

- MAJOR — Breaking changes
- MINOR — New features (backwards compatible)
- PATCH — Fixes and refactors

Version hygiene is tracked and enforced per release.

---

## Contributing

1. Fork the repository
2. Create a feature branch:

       git checkout -b feature-name

3. Commit your changes:

       git commit -am "Add feature"

4. Push and open a Pull Request

---

## Final Notes

GBPBot is designed to be:

- Mystical but reliable
- Thoughtfully engineered
- Safe under real-world Discord conditions
- Hosting-friendly (Discloud)

This README reflects the current, production-ready baseline.
