# resources\tests\test_sidebar_auto_collapse.py
"""Pruebas del colapso automático del sidebar según el ancho de la ventana."""

from unittest.mock import MagicMock

from PySide6.QtWidgets import QMainWindow

from frontend.common import Size
from frontend.navigation import Sidebar
from frontend.window.main_window_core import MainWindowCore


class _I18n:
    def get(self, key, default="", **_kwargs):
        return default or key


def _sidebar(qapp):
    return Sidebar(_I18n(), app_version="1.6.8")


def test_narrow_window_collapses_and_wide_window_restores(qapp):
    sidebar = _sidebar(qapp)

    sidebar.fit_to_window(1000)
    assert sidebar.is_expanded is False
    assert sidebar.width() == Size.SIDEBAR_COLLAPSED

    sidebar.fit_to_window(1200)
    assert sidebar.is_expanded is True


def test_manual_collapse_survives_a_narrow_and_wide_cycle(qapp):
    sidebar = _sidebar(qapp)
    sidebar.toggle_sidebar()
    assert sidebar.is_expanded is False

    sidebar.fit_to_window(1000)
    sidebar.fit_to_window(1400)

    assert sidebar.is_expanded is False


def test_manual_expand_in_a_narrow_window_is_kept_until_the_next_crossing(qapp):
    sidebar = _sidebar(qapp)
    sidebar.fit_to_window(1000)

    sidebar.toggle_sidebar()
    sidebar.fit_to_window(950)
    assert sidebar.is_expanded is True

    sidebar.fit_to_window(1300)
    sidebar.fit_to_window(1000)
    assert sidebar.is_expanded is False


def test_window_resize_event_drives_the_sidebar(qapp):
    class _Window(MainWindowCore):
        def __init__(self):
            QMainWindow.__init__(self)
            self.sidebar = _sidebar(qapp)
            self.window_state = MagicMock()

    window = _Window()
    window.resize(1000, 700)
    window.show()
    qapp.processEvents()
    assert window.sidebar.is_expanded is False

    window.resize(1300, 700)
    qapp.processEvents()
    assert window.sidebar.is_expanded is True
    window.hide()
