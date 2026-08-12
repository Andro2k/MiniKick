# Walkthrough v1.5.0: Complete Version Consolidation Report

## Overview
Comprehensive release walkthrough for **MiniKick v1.5.0**, consolidating all feature implementations, architectural refactorings, UI/UX modernizations, and cache retention fixes into a single unified document.

---

## Key Modules & Feature Implementations

### 1. Weighted Score Music Cache Eviction & Retention Fixes
- **[youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py)**: Prevented premature track deletion upon app shutdown by removing `os.remove(self.current_local_file)`. Active playing tracks remain cached.
- **[manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py)** & **[music_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/music_storage.py)**:
  - Removed 15-day automatic SQLite pruning trigger (`prune_youtube_cache`), deferring cache control to 5GB capacity limits.
  - Added `file_size_mb REAL DEFAULT 4.0` column and migration to `youtube_search_cache`.
  - Implemented weighted scoring formula for eviction:
    $$\text{Score} = \frac{\text{play\_count}}{((\text{julianday('now')} - \text{julianday(last\_accessed)}) + 0.5) \times \text{file\_size\_mb}}$$
    Evicts lowest-scoring songs first when cache approaches 5GB.

### 2. Reward Media Previews, Positions & Volume Columns
- **[thumbnail_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/rewards/thumbnail_service.py)**: Added frame extraction for videos (`0.5s` frame via `QVideoSink`), scaling for images, and SVG icons for audio.
- **[manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py)** & **[rewards_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/rewards_storage.py)**: Added `thumbnail_bytes BLOB` column to `obs_rewards` to store static previews persistently.
- **[rewards_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py)**:
  - Column 0: 48x32 rounded thumbnail previews for video/image files and dark volume pill SVG icons for audio.
  - Column 2 & 3: Added **Posición** (`X: {x}, Y: {y}` / `Aleatorio`) and **Volumen (%)** (`100%`) columns.
  - Expanded table to 5 structured columns.
- **[locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)** & **[locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)**: Added translation keys `col_pos`, `col_volume`, `pos_random`.

### 3. Dashboard, Chat & TTS Layout Optimizations
- **[dashboard_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py)**: Fixed vertical stretching on `avatar_card` and `info_card` by setting `QSizePolicy.Policy.Preferred`.
- **[chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py)**: Configured dynamic orientation layout ratios:
  - Horizontal mode: 40% tabs / 60% chat pane.
  - Vertical mode: 50% top tabs / 50% bottom chat pane for vertical monitor flexibility.
- **[tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py)**: Implemented `VoiceSettingRow` widget to stack titles above combo boxes, preventing text truncation in horizontal orientation.

### 4. Table Header Item Counts
- Updated table card headers across **[command_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/command_view.py)**, **[rewards_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py)**, and **[timers_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/timers_view.py)** to append total item counts dynamically (e.g. `Comandos Personalizados (12)`).

### 5. SVG Illustrations Sizing & 4-Color Normalization
- **4-Color System**: Standardized all 7 core 3D isometric SVG vector illustrations (`illustration-document.svg`, `illustration-earphone.svg`, `illustration-menu.svg`, `illustration-picture.svg`, `illustration-switch.svg`, `illustration-thumbs-up.svg`, `illustration-time.svg`) to strictly use the 4 theme colors:
  1. Base Floor Shadow: `#18181B` (`COLOR_NEUTRAL_850`)
  2. Platform Slab Top: `#27272A` (`COLOR_NEUTRAL_800`)
  3. Structure & Bevels: `#3F3F46` (`COLOR_NEUTRAL_700`)
  4. Primary Feature Accent: `#2ECD70` (Kick Green)
- **Scalable Dimensions**: Standardized `ScalableIllustration` parameters to `min_size=120`, `max_size=300`, and `size_offset=320` across `ModernTableCard`, `LogView`, and `AlreadyRunningDialog`.

### 6. App Taskbar Icon & OAuth Web Favicon
- **[main.py](file:///c:/Users/TheAn/Desktop/python/Kick/main.py)**: Registered `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("andro2k.minikick.app.1.5")` on Windows, ensuring Windows Taskbar displays the custom app icon (`icon.ico`) instead of the default Python executable icon.
- **[auth.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/web/auth.html)**: Added Kick green SVG data URI `<link rel="icon">` in `<head>` for OAuth web browser tabs.

### 7. Custom UI Components: Unified Search Bar & Segmented Pagination
- **[search_bar.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/search_bar.py)** (`UnifiedSearchBar`): Created a rounded box widget integrating a frameless input field and a right-aligned search button segment with a `search.svg` icon separated by a vertical line divider.
- **[pagination.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/pagination.py)** (`SegmentedPagination`): Created a 5-segment pill control (`<<`, `<`, `X / Y`, `>`, `>>`) with Tabler SVG icons (`chevrons-left.svg`, `chevron-left.svg`, `chevron-right.svg`, `chevrons-right.svg`).
- **[log_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/log_view.py)**: Integrated `UnifiedSearchBar` and `SegmentedPagination`.
- **[command_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/command_view.py)** & **[timers_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/timers_view.py)**: Upgraded table card search headers to `UnifiedSearchBar` via `ModernTableCard`.

### 8. Theme QSS Centralization
- **[theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)**: Centralized all composite widget styling rules (`QFrame[role="search_bar"]` and `QFrame[role="segmented_pagination"]`) into `GLOBAL_QSS`, eliminating inline QSS strings across widget files for strict Single Source of Truth (SSoT) compliance.

---

## Verification & Validation

### Automated Unit Test Suite
Ran full test suite via `uv run pytest`:
```bash
33 passed in 7.76s
```

### Module Compilation Verification
Verified Python compilation across all altered frontend and backend files:
```bash
uv run python -m py_compile main.py frontend/common/theme.py frontend/widgets/search_bar.py frontend/widgets/pagination.py frontend/widgets/table.py frontend/views/command_view.py frontend/views/rewards_view.py frontend/views/timers_view.py frontend/views/dashboard_view.py frontend/views/log_view.py frontend/dialogs/already_running_dialog.py
```
*Status*: 0 errors (clean compilation).
