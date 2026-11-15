# resources\tests\test_commands_help_and_backup.py
"""Etiquetas i18n de !commands y round-trip de la copia de seguridad (playlists y timers)."""

import json
import os

import pytest

from backend.handlers.command_help_formatter import CommandHelpFormatter
from backend.services.app.backup_service import BackupService

LOCALES = os.path.join(os.path.dirname(__file__), "..", "..", "locales")


class _I18n:
    def __init__(self, lang):
        with open(os.path.join(LOCALES, f"{lang}.json"), encoding="utf-8") as f:
            self._texts = json.load(f)

    def get(self, key, **_):
        val = self._texts
        for part in key.split("."):
            if not isinstance(val, dict) or part not in val:
                return key
            val = val[part]
        return str(val)


@pytest.mark.parametrize("lang", ["es", "en"])
def test_commands_help_has_no_raw_i18n_keys(lang):
    cmds = [
        {"trigger": "!hola", "response": "hola", "permission": "everyone"},
        {"trigger": "!sr", "response": "[PLUGIN_MUSIC_SR]", "permission": "everyone"},
        {"trigger": "!death", "response": "[PLUGIN_WIDGET_DEATH]", "permission": "everyone"},
        {"trigger": "!ttsmute", "response": "[PLUGIN_CHAT_TTS_MUTE]", "permission": "moderator"},
    ]
    msgs = CommandHelpFormatter(_I18n(lang)).format(cmds, "", is_mod=True)
    assert msgs and all("sec_" not in m for m in msgs)


class _Playlists:
    def __init__(self):
        self.data = {}

    def list_playlists(self):
        return [{"id": i, "name": n, "song_count": len(s)} for i, (n, s) in enumerate(self.data.items(), 1)]

    def get_songs(self, playlist_id):
        return list(list(self.data.values())[playlist_id - 1])

    def create_playlist(self, name):
        if name in self.data:
            return -1
        self.data[name] = []
        return list(self.data).index(name) + 1

    def add_song(self, playlist_id, title, artist, url, duration="-"):
        songs = list(self.data.values())[playlist_id - 1]
        if any(s["url"] == url for s in songs):
            return False
        songs.append({"title": title, "artist": artist, "url": url, "duration": duration})
        return True


class _Cfg(dict):
    def get_all(self):
        return dict(self)

    def load_string(self, key, default=""):
        return self.get(key, default)

    def save_all(self, settings):
        self.update(settings)


class _Timers:
    def __init__(self):
        self.saved = []

    def load_all(self):
        return [{"name": "t", "messages": ["m"], "apply_youtube": False}]

    def save_timer(self, **kwargs):
        self.saved.append(kwargs)


def test_backup_roundtrip_playlists_and_timer_youtube_flag(tmp_path):
    src = _Playlists()
    pid = src.create_playlist("Rock")
    src.add_song(pid, "Song", "Band", "https://y/1", "3:00")
    timers = _Timers()
    svc = BackupService(_Cfg(), None, None, None, timers_storage=timers, playlist_storage=src)
    path = str(tmp_path / "b.json")
    assert svc.export_to_json(path)

    dst = _Playlists()
    dst_timers = _Timers()
    svc2 = BackupService(_Cfg(), None, None, None, timers_storage=dst_timers, playlist_storage=dst)
    assert svc2.inspect_backup(path)["sections"]["playlists"]["count"] == 1
    assert svc2.import_from_json(path)
    assert dst.data["Rock"][0]["url"] == "https://y/1"
    assert dst_timers.saved[0]["apply_youtube"] is False
    assert svc2.import_from_json(path, sections={"playlists"})
    assert len(dst.data["Rock"]) == 1
