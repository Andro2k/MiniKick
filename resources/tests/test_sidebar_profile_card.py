# resources\tests\test_sidebar_profile_card.py
"""Pruebas de la tarjeta de perfil de la barra lateral."""

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from frontend.common import Size
from frontend.navigation import Sidebar
from frontend.widgets import ClickableFrame, ModernButton


class _I18n:
    def get(self, key: str, default: str = "") -> str:
        return default or key


def _sidebar() -> Sidebar:
    sidebar = Sidebar(_I18n(), app_version="1.6.7")
    sidebar.add_tab("Dashboard", "home.svg", is_active=False)
    sidebar.add_tab("Chat", "message.svg", is_active=True)
    return sidebar


def _dashboard_button(sidebar: Sidebar):
    return next(btn for btn in sidebar.nav_buttons if btn.property("view_name") == "Dashboard")


def test_profile_card_is_a_plain_frame_that_does_not_navigate(qapp):
    sidebar = _sidebar()
    sidebar.show()
    qapp.processEvents()
    seen = []
    sidebar.view_selected.connect(seen.append)

    QTest.mouseClick(sidebar.profile_card, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))

    assert not isinstance(sidebar.profile_card, ClickableFrame)
    assert seen == []
    assert sidebar.button_group.checkedButton().property("view_name") == "Chat"


def test_settings_button_lives_in_the_profile_card_and_selects_settings(qapp):
    sidebar = _sidebar()
    sidebar.add_tab("Settings", "gear.svg", position="profile")
    gear = next(btn for btn in sidebar.nav_buttons if btn.property("view_name") == "Settings")
    sidebar.show()
    qapp.processEvents()
    seen = []
    sidebar.view_selected.connect(seen.append)

    QTest.mouseClick(gear, Qt.MouseButton.LeftButton)

    assert gear.parent() is sidebar.profile_card
    assert gear.text() == "" and gear.toolTip() == "main.sidebar.tabs.settings"
    assert seen == ["Settings"] and gear.isChecked()
    assert all(sidebar.section_layouts[name].indexOf(gear) == -1 for name in sidebar.section_layouts)


def test_tabs_are_grouped_by_section_and_headers_hide_when_collapsed(qapp):
    sidebar = _sidebar()
    sidebar.add_tab("Stats", "chart.svg", position="main")
    sidebar.add_tab("Music", "music.svg", position="tools")
    sidebar.add_tab("Developer", "file.svg", position="system")

    placed = {
        name: [layout.itemAt(i).widget().property("view_name") for i in range(layout.count())]
        for name, layout in sidebar.section_layouts.items()
    }
    assert placed == {"main": ["Dashboard", "Chat", "Stats"], "stream": [], "tools": ["Music"], "system": ["Developer"]}

    sidebar._update_texts_and_styles(show=False)
    assert not any(header.isVisible() or header.isVisibleTo(sidebar) for header in sidebar.section_headers.values())
    sidebar._update_texts_and_styles(show=True)
    assert all(header.isVisibleTo(sidebar) for header in sidebar.section_headers.values())


def test_settings_badge_shows_as_a_dot_on_the_profile_button(qapp):
    sidebar = _sidebar()
    sidebar.add_tab("Settings", "gear.svg", position="profile")
    sidebar.show()
    qapp.processEvents()

    sidebar.set_tab_badge("Settings", True)
    gear = next(btn for btn in sidebar.nav_buttons if btn.property("view_name") == "Settings")

    assert gear.badge_label.isVisible()
    assert gear.badge_label.property("state") == "collapsed"


def test_sidebar_sizes_come_from_the_theme(qapp):
    sidebar = _sidebar()
    assert sidebar.expanded_width == Size.SIDEBAR_EXPANDED == 230
    assert sidebar.collapsed_width == Size.SIDEBAR_COLLAPSED == 60
    assert sidebar.profile_avatar.width() == Size.AVATAR_SM
    assert all(btn.height() == Size.NAV_BUTTON_HEIGHT for btn in sidebar.nav_buttons)


def test_sidebar_and_icon_only_buttons_use_explicit_icon_sizes(qapp):
    sidebar = _sidebar()
    compact = ModernButton("", icon_name="gear-outline.svg")
    prominent = ModernButton("", icon_name="play-outline.svg", icon_size=Size.ICON_FEATURE)

    assert _dashboard_button(sidebar).iconSize().width() == Size.ICON_NAV
    assert compact.iconSize().width() == Size.ICON_ACTION
    assert prominent.iconSize().width() == Size.ICON_FEATURE


def test_sidebar_version_label_is_not_shown_as_a_top_level_window(qapp):
    class TopLevelLabelProbe(QObject):
        def __init__(self):
            super().__init__()
            self.shown_labels = []

        def eventFilter(self, watched, event):
            if (
                event.type() == QEvent.Type.Show
                and isinstance(watched, QLabel)
                and watched.isWindow()
            ):
                self.shown_labels.append(watched)
            return super().eventFilter(watched, event)

    probe = TopLevelLabelProbe()
    qapp.installEventFilter(probe)
    try:
        sidebar = _sidebar()
    finally:
        qapp.removeEventFilter(probe)

    assert probe.shown_labels == []
    assert sidebar.lbl_version.parentWidget() is sidebar.header_container
