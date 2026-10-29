# resources\tests\test_music_controller_chat_context.py

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from backend.controllers.music_controller import MusicController


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _controller(view=None):
    provider = MagicMock()
    provider.get_current_song.return_value = None
    return MusicController(
        view=view,
        command_service=MagicMock(get_all_commands=MagicMock(return_value=[])),
        toast_manager=MagicMock(),
        i18n=MagicMock(),
        settings_storage=None,
        music_provider=provider,
    ), provider


def test_controller_exposes_public_chat_context(qapp):
    controller, _ = _controller()
    for name in ("send_chat_message", "refresh_now_playing", "apply_chat_volume"):
        assert callable(getattr(controller, name))
    assert not hasattr(controller, "_user_last_request_time")
    controller.shutdown()


def test_send_chat_message_goes_through_command_service(qapp):
    controller, _ = _controller()
    controller.send_chat_message("hola", platform="twitch")
    controller.command_service.send_response.assert_called_once_with("hola", platform="twitch")
    controller.shutdown()


def test_apply_chat_volume_updates_provider_and_view_slider(qapp):
    view = MagicMock()
    controller, provider = _controller(view=view)
    view.slider_vol.reset_mock()

    controller.apply_chat_volume(42)

    provider.set_volume.assert_called_with(42)
    view.slider_vol.setValue.assert_called_with(42)
    view.lbl_vol_perc.setText.assert_called_with("42%")
    controller.shutdown()


def test_apply_chat_volume_without_view_only_updates_provider(qapp):
    controller, provider = _controller(view=None)
    controller.apply_chat_volume(10)
    provider.set_volume.assert_called_with(10)
    assert controller.current_volume == 10
    controller.shutdown()
