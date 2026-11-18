# resources\tests\test_po_token_service.py
"""Pruebas del relevo del PO token de YouTube (tokens vigentes, peticiones y espera tras fallos)."""

import pytest

from backend.services.music.po_token_service import (
    KEEP_SECONDS,
    SLOWEST_SECONDS,
    SOONEST_SECONDS,
    PoTokenService,
    hold_seconds,
)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def service(clock):
    return PoTokenService(clock=clock)


def test_unknown_binding_records_one_ask_and_returns_none(service):
    assert service.token("vid") is None
    assert service.wanted() == "vid"
    assert service.wanted() is None


def test_minted_never_records_an_ask(service):
    assert service.minted("vid") is None
    assert service.wanted() is None


def test_given_token_is_returned_until_it_expires(service, clock):
    service.give("vid", "tok")
    assert service.token("vid") == "tok"
    assert service.wanted() is None

    clock.now += KEEP_SECONDS - 1
    assert service.minted("vid") == "tok"
    clock.now += 2
    assert service.minted("vid") is None


def test_failure_holds_off_new_asks_then_releases(service, clock):
    service.failed()
    assert service.token("vid") is None
    assert service.wanted() is None

    clock.now += SOONEST_SECONDS + 0.1
    assert service.token("vid") is None
    assert service.wanted() == "vid"


def test_give_forgets_earlier_failures(service, clock):
    service.failed()
    service.failed()
    service.give("other", "tok")
    assert service.token("vid") is None
    assert service.wanted() == "vid"


def test_hold_doubles_and_is_capped():
    assert [hold_seconds(n) for n in (0, 1, 2, 3)] == [5.0, 5.0, 10.0, 20.0]
    assert hold_seconds(100) == SLOWEST_SECONDS


def test_warm_flag_round_trips(service):
    assert service.warm() is False
    service.set_warm(True)
    assert service.warm() is True


def test_expired_tokens_are_purged_on_give(service, clock):
    service.give("old", "a")
    clock.now += KEEP_SECONDS + 1
    service.give("new", "b")
    assert service.minted("old") is None
    assert service.minted("new") == "b"
