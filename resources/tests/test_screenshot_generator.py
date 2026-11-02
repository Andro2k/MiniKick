from types import SimpleNamespace
from unittest.mock import MagicMock

from resources.tools.generate_screenshots import _navigate_to_view, _shutdown_window


def test_screenshot_generator_navigates_through_coordinator():
    handle_navigation = MagicMock()
    window = SimpleNamespace(
        navigation=SimpleNamespace(handle_navigation=handle_navigation)
    )

    _navigate_to_view(window, "Dashboard")

    handle_navigation.assert_called_once_with("Dashboard")


def test_screenshot_generator_waits_for_orderly_shutdown():
    window = SimpleNamespace(_cleanup_complete=False, _force_quit=MagicMock())
    app = SimpleNamespace(
        processEvents=lambda: setattr(window, "_cleanup_complete", True)
    )

    _shutdown_window(app, window)

    window._force_quit.assert_called_once_with()
    assert window._cleanup_complete is True
