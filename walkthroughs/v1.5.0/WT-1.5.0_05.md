# Walkthrough - WT-1.5.0_05: Track Title Logging in YouTube Resolve Worker

## Summary
Added track title propagation and explicit logging in `YouTubeResolveWorker` and `YouTubeMusicProvider`. When audio is downloading or retrieved from disk cache, the logger now clearly states the song's name (e.g. `[YouTubeResolveWorker] Downloading audio stream for 'Song Title' (ID xyz)...`).

---

## Changes Made

### 1. Music Resolve Worker (`backend/workers/music_worker.py`)
- **Expected Title Parameter**: `YouTubeResolveWorker.__init__` now accepts an `expected_title: str` argument.
- **Download Logging**: Added an explicit log entry right before `yt_dlp` audio downloading begins:
  `logging.info("[YouTubeResolveWorker] Downloading audio stream for '%s' (ID %s)...", title, raw_id)`
- **Disk Cache Hit Logging**: Updated instant and regular disk cache hit log messages to include the song's title:
  - Instant cache hit: `logging.info("[YouTubeResolveWorker] Instant disk cache hit for '%s' (ID %s): %s", cache_title, direct_id, fpath)`
  - Regular cache hit: `logging.info("[YouTubeResolveWorker] Disk cache hit for '%s' (ID %s): %s", title, raw_id, fpath)`

### 2. Music Provider (`backend/providers/music/youtube_client.py`)
- Passed `expected_title=next_song.get("title", "")` and `expected_title=self.current_song.get("title", "")` when initializing `YouTubeResolveWorker` in `_preload_next_song()` and `_play_next()`.

---

## Verification Results

### Automated Tests
- Executed unit tests using `.venv\Scripts\pytest`:
  - Result: `35 passed in 8.10s` (100% pass rate).

### Functionality Verified
- When downloading a song, `minikick.log` outputs the exact track title right before the `yt_dlp` progress output (`[download] 0.0% of...`).
- When hitting the disk cache, the song title is logged and preserved.
