# resources\tests\test_spam_filters.py
"""Pruebas de los filtros de spam del chat (enlaces y umbrales)."""

import pytest

from backend.services.chat.spam_service import SpamService
from backend.utils.io_background_utils import flush_network_io


class _Storage:
    def __init__(self, filters):
        self._filters = filters

    def load_all(self):
        return self._filters

    def save_filter(self, filter_id, config):
        self._filters[filter_id] = config


def _service(filter_id, **config):
    base = {"is_active": True, "penalty": "delete", "apply_kick": True, "apply_twitch": True}
    base.update(config)
    return SpamService(_Storage({filter_id: base}))


def _is_spam(service, message, user="viewer"):
    result = service.is_spam(user, message, [], "m1", 1, platform="kick")
    flush_network_io(2.0)
    return result


@pytest.mark.parametrize("message,expected", [
    ("mira https://kick.com/canal", False),
    ("mira https://www.kick.com/canal", False),
    ("mira https://clips.kick.com/x", False),
    ("mira https://notkick.com/x", True),
    ("mira https://evil.example/?kick.com", True),
    ("mira https://kick.com.evil.example/x", True),
    ("mira www.evil.example", True),
])
def test_link_allowlist_compares_hostnames(message, expected):
    service = _service("link_protection", allowlist="kick.com")
    assert _is_spam(service, message) is expected


def test_link_without_allowlist_is_blocked():
    service = _service("link_protection", allowlist="")
    assert _is_spam(service, "https://kick.com/x") is True


@pytest.mark.parametrize("filter_id,message", [
    ("caps_protection", "Hola amigos como estan"),
    ("emote_protection", "hola [emote:123:kekw] amigos"),
    ("repetition_protection", "hola mundo"),
])
@pytest.mark.parametrize("max_amount", [0, None])
def test_unset_threshold_falls_back_to_default_instead_of_flagging_everything(filter_id, message, max_amount):
    service = _service(filter_id, max_amount=max_amount)
    assert _is_spam(service, message) is False


def test_caps_filter_still_triggers_above_default_threshold():
    service = _service("caps_protection", max_amount=0)
    assert _is_spam(service, "ESTO ES UN MENSAJE MUY GRITADO") is True
