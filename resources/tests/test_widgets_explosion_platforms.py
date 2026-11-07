from unittest.mock import MagicMock

import pytest

from backend.controllers.widgets_controller import WidgetsController


def _controller(qapp, config):
    widget_service = MagicMock()
    widget_service.get_all_widgets.return_value = {}
    widget_service.get_widget.side_effect = lambda w_id: (
        {"is_active": True, "config": config} if w_id == "explosion" else {"is_active": False, "config": {}}
    )
    overlay = MagicMock()
    return WidgetsController(None, widget_service, MagicMock(), overlay_server=overlay), overlay


def _explosions(overlay):
    return [c.args[1] for c in overlay.trigger_widget_event.call_args_list if c.args[0] == "emote_explosion"]


@pytest.mark.parametrize("platform,content,tag", [
    ("kick", "hi [emote:123:KEKW]", ""),
    ("twitch", "Kappa", "25:0-4"),
])
def test_explosion_fires_for_enabled_platform(qapp, platform, content, tag):
    controller, overlay = _controller(qapp, {})
    controller.handle_chat_message("u", content, "#fff", [], platform, tag)
    assert len(_explosions(overlay)) == 1


def test_explosion_skips_disabled_platform_only(qapp):
    controller, overlay = _controller(qapp, {"show_twitch": False})
    controller.handle_chat_message("u", "Kappa", "#fff", [], "twitch", "25:0-4")
    assert _explosions(overlay) == []
    controller.handle_chat_message("u", "hi [emote:123:KEKW]", "#fff", [], "kick", "")
    assert len(_explosions(overlay)) == 1


def test_explosion_ignores_emojis(qapp):
    controller, overlay = _controller(qapp, {})
    controller.handle_chat_message("u", "gg 🔥", "#fff", [], "kick", "")
    assert _explosions(overlay) == []
