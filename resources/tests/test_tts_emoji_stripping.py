# resources\tests\test_tts_emoji_stripping.py

from unittest.mock import MagicMock, patch

import pytest

from backend.handlers.spam_handler import ChatFilterHandler
from backend.utils import strip_emojis


class _I18n:
    def get(self, key: str, default: str = "") -> str:
        return {"chat.status.web_link": "un enlace web"}.get(key, default or key)


@pytest.mark.parametrize("raw, expected", [
    ("hola 😂 amigos", "hola amigos"),
    ("gracias🙏", "gracias"),
    ("hola😂mundo", "hola mundo"),
    ("😂😂😂", ""),
    ("fuego 🔥🔥 total", "fuego total"),
    ("corazon ❤️ rojo", "corazon rojo"),
    ("familia 👨‍👩‍👧‍👦 unida", "familia unida"),
    ("saludo 👋🏽 amigo", "saludo amigo"),
    ("bandera 🇲🇽 mexico", "bandera mexico"),
    ("bandera 🏴󠁧󠁢󠁥󠁮󠁧󠁿 inglesa", "bandera inglesa"),
    ("numero 1️⃣ gana", "numero gana"),
    ("estrella ⭐ y rayo ⚡", "estrella y rayo"),
    ("check ✅ y cruz ❌", "check y cruz"),
    ("reloj ⌚ ahora ⏰", "reloj ahora"),
])
def test_strip_emojis_removes_pictographs_and_sequences(raw, expected):
    assert strip_emojis(raw) == expected


@pytest.mark.parametrize("text", [
    "Hola, ¿cómo estás? ¡Qué bueno!",
    "mañana a las 10:30 en el canal #1",
    "100% seguro, 5 + 3 = 8",
    "precio $20 y 15€ © 2026",
    "ñandú, pingüino, acción, über",
    "texto con símbolos: @usuario & co.",
    "日本語のテキスト",
    "1 2 3 y 10",
])
def test_strip_emojis_keeps_regular_text_untouched(text):
    assert strip_emojis(text) == text


def test_strip_emojis_keeps_zero_width_joiner_between_non_emoji_characters():
    text = "\u0915\u094d\u200d\u0937"
    assert strip_emojis(text) == text


def test_strip_emojis_handles_empty_input():
    assert strip_emojis("") == ""
    assert strip_emojis(None) == ""


def test_clean_message_for_tts_drops_emojis():
    handler = ChatFilterHandler(i18n=_I18n(), service=None)
    assert handler.clean_message_for_tts("jajaja 😂😂 que bueno 🔥") == "jajaja que bueno"
    assert handler.clean_message_for_tts("😂🔥🙏") == ""


def test_tts_manager_say_strips_emojis_and_ignores_emoji_only_text():
    from backend.services.chat.tts_service import TTSManager

    with patch("backend.services.chat.tts_service.threading.Thread", return_value=MagicMock()):
        manager = TTSManager()
    manager.say("Juan🔥 dice: hola 😂")
    manager.say("😂😂")
    manager.say("   ")

    assert manager.text_queue.qsize() == 1
    assert manager.text_queue.get_nowait() == ("Juan dice: hola", None)
