# resources\tests\test_po_token_minter_service.py
"""Pruebas de la máquina de estados que atiende las peticiones de PO token."""

import pytest

from backend.interfaces import PoTokenAnswer
from backend.services.music import po_token_minter_service as mod
from backend.services.music.po_token_minter_service import PoTokenMinter
from backend.services.music.po_token_service import PoTokenService


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class FakePage:
    def __init__(self, binding):
        self.asked = [binding]
        self.reply = None
        self.closed = False

    def ask(self, binding):
        self.asked.append(binding)
        self.reply = None

    def answer(self):
        return self.reply

    def close(self):
        self.closed = True


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def service(clock):
    return PoTokenService(clock=clock)


@pytest.fixture
def pages():
    return []


@pytest.fixture
def minter(service, clock, pages):
    def open_page(binding):
        page = FakePage(binding)
        pages.append(page)
        return page

    return PoTokenMinter(service, open_page, clock=clock)


def test_without_an_ask_no_page_is_opened(minter, pages):
    assert minter.tick() == mod.IDLE_TICK_SECONDS
    assert pages == []


def test_an_ask_opens_a_page_for_its_binding(minter, service, pages):
    service.token("vid")
    assert minter.tick() == mod.BUSY_TICK_SECONDS
    assert pages[0].asked == ["vid"]


def test_a_minted_token_is_filed_and_the_page_stays_warm(minter, service, pages):
    service.token("vid")
    minter.tick()
    pages[0].reply = PoTokenAnswer("vid", token="tok")
    minter.tick()

    assert service.minted("vid") == "tok"
    assert service.warm() is True
    assert pages[0].closed is False


def test_an_answer_for_another_binding_is_ignored(minter, service, pages):
    service.token("vid")
    minter.tick()
    pages[0].reply = PoTokenAnswer("stale", token="old")
    minter.tick()

    assert service.minted("vid") is None
    assert service.minted("stale") is None


def test_a_page_error_closes_it_and_holds_the_minter_off(minter, service, pages):
    service.token("vid")
    minter.tick()
    pages[0].reply = PoTokenAnswer("vid", error="no client")
    minter.tick()

    assert pages[0].closed is True
    assert service.warm() is False
    assert service.token("other") is None
    assert service.wanted() is None


def test_a_silent_page_is_given_up_on_after_the_patience(minter, service, pages, clock):
    service.token("vid")
    minter.tick()
    clock.now += mod.PATIENCE_SECONDS - 1
    minter.tick()
    assert pages[0].closed is False

    clock.now += 2
    minter.tick()
    assert pages[0].closed is True


def test_a_warm_page_serves_the_next_ask_and_closes_after_lingering(minter, service, pages, clock):
    service.token("one")
    minter.tick()
    pages[0].reply = PoTokenAnswer("one", token="t1")
    minter.tick()

    clock.now += 1
    service.token("two")
    minter.tick()
    assert pages[0].asked == ["one", "two"]
    pages[0].reply = PoTokenAnswer("two", token="t2")
    minter.tick()
    assert service.minted("two") == "t2"

    clock.now += mod.LINGER_SECONDS + 1
    minter.tick()
    assert pages[0].closed is True
    assert service.warm() is False
    assert len(pages) == 1


def test_a_factory_that_raises_counts_as_a_failure(service, clock):
    def broken(_binding):
        raise RuntimeError("no engine")

    minter = PoTokenMinter(service, broken, clock=clock)
    service.token("vid")
    assert minter.tick() == mod.IDLE_TICK_SECONDS
    assert service.token("other") is None
    assert service.wanted() is None
