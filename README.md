# 🌙 GBPBot – Your Mystical Discord Companion

✨ **Welcome to GBPBot**! ✨  
GBPBot is a Discord bot designed for community engagement with a mystical, astrology-themed experience. It provides personalized onboarding, daily reminders, interactive region & zodiac features, and journaling prompts.

---
# Version History

- **v1.0** – Initial reminders cog with basic daily loop and Next Sabbat / Next Full Moon buttons.

- **v1.1** – Added `safe_send` handling for all interaction responses to prevent errors.

- **v1.2** – Introduced Random Quote button for users.

- **v1.3** – Combined Random Quote + Journal Prompt button; fully consistent with bot UX and safe_send handling.

- **v1.4** – Added `daily` column to users table; updated `save_user_preferences` and `get_user_preferences` to handle daily preference.

- **v1.5** – Automatic `ALTER TABLE` to add `daily` if missing; backward-compatible with `set_user_preferences`.

- **v1.6** – Minor fixes for async DB operations and improved exception logging.

- **v1.7** – Updated `daily_loop` to unpack 6 values from `get_all_subscribed_users`; added `prefs["daily"]` check to send reminders only when enabled.

- **v1.8** – Fully robust `safe_send` handling across all buttons and daily loop; fixed `NoneType is_finished` errors.

- **v1.9** – Fixed `ephem.Moon` input type; ensured `view=None` in all `safe_send` calls.

- **v1.10** – Added hemisphere-aware sabbat reminders; daily loop now includes moon phase emoji; updated `constants.py` with `hemisphere` field and `SABBATS_HEMISPHERES` dict; fully integrated with safe_send and robust logging.

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
   cd gbpbot```

2. **Clone the repository**
	```bash 
	python -m venv .venv
	source .venv/bin/activate  # Linux/macOS
	.venv\Scripts\activate     # Windows```
	
3. **Install dependencies**
	```pip install -r requirements.txt```
	
4. **Environment Variables**
	
	Create a .env file with/Use railway
	
	```DISCORD_BOT_TOKEN=your_bot_token```
				and
	```GUILD_ID=your_server_id```

	**Initialize the Database**
	``` python -c "from db import init_db; init_db()" ```
	
	**Run**
	``` python bot.py ```

## Usage

### Onboarding

- New members will receive a DM upon joining.

- Use /onboard if the DM onboarding needs to be triggered manually.

### Daily Reminders

- Users can subscribe during onboarding.

- Reminders include quotes and journal prompts.

### Commands

- Interact with the bot using slash commands in Discord.

		Example: `/reminder`, `/submit_quote`, `/status`.

# Configuration

## Region Roles
```
python
REGIONS = {
    "North America": {"role_id": 1416438886397251768, "emoji": "🇺🇸"},
    "South America": {"role_id": 1416438925140164809, "emoji": "🌴"},
    "Europe": {"role_id": 1416439011517534288, "emoji": "🍀"},
    "Africa": {"role_id": 1416439116043649224, "emoji": "🌍"},
    "Oceania & Asia": {"role_id": 1416439141339758773, "emoji": "🌺"},
}
```

## Logging

- All errors and warnings are logged to the channel ID specified by ```LOG_CHANNEL_ID.```

## Contributing

- Fork the repository
- Create a feature branch:
  ```bash git checkout -b feature-name```
  
- Commit your changes:
  ```bash git commit -am 'Add new feature'```

- Push to the branch:
 ```bashgit push origin feature-name```

- Open a Pull Request
