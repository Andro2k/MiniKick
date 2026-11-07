# resources\tests\test_delete_confirmation_dialogs.py

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QWidget
from frontend.common import BrandColors, get_assets_path, get_global_qss
from frontend.dialogs.base_dialog import build_icon_badge
from frontend.views.commands_view import CommandView
from frontend.views.timers_view import TimersView
from frontend.views.rewards_view import RewardsView
from frontend.dialogs.piper_dialog import PiperVoicesDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

@pytest.fixture
def mock_i18n():
    i18n = MagicMock()
    i18n.get.side_effect = lambda key: f"translated_{key}"
    return i18n

def test_commands_view_delete_confirmation_accepted(qapp, mock_i18n):
    view = CommandView(mock_i18n)
    signal_spy = MagicMock()
    view.delete_requested.connect(signal_spy)

    with patch("frontend.dialogs.ModernConfirmDialog.exec", return_value=QDialog.DialogCode.Accepted):
        view._confirm_delete_command("!mycmd")

    signal_spy.assert_called_once_with("!mycmd")

def test_commands_view_delete_confirmation_rejected(qapp, mock_i18n):
    view = CommandView(mock_i18n)
    signal_spy = MagicMock()
    view.delete_requested.connect(signal_spy)

    with patch("frontend.dialogs.ModernConfirmDialog.exec", return_value=QDialog.DialogCode.Rejected):
        view._confirm_delete_command("!mycmd")

    signal_spy.assert_not_called()

def test_timers_view_delete_confirmation_accepted(qapp, mock_i18n):
    view = TimersView(mock_i18n)
    signal_spy = MagicMock()
    view.delete_requested.connect(signal_spy)

    with patch("frontend.dialogs.ModernConfirmDialog.exec", return_value=QDialog.DialogCode.Accepted):
        view._confirm_delete_timer(42, "Timer Promocion")

    signal_spy.assert_called_once_with(42)

def test_timers_view_delete_confirmation_rejected(qapp, mock_i18n):
    view = TimersView(mock_i18n)
    signal_spy = MagicMock()
    view.delete_requested.connect(signal_spy)

    with patch("frontend.dialogs.ModernConfirmDialog.exec", return_value=QDialog.DialogCode.Rejected):
        view._confirm_delete_timer(42, "Timer Promocion")

    signal_spy.assert_not_called()

def test_rewards_view_delete_confirmation_accepted(qapp, mock_i18n):
    view = RewardsView(mock_i18n)
    signal_spy = MagicMock()
    view.delete_requested.connect(signal_spy)

    with patch("frontend.dialogs.ModernConfirmDialog.exec", return_value=QDialog.DialogCode.Accepted):
        view._confirm_delete_reward("reward_hydrated", "Beber Agua")

    signal_spy.assert_called_once_with("reward_hydrated")

def test_rewards_view_delete_confirmation_rejected(qapp, mock_i18n):
    view = RewardsView(mock_i18n)
    signal_spy = MagicMock()
    view.delete_requested.connect(signal_spy)

    with patch("frontend.dialogs.ModernConfirmDialog.exec", return_value=QDialog.DialogCode.Rejected):
        view._confirm_delete_reward("reward_hydrated", "Beber Agua")

    signal_spy.assert_not_called()

def test_piper_dialog_delete_confirmation_accepted(qapp, mock_i18n):
    mock_mgr = MagicMock()
    mock_mgr.get_installed_voices.return_value = []
    mock_mgr.get_catalog.return_value = []
    mock_mgr.delete_voice.return_value = True

    dialog = PiperVoicesDialog(mock_i18n, tts_service=MagicMock(), manager=mock_mgr)

    with patch("frontend.dialogs.ModernConfirmDialog.exec", return_value=QDialog.DialogCode.Accepted):
        dialog._delete_voice("es_ES-test-medium")

    mock_mgr.delete_voice.assert_called_once_with("es_ES-test-medium")

def test_piper_dialog_delete_confirmation_rejected(qapp, mock_i18n):
    mock_mgr = MagicMock()
    mock_mgr.get_installed_voices.return_value = []
    mock_mgr.get_catalog.return_value = []

    dialog = PiperVoicesDialog(mock_i18n, tts_service=MagicMock(), manager=mock_mgr)

    with patch("frontend.dialogs.ModernConfirmDialog.exec", return_value=QDialog.DialogCode.Rejected):
        dialog._delete_voice("es_ES-test-medium")

    mock_mgr.delete_voice.assert_not_called()


def test_icon_badge_uses_theme_radius_and_transparent_glyph(qapp):
    previous_stylesheet = qapp.styleSheet()
    qapp.setStyleSheet(get_global_qss())
    badge = build_icon_badge(
        get_assets_path("icons/circle-info-filled.svg"),
        BrandColors.RED,
    )
    parent = QWidget()
    parent.setProperty("role", "splash_window")
    parent.resize(60, 60)
    badge.setParent(parent)
    badge.move(10, 10)
    try:
        parent.ensurePolished()
        rendered = QPixmap(parent.size())
        rendered.fill(Qt.GlobalColor.transparent)
        parent.render(rendered)

        rendered_image = rendered.toImage()
        assert rendered_image.pixelColor(10, 10) != QColor(BrandColors.RED)
        assert rendered_image.pixelColor(12, 30) == QColor(BrandColors.RED)
        glyph = badge.findChild(QLabel, "dialog_icon_badge_glyph")
        assert glyph is not None
        assert glyph.pixmap() is not None
        assert badge.mask().isEmpty()
    finally:
        parent.deleteLater()
        qapp.setStyleSheet(previous_stylesheet)
