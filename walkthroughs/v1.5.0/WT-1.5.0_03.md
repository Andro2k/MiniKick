# Walkthrough: Weighted Score Music Cache Eviction & Retention Fixes

## Overview
Implemented an intelligent, weighted-scoring cache eviction algorithm for MiniKick's 5GB music cache. Also resolved underlying bugs causing premature track deletion before reaching the 5GB cache threshold.

---

## Key Changes

### Fixes for Premature Track Deletion
- **[youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py#L252)**: Removed `os.remove(self.current_local_file)` from `shutdown()`. Active tracks playing when closing MiniKick will now remain safely in cache.
- **[manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py#L298)**: Removed the 15-day automatic SQLite trigger `prune_youtube_cache`. Metadata entries are no longer purged arbitrarily after 15 days, allowing the weighted score algorithm to fully govern retention up to 5GB.

### Database Layer
- **[manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py)**: Added `file_size_mb REAL DEFAULT 4.0` column definition and safe migration (`ALTER TABLE`) to `youtube_search_cache`.
- **[music_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/music_storage.py)**:
  - Added `update_file_size(query_or_url, size_mb)` to save actual file sizes to SQLite.
  - Refactored `get_least_popular_cached_songs()` to query candidates using the SQLite formula:
    $$\text{Score} = \frac{\text{play\_count}}{((\text{julianday('now')} - \text{julianday(last\_accessed)}) + 0.5) \times \text{file\_size\_mb}}$$
    Candidates are returned in ascending order of `score`, ensuring low-value files are evicted first.

### Provider Layer
- **[youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py)**: Added file size measurement (`os.path.getsize()`) on active track resolution (`_on_song_resolved`) and background preloading (`on_preload_resolved`), storing exact sizes in SQLite.

---

## Verification & Automated Test Results

### Test Suite Execution
Executed unit test suite via `uv run pytest`:
```bash
33 passed in 7.76s
```
All tests passed successfully.
