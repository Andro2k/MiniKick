# resources\\tests\\test_music_sr_youtube_links.py

import sys
import types
from unittest.mock import MagicMock

import pytest

from backend.services.chat.commands_service import CommandService
from backend.services.chat.spam_service import SpamService
from backend.utils.youtube_url import KIND_LINK, KIND_SEARCH, KIND_YOUTUBE_VIDEO, classify_music_query
from backend.workers.music_worker import YouTubeSearchWorker

VIDEO = "dQw4w9WgXcQ"
CANONICAL = f"https://www.youtube.com/watch?v={VIDEO}"


@pytest.mark.parametrize("text", [
    f"https://www.youtube.com/watch?v={VIDEO}",
    f"https://www.youtube.com/watch?v={VIDEO}&list=RDdQw4w9WgXcQ&start_radio=1",
    f"https://youtu.be/{VIDEO}?si=abc123",
    f"youtu.be/{VIDEO}",
    f"www.youtube.com/watch?v={VIDEO}",
    f"https://m.youtube.com/watch?v={VIDEO}&t=42s",
    f"https://music.youtube.com/watch?v={VIDEO}&si=xyz",
    f"https://www.youtube.com/shorts/{VIDEO}",
    f"https://www.youtube.com/live/{VIDEO}?feature=share",
    f"https://www.youtube.com/embed/{VIDEO}",
    f"<https://youtu.be/{VIDEO}>",
    f"https://youtu.be/{VIDEO} porfa esta canción",
])
def test_youtube_video_links_are_normalised(text):
    assert classify_music_query(text) == (KIND_YOUTUBE_VIDEO, CANONICAL)


def test_search_text_is_not_a_link():
    assert classify_music_query("bad bunny titi me pregunto") == (KIND_SEARCH, "bad bunny titi me pregunto")
    assert classify_music_query("youtube lofi beats") == (KIND_SEARCH, "youtube lofi beats")


def test_playlist_and_foreign_links_pass_through_as_links():
    playlist = "https://www.youtube.com/playlist?list=PL123"
    assert classify_music_query(playlist) == (KIND_LINK, playlist)
    other = "https://soundcloud.com/artist/track"
    assert classify_music_query(other) == (KIND_LINK, other)


class _FakeYDL:
    result = {}

    def __init__(self, opts):
        type(self).last_opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, query, download=False):
        return type(self).result


@pytest.fixture
def fake_yt_dlp(monkeypatch):
    module = types.ModuleType("yt_dlp")
    module.YoutubeDL = _FakeYDL
    monkeypatch.setitem(sys.modules, "yt_dlp", module)
    return _FakeYDL


class _I18n:
    def get(self, key):
        return key


def _run_worker(**kwargs):
    worker = YouTubeSearchWorker(CANONICAL, CANONICAL, _I18n(), **kwargs)
    results = []
    worker.search_completed.connect(lambda ok, msg: results.append((ok, msg)))
    worker.run()
    return worker, results


def test_single_video_without_entries_is_queued(fake_yt_dlp):
    fake_yt_dlp.result = {"id": VIDEO, "title": "Song", "uploader": "Artist", "duration": 213, "extractor": "youtube"}
    worker, results = _run_worker(single_video=True)
    assert results[0][0] is True
    assert worker.song_entry["url"] == CANONICAL
    assert fake_yt_dlp.last_opts["noplaylist"] is True


def test_search_results_with_entries_still_work(fake_yt_dlp):
    fake_yt_dlp.result = {"entries": [{"id": VIDEO, "title": "Song", "uploader": "A", "duration": 100, "ie_key": "Youtube"}]}
    worker, results = _run_worker()
    assert results[0][0] is True
    assert fake_yt_dlp.last_opts["noplaylist"] is False


def test_empty_result_reports_not_found(fake_yt_dlp):
    fake_yt_dlp.result = {}
    _, results = _run_worker(single_video=True)
    assert results[0][0] is False


def _spam_service(allowlist=""):
    service = SpamService.__new__(SpamService)
    service.filters = {"link_protection": {"is_active": True, "penalty": "delete", "duration": 0, "exclude_group": "", "max_amount": 0, "allowlist": allowlist, "apply_kick": True, "apply_twitch": True}}
    service.user_history = {}
    service._apply_penalty = MagicMock()
    return service


def test_link_protection_blocks_youtube_link_in_normal_message():
    service = _spam_service()
    assert service.is_spam("viewer", f"mira https://youtu.be/{VIDEO}", [], "1", 1) is True


def test_link_protection_lets_song_request_youtube_link_through():
    service = _spam_service()
    assert service.is_spam("viewer", f"!sr https://youtu.be/{VIDEO}", [], "1", 1, youtube_links_allowed=True) is False


def test_song_request_exemption_does_not_cover_other_domains():
    service = _spam_service()
    assert service.is_spam("viewer", "!sr https://evil.example.com/x", [], "1", 1, youtube_links_allowed=True) is True


def test_peek_plugin_tag_resolves_command_and_aliases(qapp):
    storage = MagicMock()
    storage.load_all.return_value = [
        {"trigger": "!sr", "response": "[PLUGIN_MUSIC_SR]", "is_active": True, "cooldown": 5, "aliases": "!pedir", "is_regex": False, "permission": "everyone"},
        {"trigger": "!off", "response": "[PLUGIN_MUSIC_SKIP]", "is_active": False, "cooldown": 5, "aliases": "", "is_regex": False, "permission": "everyone"},
    ]
    service = CommandService(storage)
    assert service.peek_plugin_tag("!SR https://youtu.be/x") == "[PLUGIN_MUSIC_SR]"
    assert service.peek_plugin_tag("!pedir algo") == "[PLUGIN_MUSIC_SR]"
    assert service.peek_plugin_tag("!off") == ""
    assert service.peek_plugin_tag("hola") == ""
