from unittest.mock import MagicMock

from PySide6.QtCore import QObject, Signal

from backend.connections import ConnectionHub
from frontend.window.integrations_status import IntegrationsStatusPresenter


class _Connection(QObject):
    state_changed = Signal()

    def __init__(self, connected=False, channel=""):
        super().__init__()
        self.is_connected = connected
        self.channel = channel


def _connections():
    return {
        "kick": _Connection(True, "kick_channel"),
        "twitch": _Connection(False, "twitch_channel"),
        "youtube": _Connection(True, "youtube_channel"),
        "tiktok": _Connection(False, "tiktok_channel"),
    }


def test_connection_hub_reports_status_and_authenticated_platforms(qapp):
    connections = _connections()
    auth_state = {"kick": False, "twitch": True}
    hub = ConnectionHub(
        connections,
        authenticated_providers={
            platform: lambda platform=platform: auth_state[platform]
            for platform in ("kick", "twitch")
        },
    )
    changed = []
    hub.status_changed.connect(lambda: changed.append(True))

    assert hub.get_integration_statuses()["youtube"].channel == "youtube_channel"
    assert hub.get_connected_platforms() == {
        "kick": True,
        "twitch": True,
        "youtube": True,
        "tiktok": False,
    }

    connections["tiktok"].state_changed.emit()

    assert changed == [True]


def test_integrations_presenter_refreshes_dashboard_and_existing_views(qapp):
    connections = _connections()
    hub = ConnectionHub(
        connections,
        authenticated_providers={
            "kick": lambda: False,
            "twitch": lambda: True,
        },
    )
    dashboard = MagicMock()
    metrics = MagicMock()
    metrics.platform_messages.side_effect = {
        "kick": 1,
        "twitch": 2,
        "youtube": 3,
        "tiktok": 4,
    }.get
    settings_view = MagicMock()
    chat_view = MagicMock()
    alerts_view = MagicMock()
    _presenter = IntegrationsStatusPresenter(
        hub=hub,
        dashboard_controller=dashboard,
        session_metrics=metrics,
        settings_view_provider=lambda: settings_view,
        platform_views_provider=lambda: (chat_view, None, alerts_view),
    )

    connections["youtube"].channel = "updated_channel"
    connections["youtube"].state_changed.emit()

    dashboard.set_kick_status.assert_called_once_with(
        connected=True,
        channel="kick_channel",
        msg_count=1,
    )
    dashboard.set_twitch_status.assert_called_once_with(
        connected=False,
        channel="twitch_channel",
        msg_count=2,
    )
    dashboard.set_youtube_status.assert_called_once_with(
        connected=True,
        channel="updated_channel",
        msg_count=3,
    )
    dashboard.set_tiktok_status.assert_called_once_with(
        connected=False,
        channel="tiktok_channel",
        msg_count=4,
    )
    settings_view.set_integrations_status.assert_called_once_with(
        kick_connected=True,
        kick_channel="kick_channel",
        twitch_connected=False,
        twitch_channel="twitch_channel",
        youtube_connected=True,
        youtube_channel="updated_channel",
        tiktok_connected=False,
        tiktok_channel="tiktok_channel",
    )
    expected_connected = {
        "kick": True,
        "twitch": True,
        "youtube": True,
        "tiktok": False,
    }
    chat_view.set_connected_platforms.assert_called_once_with(expected_connected)
    alerts_view.set_connected_platforms.assert_called_once_with(expected_connected)
