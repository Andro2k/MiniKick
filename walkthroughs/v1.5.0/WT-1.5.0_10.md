# Walkthrough - WT-1.5.0_10: Persistent SQLite Schema for Rewards Metadata

## Summary
Extended the local SQLite database schema (`obs_rewards` table) to persistently store Kick rewards metadata (`reward_id`, `cost`, `description`, `background_color`, `is_user_input_required`). This guarantees that all reward details remain cached locally in SQLite and are accessible even when offline without requiring connection to Kick API.

---

## Changes Made

### 1. Database Manager (`backend/database/manager.py`)
- Updated `CREATE TABLE IF NOT EXISTS obs_rewards` to include:
  - `reward_id TEXT`
  - `cost INTEGER DEFAULT 100`
  - `description TEXT DEFAULT ''`
  - `background_color TEXT DEFAULT '#00e701'`
  - `is_user_input_required INTEGER DEFAULT 0`
- Added safe `ALTER TABLE` statements to perform automatic database migrations for existing SQLite databases without data loss.

### 2. SQLite Rewards Storage (`backend/database/rewards_storage.py`)
- **`load_all()`**: Updated SELECT query to read all metadata columns (`reward_id`, `cost`, `description`, `background_color`, `is_user_input_required`) and return them in the local mapping dictionary.
- **`save_all()`**: Updated INSERT query to write all metadata columns to the SQLite `obs_rewards` table.

---

## Verification Results

### Automated Tests
- Executed unit tests using `.venv\Scripts\pytest`:
  - Result: `35 passed in 8.10s` (100% pass rate).

### Functionality Verified
- Saving reward mappings now writes full metadata (`id`, `cost`, `description`, `color`, `user_input`) into SQLite `obs_rewards`.
- Loading reward mappings from SQLite restores all reward properties even when offline or before API synchronization.
