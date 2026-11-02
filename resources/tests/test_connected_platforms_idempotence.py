# resources\tests\test_connected_platforms_idempotence.py

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from frontend.views.alerts_view import AlertsView
from frontend.views.commands_view import CommandView
from frontend.views.rewards_view import RewardsView
from frontend.views.timers_view import TimersView

_STATE = {"kick": True, "twitch": False, "youtube": False, "tiktok": False}


def _commands():
    view = SimpleNamespace(_raw_commands=[{"trigger": "!a"}], populate_table=MagicMock())
    return view, CommandView.set_connected_platforms, view.populate_table


def _timers():
    view = SimpleNamespace(connected_platforms={"kick": True, "twitch": True}, _raw_timers=[{"id": 1}], populate_table=MagicMock())
    return view, TimersView.set_connected_platforms, view.populate_table


def _rewards():
    view = SimpleNamespace(connected_platforms={"kick": True, "twitch": True}, _apply_filters=MagicMock())
    return view, RewardsView.set_connected_platforms, view._apply_filters


def _alerts():
    view = SimpleNamespace(connected_platforms={}, _update_platform_connection_ui=MagicMock())
    return view, AlertsView.set_connected_platforms, view._update_platform_connection_ui


FACTORIES = [_commands, _timers, _rewards, _alerts]


@pytest.mark.parametrize("factory", FACTORIES)
def test_same_state_does_not_rebuild_the_view_again(factory):
    view, setter, rebuild = factory()

    setter(view, dict(_STATE))
    setter(view, dict(_STATE))
    setter(view, dict(_STATE))

    assert rebuild.call_count == 1
    assert view.connected_platforms == _STATE


@pytest.mark.parametrize("factory", FACTORIES)
def test_changed_state_rebuilds_and_is_stored(factory):
    view, setter, rebuild = factory()
    setter(view, dict(_STATE))

    updated = {**_STATE, "twitch": True}
    setter(view, updated)

    assert rebuild.call_count == 2
    assert view.connected_platforms == updated


@pytest.mark.parametrize("factory", FACTORIES)
def test_view_keeps_its_own_copy_of_the_state(factory):
    view, setter, rebuild = factory()
    caller_state = dict(_STATE)
    setter(view, caller_state)

    caller_state["kick"] = False

    assert view.connected_platforms["kick"] is True
    setter(view, dict(_STATE))
    assert rebuild.call_count == 1


@pytest.mark.parametrize("factory", FACTORIES)
def test_none_is_treated_as_empty_state(factory):
    view, setter, rebuild = factory()
    setter(view, None)
    setter(view, {})
    assert view.connected_platforms == {}
    assert rebuild.call_count <= 1


def test_rewards_view_ignores_platforms_it_does_not_use():
    view, setter, rebuild = _rewards()
    view.connected_platforms = {"kick": True, "twitch": False}

    setter(view, {"kick": True, "twitch": False, "youtube": True, "tiktok": False})
    assert rebuild.call_count == 0

    setter(view, {"kick": True, "twitch": True, "youtube": True, "tiktok": False})
    assert rebuild.call_count == 1
    assert view.connected_platforms["twitch"] is True
