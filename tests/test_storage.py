# tests\test_storage.py

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
