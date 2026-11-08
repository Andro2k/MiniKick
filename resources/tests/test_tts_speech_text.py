# resources\tests\test_tts_speech_text.py

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from backend.handlers.spam_handler import ChatFilterHandler
from backend.services.chat.tts_service import DEFAULT_MESSAGE_GAP_S, TTSManager
from backend.utils import apply_pronunciations, normalize_symbols_for_speech, speakable_username


class _I18n:
    _TEXTS = {"chat.status.web_link": "un enlace web", "chat.status.user_says": "{user} dice: {message}"}

    def get(self, key: str, default: str = "") -> str:
        return self._TEXTS.get(key, default or key)


@pytest.mark.parametrize("raw, expected", [
    ("q onda", "que onda"),
    ("Q pasa xq no vienes", "que pasa porque no vienes"),
    ("tmb quiero?", "también quiero?"),
    ("(q) raro", "(que) raro"),
    ("gg wp", "yi yi wp"),
    ("GG", "yi yi"),
    ("los streamers y sus followers", "los estrímers y sus fólouers"),
    ("5 likes y mucho hype!", "5 láiks y mucho jaip!"),
    ("salu2 a todos", "saludos a todos"),
    ("gl hf", "yi el eich ef"),
])
def test_apply_pronunciations_replaces_whole_tokens(raw, expected):
    assert apply_pronunciations(raw) == expected


@pytest.mark.parametrize("text", [
    "que bueno",
    "Q&A de hoy",
    "q-learning es otra cosa",
    "a/q/b",
    "streaming y following",
    "hola amigos",
    "",
])
def test_apply_pronunciations_leaves_other_text_untouched(text):
    assert apply_pronunciations(text) == text


def test_normalize_symbols_drops_mentions_hashtags_and_inner_underscores():
    assert normalize_symbols_for_speech("@juan mira #1 de pro_gamer") == "juan mira 1 de pro gamer"
    assert normalize_symbols_for_speech("juan@gmail.com y solo # suelto") == "juan@gmail.com y solo # suelto"


@pytest.mark.parametrize("name, expected", [
    ("xX_ProGamer_Xx", "Pro Gamer"),
    ("Juan_Carlos", "Juan Carlos"),
    ("Juan.Perez", "Juan Perez"),
    ("Juan2005", "Juan"),
    ("Juan_123456", "Juan"),
    ("Juan🔥", "Juan"),
    ("SrPepe", "Sr Pepe"),
    ("NASAFan", "NASA Fan"),
    ("ÁlvaroLópez", "Álvaro López"),
    ("Max", "Max"),
    ("R2D2", "R2D2"),
    ("Pro99", "Pro99"),
    ("12345", "12345"),
    ("", ""),
])
def test_speakable_username(name, expected):
    assert speakable_username(name) == expected


def test_clean_message_for_tts_applies_symbol_and_pronunciation_rules():
    handler = ChatFilterHandler(i18n=_I18n(), service=None)
    assert handler.clean_message_for_tts("@juan q onda #1 jajaja 😂") == "juan que onda 1 jajaja"
    assert handler.clean_message_for_tts("xq no hay stream hoy") == "porque no hay estrim hoy"


def test_build_spoken_text_cleans_the_name_and_respects_read_name():
    handler = ChatFilterHandler(i18n=_I18n(), service=None)
    assert handler.build_spoken_text("xX_ProGamer_Xx", "hola") == "Pro Gamer dice: hola"
    assert handler.build_spoken_text("Juan🔥", "hola") == "Juan dice: hola"
    assert handler.build_spoken_text("Juan", "hola", read_name=False) == "hola"


def _manager_without_threads() -> TTSManager:
    with patch("backend.services.chat.tts_service.threading.Thread", return_value=MagicMock()):
        return TTSManager()


def test_message_gap_has_a_pause_by_default_and_can_be_changed():
    manager = _manager_without_threads()
    assert manager._message_gap_s == DEFAULT_MESSAGE_GAP_S > 0
    manager.set_message_gap(1.5)
    assert manager._message_gap_s == 1.5
    manager.set_message_gap(-3)
    assert manager._message_gap_s == 0.0


def test_wait_message_gap_waits_only_the_remaining_time():
    manager = _manager_without_threads()
    manager.set_message_gap(0.3)
    manager._last_speech_end = time.monotonic()
    started = time.monotonic()
    assert manager._wait_message_gap(manager._stop_generation) is True
    assert 0.25 <= time.monotonic() - started < 1.0


def test_wait_message_gap_does_not_delay_the_first_message_or_when_disabled():
    manager = _manager_without_threads()
    started = time.monotonic()
    assert manager._wait_message_gap(manager._stop_generation) is True
    manager.set_message_gap(0)
    manager._last_speech_end = time.monotonic()
    assert manager._wait_message_gap(manager._stop_generation) is True
    assert time.monotonic() - started < 0.2


def test_stop_cancels_the_message_waiting_in_the_gap():
    manager = _manager_without_threads()
    manager.set_message_gap(3.0)
    manager._last_speech_end = time.monotonic()
    generation = manager._stop_generation
    threading.Timer(0.1, manager.stop).start()
    started = time.monotonic()
    assert manager._wait_message_gap(generation) is False
    assert time.monotonic() - started < 1.5


def test_worker_leaves_a_pause_between_two_queued_messages():
    class FakeProvider:
        def __init__(self):
            self.spans = []

        def speak(self, text, voice_id=None):
            started = time.monotonic()
            time.sleep(0.05)
            self.spans.append((text, started, time.monotonic()))

        def stop(self):
            pass

    manager = TTSManager()
    provider = FakeProvider()
    manager._providers["piper"] = provider
    manager.set_message_gap(0.3)
    try:
        manager.say("mensaje uno")
        manager.say("mensaje dos")
        deadline = time.time() + 5
        while len(provider.spans) < 2 and time.time() < deadline:
            time.sleep(0.02)
        assert [span[0] for span in provider.spans] == ["mensaje uno", "mensaje dos"]
        assert provider.spans[1][1] - provider.spans[0][2] >= 0.25
    finally:
        manager.shutdown()
