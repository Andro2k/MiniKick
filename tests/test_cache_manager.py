# tests\test_cache_manager.py

import os
from backend.database.cache_manager import MusicCacheManager

def test_music_cache_manager_initialization(tmp_path):
    manager = MusicCacheManager()
    assert os.path.exists(manager.cache_dir)
    assert manager.get_cache_size_bytes() >= 0
    assert manager.get_cache_size_mb() >= 0.0

def test_cache_manager_eviction_under_threshold(tmp_path, monkeypatch):
    manager = MusicCacheManager()
    monkeypatch.setattr(manager, "cache_dir", str(tmp_path))
    dummy_file = tmp_path / "yt_test12345.m4a"
    dummy_file.write_bytes(b"0" * (1024 * 1024))
    deleted = manager.check_and_clean_cache(max_size_mb=5000)

    assert deleted == 0
    assert dummy_file.exists()
