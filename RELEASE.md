# GBPBot — Release Notes

## 🚀 Version 1.10.1  
**Release date:** 2026-01-18  
**Codename:** Discloud Migration & Stability Release

---

## ✨ Highlights

This release focuses on **deployment stability**, **hosting compatibility**, and **long-term maintainability**.

- ✅ Full migration to **Discloud**
- ✅ Flat file structure (single-directory project)
- ✅ Robust environment variable handling
- ✅ Centralized slash-command syncing
- ✅ Improved logging and error safety
- ✅ No breaking changes for end users

---

## 🧱 Architecture Overview

### Flat File Structure (Required)

All Python files now live in a **single directory**:

bot.py
logger.py
version_tracker.py
db.py
safe_send.py
constants.py
onboarding.py
reminders.py
commands.py


This structure:
- Prevents partial uploads on Discloud
- Avoids broken imports
- Allows safe single-file hotfixes

---

## 🔐 Environment Variables

Configuration is handled via `.env`, loaded at startup.

| Variable | Required | Purpose |
|--------|----------|---------|
| `DISCORD_TOKEN` | ✅ | Discord bot token |
| `GUILD_ID` | Optional | Faster slash command sync |
| `LOG_CHANNEL_ID` | Optional | Centralized logging |
| `DB_FILE` | Optional | SQLite DB path |
| `SABBAT_CHANNEL_ID` | Optional | Public sabbat announcements |

Missing optional variables **never crash the bot**.

---

## 🧠 Core Improvements

### bot.py
- Loads `.env` early using `python-dotenv`
- Graceful fallback from guild → global command sync
- Centralized cog loading and syncing
- Exposes `bot.GUILD_ID` for cog access

### Logging
- Logging channel is optional
- Console logging always works
- Discord logging fails safely if unavailable

### safe_send
- Fully interaction-safe
- Handles already-responded interactions
- Works with DMs, channels, users, and interactions

---

## 🌙 Features (User-Facing)

- 🌍 Region-aware reminders
- 🌓 Hemisphere-aware sabbats
- 📬 Daily reminder opt-in/out
- 🔮 Zodiac profiles
- 🧾 `/profile` (DM-only)
- 🧪 Admin tools: `/test`, `/onboarding_status`

---

## 🧪 Deployment Notes (Discloud)

### Required
- Upload files **one at a time**
- Restart bot after updates
- Ensure `.env` exists before starting

### Recommended
- Do not use subfolders
- Watch logs immediately after restart
- Test `/version` and `/test` after deploy

---

## 🔄 Upgrade Notes

Upgrading from ≤ v1.10.0:
- Flatten file structure
- Remove `utils/` and `cogs/`
- Update imports to flat names
- Add `.env`

Database schema remains compatible.

---

## 🏷 Versioning

- **Master version:** 1.10.1
- **Release type:** Stability / Infrastructure
- **Next focus:** Feature iteration (non-breaking)

---

This release establishes a **stable baseline** for future development on Discloud.
