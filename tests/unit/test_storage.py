# tests\unit\test_storage.py

import os

def test_save_and_get_string(storage):
    storage.save_string("test_key", "test_value")
    val = storage.load_string("test_key", default="")
    assert val == "test_value"

def test_load_and_save_bool(storage):
    storage.save_bool("autostart", True)
    assert storage.load_bool("autostart", False) is True

    storage.save_bool("autostart", False)
    assert storage.load_bool("autostart", True) is False

def test_default_fallback(storage):
    val = storage.load_string("non_existent_key", default="default_val")
    assert val == "default_val"

def test_sqlite_token_storage_list_scope():
    import tempfile
    from backend.database.manager import DatabaseManager
    from backend.database.token_storage import SQLiteTokenStorage

    tmpdir_ctx = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    try:
        db_path = os.path.join(tmpdir_ctx.name, "test_tokens.db")
        db = DatabaseManager(db_name=db_path)
        token_storage = SQLiteTokenStorage(db, provider="twitch")

        tokens = {
            "access_token": "twitch_access_123",
            "refresh_token": "twitch_refresh_456",
            "expires_in": 14400,
            "scope": ["chat:read", "chat:edit", "user:read:chat", "channel:moderate"],
            "token_type": "bearer"
        }

        token_storage.save(tokens)
        loaded = token_storage.load()
        assert loaded is not None
        assert loaded["access_token"] == "twitch_access_123"
        assert loaded["scope"] == "chat:read chat:edit user:read:chat channel:moderate"
        db.cleanup()
    finally:
        tmpdir_ctx.cleanup()
