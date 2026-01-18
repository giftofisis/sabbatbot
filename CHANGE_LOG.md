# GBPBot — MASTER CHANGE LOG
# ==================================================
# This file is the authoritative, human-readable history of GBPBot.
# It consolidates all in-file CHANGE LOG entries across bot.py, cogs,
# utilities, and configuration into a single chronological timeline.
#
# Deployment target: Discloud
# Architecture: Flat-file (single directory) Python project
# ==================================================
# --------------------------------------------------
# [2026-01-18] v1.10.2 — Profile Editing & Admin Hardening
# --------------------------------------------------

## User Experience
- Added **interactive `/profile` command (DM-only)** with edit buttons:
  - 🔄 Refresh profile
  - ☀️ Toggle daily messages
  - 📬 Toggle subscription status
  - 🧭 Guidance to re-run onboarding for region/zodiac changes
- `/profile` continues to expose **user-facing data only**:
  - Region, timezone, hemisphere (derived from constants)
  - Zodiac
  - Subscription and daily reminder status
- All profile interactions are **owner-locked** (buttons cannot be used by other users)

## Admin / Moderation
- Hardened internal and diagnostic commands:
  - `/test` is now **guild-only** and **administrator-only**
  - `/onboarding_status` is now **guild-only** and **administrator-only**
- Prevents accidental exposure of internal or member-level data in public servers

## commands.py (v1.9.4.0)
- Introduced `ProfileEditView` using Discord UI buttons
- Centralized profile embed rendering for consistent refresh/update behavior
- Removed cog-level slash command syncing:
  - Command sync is now **exclusively handled in bot.py**
- Improved error handling and logging consistency via `robust_log(exc=...)`

## db.py (v1.0.5.0)
- Added `set_daily()` helper for toggling daily reminders
- `set_daily()` delegates to `save_user_preferences()` for:
  - Upsert safety
  - Schema consistency
  - Zero new dependencies
- No breaking schema changes introduced

## version_tracker.py (v1.0.9)
- Updated tracked versions for:
  - `commands.py` → 1.9.4.0
  - `db.py` → 1.0.5.0
- Maintains flat-structure compatibility and backward aliases
- Master `GBPBot_version` remains **1.10.1** (feature batch in progress)

## Internal Quality
- All new interactions use existing `safe_send` lifecycle handling
- No changes required to reminder loops or onboarding flow
- Fully Discloud-safe (no background tasks, no new env requirements)


# --------------------------------------------------
# [2026-01-18] v1.10.1 — Discloud Migration & Flat Structure Refactor
# --------------------------------------------------

## Core / Architecture
- Migrated project to **Discloud-compatible flat file structure**:
  - Removed all `utils.*` and `cogs.*` imports
  - All `.py` files now reside in a single directory
  - All extensions loaded via flat module names (`onboarding`, `reminders`, `commands`)
- Ensured compatibility with Discloud’s **single-file upload workflow**
- Standardized imports across all files to prevent partial-upload failures

## bot.py (v1.9.5.1)
- Loads `.env` **early** via `python-dotenv` (required for Discloud)
- Supports `DISCORD_TOKEN` (preferred) and legacy token names
- Exposes `bot.GUILD_ID` for cogs
- Centralized slash command syncing (guild-first with 403 fallback to global)
- Added safe debug logging for env presence (never prints secrets)
- Cleaned duplicated changelog entries

## logger.py (v1.1.0)
- Replaced hardcoded `LOG_CHANNEL_ID` with **env-driven configuration**
- Added support for both `error=` and `exc=` arguments
- Fully safe logging:
  - Never crashes if bot, channel, or permissions are missing
  - Console logging always works
  - Discord logging is optional and failure-tolerant

## version_tracker.py (v1.0.8)
- Updated tracked versions to match flat structure
- Removed references to non-deployed files
- Added tracking for version_tracker.py itself
- Maintains backward-compatible aliases (`VERSIONS`, `file_versions`)
- Master `GBPBot_version` remains **1.10.1**

## db.py (v1.0.4.1)
- Flat-structure import refactor
- Database path now **env-driven** via `DB_FILE`
- Auto-creates database directories when needed (Discloud-safe)
- Fixed improper `robust_log(exc=traceback)` usage
- Ensured all SQLite connections close safely
- Retains:
  - `daily` column auto-migration
  - Upsert-safe user preference handling
  - Quote and journal prompt prepopulation

## safe_send.py (v1.9.1.0)
- Moved from `utils/safe_send.py` to flat `safe_send.py`
- Fixed incorrect `robust_log` call signatures
- Added optional `bot=` passthrough for reliable logging
- Robust handling for:
  - Interactions (response → followup fallback)
  - DMs, channels, users
  - Already-responded interactions
- Eliminates all `is_finished` interaction errors

## constants.py (v1.0.2)
- Flat-structure compatible (no imports required)
- Added `"name"` field to each region entry (prevents KeyErrors)
- Central source of truth for:
  - REGIONS (emoji, tz, color, hemisphere)
  - ZODIAC_SIGNS
  - SABBATS_HEMISPHERES

## reminders.py (v1.10.2)
- Flat imports (`logger`, `safe_send`, `constants`)
- Hemisphere-aware sabbat reminders retained
- Env-driven `SABBAT_CHANNEL_ID` for optional public posts
- Fixed Next Full Moon button bug (date vs datetime)
- Portable date formatting (no platform-specific strftime flags)
- Daily + Sabbat loops made **idempotent** to prevent double-start errors
- Reminder buttons fully synced with constants data

## onboarding.py (v1.9.2.2)
- Flat imports (`safe_send`, `logger`, `constants`)
- Robust DM onboarding flow retained:
  - Region → Zodiac → Daily reminders
  - Cancel support at every stage
- Env-driven `LOG_CHANNEL_ID` for optional onboarding completion logs
- Fully synced with DB daily/subscription flags
- Safe interaction handling everywhere

## commands.py (v1.9.3.2)
- Flat imports (`safe_send`, `logger`, `constants`, `reminders`)
- Fixed `/profile`:
  - Hemisphere now derived from region constants (not DB)
- `/profile` remains DM-only with user-facing fields only
- Admin-only restrictions enforced on:
  - `/onboarding_status`
  - `/test`
- `/version` now uses centralized FILE_VERSIONS consistently
- Reminder buttons imported directly from `reminders.py`

---

# --------------------------------------------------
# [2025-09-21] v1.10.0 — Hemisphere-Aware Sabbats
# --------------------------------------------------
- Added hemisphere-aware sabbat reminders
- Introduced `SABBATS_HEMISPHERES`
- Regions updated with `hemisphere` field
- Version tracking updated accordingly
- `GBPBot_version` set to 1.10.0

# --------------------------------------------------
# [2025-09-21] v1.9.2.x — Onboarding & Daily Preferences
# --------------------------------------------------
- Fixed onboarding button callback capture bugs
- Emojis added to onboarding buttons
- Onboarding fully synced with constants
- Daily preference flag respected across reminders and DB

# --------------------------------------------------
# [2025-09-21] v1.9.0.0 — safe_send Integration
# --------------------------------------------------
- Introduced robust `safe_send`
- Eliminated `This interaction failed` errors
- Added cancel support to onboarding
- Unified interaction/DM sending logic

# --------------------------------------------------
# [2025-09-21] v1.0.x — Foundations
# --------------------------------------------------
- Initial creation of:
  - bot.py
  - db.py
  - reminders.py
  - onboarding.py
  - commands.py
  - version_tracker.py
- Established centralized version tracking
