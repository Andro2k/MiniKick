# Walkthrough - WT-1.5.0_09: Fix Kick Rewards Metadata Auto-Hydration

## Summary
Fixed an issue where editing existing Kick channel rewards displayed default/empty values on first open. Resolved by calling `_fetch_api_rewards()` automatically upon view initialization, navigation, and WebSocket authentication, and updating local storage mappings with live Kick API metadata.

---

## Changes Made

### 1. Application Core (`frontend/core/main_window_core.py`)
- **Auto-Fetch on View Creation**: Triggered `self._fetch_api_rewards()` immediately when `RewardsView` ("Triggers") is instantiated in `_get_or_create_view`.
- **Auto-Fetch on Navigation**: Triggered `self._fetch_api_rewards()` when navigating to the Triggers tab in `_handle_navigation`.
- **Auto-Fetch on WebSocket Connect**: Triggered `self._fetch_api_rewards()` inside `_on_web_socket_connected`.

### 2. Controller Layer (`backend/controllers/rewards_controller.py`)
- Updated `update_rewards_list` to automatically merge fresh Kick API details (`cost`, `description`, `background_color`, `is_user_input_required`, `id`) into local storage mappings (`conf.get(key) != details[key]`), ensuring local persistent caching stays 100% in sync with Kick API.

---

## Verification Results

### Automated Tests
- Executed unit tests using `.venv\Scripts\pytest`:
  - Result: `35 passed in 8.20s` (100% pass rate).

### Functionality Verified
- Opening the "Triggers / Rewards" tab automatically fetches live Kick rewards data in the background.
- Clicking "Editar" on any pre-existing reward immediately populates all reward details (Cost, Description, Background Color, User Input switch) directly from Kick API / local cache.
