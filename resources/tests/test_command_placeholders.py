# resources\tests\test_command_placeholders.py
"""Pruebas de la sustitución segura de {user}, {touser} y {random} en respuestas de comandos."""

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from backend.services.chat.commands_service import CommandService


@pytest.fixture(scope="module")
def qapp():
    return QCoreApplication.instance() or QCoreApplication([])


def _service(response):
    storage = MagicMock()
    storage.load_all.return_value = [{
        "trigger": "!hug", "response": response, "is_active": True, "cooldown": 0,
        "aliases": "", "is_regex": False, "permission": "everyone",
    }]
    service = CommandService(storage)
    service.twitch_worker = MagicMock()
    return service


@pytest.mark.parametrize("arg,expected", [
    ("/ban", "ban es genial"),
    ("!otrocmd", "otrocmd es genial"),
    (".disconnect", "disconnect es genial"),
    ("@ana", "ana es genial"),
    ("@", "viewer es genial"),
])
def test_touser_cannot_start_the_bot_message_with_a_chat_command(qapp, arg, expected):
    service = _service("{touser} es genial")

    handled, _, _, _ = service.process_incoming_message("viewer", f"!hug {arg}", [], platform="twitch")

    assert handled is True
    service.twitch_worker.send_bot_message.assert_called_once_with(expected)


def test_placeholder_values_are_not_substituted_twice():
    rendered = CommandService._render_response("{touser}", "viewer", "{random}")
    assert rendered == "{random}"


def test_touser_is_length_limited_and_random_is_in_range():
    rendered = CommandService._render_response("{touser} {random}", "viewer", "x" * 500)
    name, number = rendered.split(" ")
    assert len(name) == CommandService._MAX_PLACEHOLDER_LENGTH
    assert 1 <= int(number) <= 100
