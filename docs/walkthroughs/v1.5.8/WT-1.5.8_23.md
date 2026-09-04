# Walkthrough: WT-1.5.8_23 - Part 1: Facade Modernization for `main.py` & `backend/core`

## 1. Executive Summary

As Part 1 of the multi-phase codebase facade migration, all imports in `main.py` and `backend/core/` have been updated to consume the unified package entry points (`backend.core`, `backend.config`, `backend.database`, `backend.services.system`, `backend.providers.music`), removing deep internal file path coupling and converting intra-package imports in `main_window_core.py` to relative imports.

---

## 2. Changes Summary

| Target File | Modifications |
| :--- | :--- |
| [main.py](file:///c:/Users/TheAn/Desktop/python/Kick/main.py) | - Combined logging and window imports into `from backend.core import setup_application_logging, flush_all_logs, MainWindowCore`.<br>- Modernized updater and instance service imports to `from backend.services.system import (...)`.<br>- Modernized version and webhook imports to `from backend.config import APP_VERSION, DISCORD_WEBHOOK_URL`.<br>- Cleaned database import to `from backend.database import DatabaseManager, SQLiteSettingsStorage`. |
| [app_container_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_container_core.py) | - Updated API keys access to `import backend.config as _api_keys`.<br>- Updated music provider import to `from backend.providers.music import YouTubeMusicProvider`. |
| [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py) | - Converted core cross-imports to relative intra-package imports (`.app_container_core`, `.app_logger_core`).<br>- Updated config import to `from backend.config import KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY, TWITCH_CLIENT_ID`. |

---

## 3. Verification & Validation

### Automated Imports Check
```bash
uv run python -c "import main; print('main imported successfully!')"
```
Exit code: `0`.

### Full Unit Test Suite
```bash
uv run pytest resources/tests/unit -q
```
**Result:**
```text
============================ 239 passed in 12.96s =============================
```
100% test pass rate with zero regressions.
