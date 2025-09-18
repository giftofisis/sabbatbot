# 🌙 GBPBot – Your Mystical Discord Companion

✨ **Welcome to GBPBot**! ✨  
GBPBot is a Discord bot designed for community engagement with a mystical, astrology-themed experience. It provides personalized onboarding, daily reminders, interactive region & zodiac features, and journaling prompts.

---

## Features

- **Interactive Onboarding**
  - DM-based sequential flow: Region → Zodiac → Subscription
  - Emoji-enhanced buttons
  - Color-coded subscription buttons (green for subscribe, red for unsubscribe)
  - Safe DM delivery with fallback messages in server channels

- **Region-Specific Roles**
  - Assign users to region roles based on selection
  - Access region-specific channels

- **Zodiac Integration**
  - Personalized zodiac selection during onboarding

- **Daily Reminders**
  - Optional daily notifications via DM
  - Includes inspirational quotes and journal prompts
  - Region-aware scheduling (time zones)

- **Interactive Commands**
  - `/reminder` – Receive an interactive daily reminder
  - `/submit_quote` – Add a custom inspirational quote
  - `/submit_journal` – Add a custom journal prompt
  - `/status` – Check bot status and upcoming events
  - `/unsubscribe` – Stop receiving daily DMs
  - `/onboard` – Manually start the onboarding process
  - `/help` – Get a DM with all available commands

- **Safe & Robust**
  - Handles missing roles, DMs, and database errors gracefully
  - Error logging to a dedicated channel

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gbpbot.git
   cd gbpbot
