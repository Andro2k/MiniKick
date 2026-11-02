# resources\tests\test_config_provider.py

import threading
import tomllib
from typing import Mapping

import pytest

from backend.config.toml_config_provider import TomlConfigProvider
from backend.interfaces import IConfigProvider


class InMemoryConfigProvider(IConfigProvider):
    def __init__(self, initial=None):
        super().__init__()
        self.stored = dict(initial or {})

    def _load(self):
        return dict(self.stored)

    def _store(self, data: Mapping):
        self.stored = dict(data)


@pytest.fixture(params=["toml", "memory"])
def make_provider(request, tmp_path):
    def build(initial=None):
        if request.param == "memory":
            return InMemoryConfigProvider(initial)
        path = tmp_path / "config.toml"
        if initial is not None:
            path.write_text("".join(f"{key} = {_toml(value)}\n" for key, value in initial.items()), encoding="utf-8")
        return TomlConfigProvider(path)
    return build


def _toml(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return repr(value) if not isinstance(value, str) else '"' + value + '"'


def test_every_backend_honours_the_same_contract(make_provider):
    config = make_provider()
    assert config.load_string("missing", "fallback") == "fallback"
    assert config.load_bool("missing", True) is True

    config.save_string("tts_provider", "web")
    config.save_bool("tts_enabled", True)
    config.save_all({"volume": 80, "ratio": 0.5, "title": "hola 🎮 \"q\"\nlinea"})

    assert config.load_string("tts_provider") == "web"
    assert config.load_bool("tts_enabled") is True
    assert config.load_string("volume") == "80"
    assert config.load_string("title") == "hola 🎮 \"q\"\nlinea"


def test_legacy_string_flags_are_read_as_booleans(make_provider):
    config = make_provider({"old_on": "1", "old_off": "0", "new_on": True})

    assert config.load_bool("old_on") is True
    assert config.load_bool("old_off", True) is False
    assert config.load_bool("new_on") is True
    assert config.load_string("new_on") == "1"
    assert config.get_all() == {"old_on": True, "old_off": False, "new_on": True}


def test_delete_key_prefix_removes_only_matching_keys(make_provider):
    config = make_provider({"alert_a": "1", "alert_b": "x", "keep": "y"})
    config.delete_key_prefix("alert_")
    assert config.get_all() == {"keep": "y"}


def test_save_all_normalizes_unsupported_values(make_provider):
    config = make_provider()
    config.save_all({"none": None, "items": [1, 2]})
    assert config.load_string("none") == ""
    assert config.load_string("items") == "[1, 2]"


def test_toml_file_is_created_and_survives_a_new_instance(tmp_path):
    path = tmp_path / "nested" / "config.toml"
    first = TomlConfigProvider(path)
    first.save_all({"language": "es", "enabled": True, "volume": 70})

    on_disk = tomllib.loads(path.read_text(encoding="utf-8"))
    assert on_disk == {"language": "es", "enabled": True, "volume": 70}

    second = TomlConfigProvider(path)
    assert second.load_string("language") == "es"
    assert second.load_bool("enabled") is True


def test_missing_file_means_empty_configuration(tmp_path):
    config = TomlConfigProvider(tmp_path / "config.toml")
    assert config.get_all() == {}
    assert not (tmp_path / "config.toml").exists()


def test_corrupt_file_is_quarantined_and_defaults_are_used(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("esto = no es [toml", encoding="utf-8")

    config = TomlConfigProvider(path)
    assert config.load_string("language", "es") == "es"

    quarantined = list(tmp_path.glob("config.toml.corrupt-*"))
    assert len(quarantined) == 1
    assert quarantined[0].read_text(encoding="utf-8") == "esto = no es [toml"
    config.save_string("language", "en")
    assert tomllib.loads(path.read_text(encoding="utf-8")) == {"language": "en"}


def test_failed_write_keeps_previous_file_and_memory_untouched(tmp_path, monkeypatch):
    path = tmp_path / "config.toml"
    config = TomlConfigProvider(path)
    config.save_string("language", "es")

    import backend.config.toml_config_provider as module

    def explode(*_args, **_kwargs):
        raise OSError("disco lleno")

    monkeypatch.setattr(module.tomli_w, "dump", explode)
    config.save_string("language", "en")

    assert config.load_string("language") == "es"
    assert tomllib.loads(path.read_text(encoding="utf-8")) == {"language": "es"}
    assert [p.name for p in tmp_path.iterdir()] == ["config.toml"]


def test_concurrent_writers_do_not_lose_updates(tmp_path):
    config = TomlConfigProvider(tmp_path / "config.toml")

    def worker(offset):
        for n in range(15):
            config.save_string(f"k{offset}_{n}", str(n))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    reloaded = TomlConfigProvider(tmp_path / "config.toml").get_all()
    assert len(reloaded) == 60
