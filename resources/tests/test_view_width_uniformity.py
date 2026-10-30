# resources\tests\test_view_width_uniformity.py

import importlib
import pkgutil

import pytest
from PySide6.QtCore import QObject, Signal

import frontend.views
from backend.services.system import TranslationService
from frontend.common import Size
from frontend.views.base_view import BaseView

_VIEWS = {
    "alerts_view": "AlertsView",
    "chat_view": "ChatView",
    "commands_view": "CommandView",
    "dashboard_view": "DashboardView",
    "logs_view": "LogView",
    "music_view": "MusicView",
    "rewards_view": "RewardsView",
    "schedule_view": "ScheduleView",
    "settings_view": "SettingsView",
    "timers_view": "TimersView",
    "widgets_view": "WidgetsView",
}
_FORM_VIEWS = {"SettingsView"}
_SCREEN_WIDTH = 2000


class _NoAudioDevices(QObject):
    audioOutputsChanged = Signal()

    @staticmethod
    def audioOutputs():
        return []


def _view_class(module_name: str, class_name: str) -> type[BaseView]:
    return getattr(importlib.import_module(f"frontend.views.{module_name}"), class_name)


def test_every_view_is_covered_by_the_uniformity_check():
    for module in pkgutil.iter_modules(frontend.views.__path__):
        importlib.import_module(f"frontend.views.{module.name}")
    declared = {cls.__name__ for cls in BaseView.__subclasses__() if cls.__module__.startswith("frontend.views")}
    assert declared == set(_VIEWS.values())


@pytest.mark.parametrize("module_name,class_name", list(_VIEWS.items()))
def test_view_content_is_capped_and_centered(qapp, monkeypatch, module_name, class_name):
    monkeypatch.setattr("frontend.views.settings_view.QMediaDevices", _NoAudioDevices)
    view = _view_class(module_name, class_name)(TranslationService(default_lang="es"))
    view.resize(_SCREEN_WIDTH, 1000)
    view.show()
    qapp.processEvents()
    qapp.processEvents()

    column = view.content_column.geometry()
    assert column.width() in (Size.CONTENT_MAX_WIDTH, Size.CONTENT_WIDE_MAX_WIDTH)
    assert abs(column.left() - (view.scroll_content.width() - column.right() - 1)) <= 1
    if class_name in _FORM_VIEWS:
        assert column.width() == Size.CONTENT_MAX_WIDTH
    view.close()


def test_alerts_editor_keeps_its_three_columns_inside_the_wide_column(qapp):
    from PySide6.QtWidgets import QBoxLayout
    from frontend.components.alerts.event_card import AlertEventCard

    view = _view_class("alerts_view", "AlertsView")(TranslationService(default_lang="es"))
    view.resize(_SCREEN_WIDTH, 1000)
    view.show()
    qapp.processEvents()
    qapp.processEvents()

    cards = view.findChildren(AlertEventCard)
    assert cards
    assert all(card.body_box.direction() == QBoxLayout.Direction.LeftToRight for card in cards if card.isVisible())
    view.close()
