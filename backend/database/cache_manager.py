# backend\database\cache_manager.py

import os
import re
import logging
from backend.database.music_storage import SQLiteMusicStorage

logger = logging.getLogger("minikick.database.cache_manager")

class MusicCacheManager:
    DEFAULT_MAX_CACHE_MB = 5000

    def __init__(self, music_storage: SQLiteMusicStorage = None):
        self.music_storage = music_storage
        app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        self.cache_dir = os.path.join(app_data_dir, '.Minikick', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_cache_size_bytes(self) -> int:
        total_bytes = 0
        if not os.path.exists(self.cache_dir):
            return 0
        try:
            for fname in os.listdir(self.cache_dir):
                if fname.startswith("yt_"):
                    fpath = os.path.join(self.cache_dir, fname)
                    if os.path.isfile(fpath):
                        total_bytes += os.path.getsize(fpath)
        except Exception as e:
            logger.error("[MusicCacheManager] Error calculating cache size: %s", e)
        return total_bytes

    def get_cache_size_mb(self) -> float:
        return round(self.get_cache_size_bytes() / (1024 * 1024), 2)

    def check_and_clean_cache(self, max_size_mb: int = DEFAULT_MAX_CACHE_MB) -> int:

        current_bytes = self.get_cache_size_bytes()
        max_bytes = max_size_mb * 1024 * 1024
        target_bytes = int(max_bytes * 0.8)

        if current_bytes <= max_bytes:
            return 0

        logger.info("[MusicCacheManager] Cache size (%.2f MB) exceeds max threshold (%d MB). Starting eviction...", 
                    current_bytes / (1024 * 1024), max_size_mb)

        deleted_files = 0
        freed_bytes = 0

        least_popular = self.music_storage.get_least_popular_cached_songs() if self.music_storage else []

        for song in least_popular:
            if current_bytes - freed_bytes <= target_bytes:
                break

            url = song.get("url", "")
            match = re.search(r'(?:v=|\/|embed\/|v\/)([a-zA-Z0-9_-]{11})', url)
            if not match:
                continue
            
            raw_id = match.group(1)
            for fname in os.listdir(self.cache_dir):
                if fname.startswith(f"yt_{raw_id}.") and not fname.endswith(".part"):
                    fpath = os.path.join(self.cache_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            fsize = os.path.getsize(fpath)
                            os.remove(fpath)
                            freed_bytes += fsize
                            deleted_files += 1
                            logger.info("[MusicCacheManager] Evicted low-score track: '%s' (Score: %.4f, freed %.2f MB)", 
                                        song.get("title", fname), song.get("score", 0.0), fsize / (1024 * 1024))
                        except Exception as del_err:
                            logger.warning("[MusicCacheManager] Failed to delete cache file %s: %s", fpath, del_err)

        if current_bytes - freed_bytes > target_bytes:
            try:
                cached_files = []
                for fname in os.listdir(self.cache_dir):
                    if fname.startswith("yt_") and not fname.endswith(".part"):
                        fpath = os.path.join(self.cache_dir, fname)
                        if os.path.isfile(fpath):
                            cached_files.append((os.path.getmtime(fpath), fpath))
                
                cached_files.sort(key=lambda x: x[0])
                for _, fpath in cached_files:
                    if current_bytes - freed_bytes <= target_bytes:
                        break
                    try:
                        fsize = os.path.getsize(fpath)
                        os.remove(fpath)
                        freed_bytes += fsize
                        deleted_files += 1
                    except Exception:
                        pass
            except Exception as e:
                logger.error("[MusicCacheManager] Error cleaning orphan files: %s", e)

        logger.info("[MusicCacheManager] Eviction completed. Freed %.2f MB across %d files.", freed_bytes / (1024 * 1024), deleted_files)
        return deleted_files

    def clear_all_cache(self) -> int:
        deleted = 0
        if not os.path.exists(self.cache_dir):
            return 0
        try:
            for fname in os.listdir(self.cache_dir):
                if fname.startswith("yt_"):
                    fpath = os.path.join(self.cache_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            os.remove(fpath)
                            deleted += 1
                        except Exception:
                            pass
        except Exception as e:
            logger.error("[MusicCacheManager] Error clearing all cache: %s", e)
        return deleted
