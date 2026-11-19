# resources\tests\test_youtube_po_token_provider.py
"""Pruebas del proveedor de PO tokens que conecta yt-dlp con el relevo de MiniKick."""

from unittest import mock

import pytest
from yt_dlp.extractor.youtube.pot._registry import _pot_providers
from yt_dlp.extractor.youtube.pot.provider import (
    PoTokenContext,
    PoTokenProviderError,
    PoTokenProviderRejectedRequest,
    PoTokenRequest,
)

from backend.providers.music import youtube_po_token_provider as mod
from backend.providers.music.youtube_po_token_provider import MiniKickPTP


class FakeSource:
    def __init__(self, token=None, minted_after=None, warm=False):
        self._token = token
        self._minted_after = minted_after
        self._warm = warm
        self.asked = []
        self.polls = 0

    def token(self, binding):
        self.asked.append(binding)
        return self._token

    def minted(self, binding):
        self.polls += 1
        if self._minted_after is not None and self.polls >= self._minted_after:
            return "late-token"
        return None

    def warm(self):
        return self._warm


def _provider(source):
    MiniKickPTP._source = source
    return MiniKickPTP(mock.Mock(), mock.Mock(), {})


def _request(client="WEB", context=PoTokenContext.GVS, **kwargs):
    kwargs.setdefault("visitor_data", "visitor-123")
    return PoTokenRequest(context=context, innertube_context={"client": {"clientName": client}}, **kwargs)


@pytest.fixture(autouse=True)
def fast_waits(monkeypatch):
    monkeypatch.setattr(mod, "POLL_SECONDS", 0.001)
    monkeypatch.setattr(mod, "WARM_WAIT_SECONDS", 0.05)
    monkeypatch.setattr(mod, "COLD_WAIT_SECONDS", 0.2)
    yield
    MiniKickPTP._source = None


def test_provider_is_unavailable_without_a_source():
    assert _provider(None).is_available() is False


def test_ready_token_is_returned_without_waiting():
    source = FakeSource(token="ready")
    response = _provider(source).request_pot(_request())

    assert response.po_token == "ready"
    assert source.asked == ["visitor-123"]
    assert source.polls == 0


def test_a_missing_token_is_waited_for_and_asked_only_once():
    source = FakeSource(minted_after=3)
    response = _provider(source).request_pot(_request())

    assert response.po_token == "late-token"
    assert source.asked == ["visitor-123"]


def test_a_warm_minter_is_given_less_time_than_a_cold_one():
    cold, warm = FakeSource(), FakeSource(warm=True)
    for source in (cold, warm):
        with pytest.raises(PoTokenProviderError):
            _provider(source).request_pot(_request())

    assert cold.polls > warm.polls > 0


def test_failing_to_get_a_token_is_an_expected_error():
    with pytest.raises(PoTokenProviderError) as error:
        _provider(FakeSource()).request_pot(_request())

    assert error.value.expected is True


def test_clients_that_do_not_use_web_po_tokens_are_rejected_without_waiting():
    source = FakeSource()
    with pytest.raises(PoTokenProviderRejectedRequest):
        _provider(source).request_pot(_request(client="IOS"))

    assert source.asked == [] and source.polls == 0


def test_a_request_without_binding_is_rejected():
    with pytest.raises(PoTokenProviderRejectedRequest):
        _provider(FakeSource()).request_pot(_request(visitor_data=None))


def test_player_requests_bind_to_the_video_id():
    source = FakeSource(token="t")
    _provider(source).request_pot(_request(context=PoTokenContext.PLAYER, video_id="abc123"))

    assert source.asked == ["abc123"]


def test_registering_twice_registers_once_and_swaps_the_source(monkeypatch):
    monkeypatch.setattr(mod, "_registered", False)
    _pot_providers.value.pop(MiniKickPTP.PROVIDER_KEY, None)
    first, second = FakeSource(), FakeSource()
    try:
        mod.register_po_token_provider(first)
        mod.register_po_token_provider(second)
        assert _pot_providers.value[MiniKickPTP.PROVIDER_KEY] is MiniKickPTP
        assert MiniKickPTP._source is second
    finally:
        _pot_providers.value.pop(MiniKickPTP.PROVIDER_KEY, None)
