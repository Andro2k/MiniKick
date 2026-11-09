# resources\tests\test_sidebar_profile_card.py

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from frontend.common import Size
from frontend.navigation import Sidebar
from frontend.widgets import ClickableFrame


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


def test_profile_card_is_a_clickable_frame_without_instance_overrides(qapp):
    sidebar = _sidebar()
    assert isinstance(sidebar.profile_card, ClickableFrame)
    assert "mousePressEvent" not in vars(sidebar.profile_card)


def test_clicking_the_profile_card_checks_dashboard_before_emitting(qapp):
    sidebar = _sidebar()
    sidebar.show()
    qapp.processEvents()
    dashboard = _dashboard_button(sidebar)
    seen = []
    sidebar.view_selected.connect(lambda name: seen.append((name, dashboard.isChecked())))

    QTest.mouseClick(sidebar.profile_card, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))

    assert seen == [("Dashboard", True)]


def test_other_mouse_buttons_do_not_open_the_dashboard(qapp):
    sidebar = _sidebar()
    sidebar.show()
    qapp.processEvents()
    seen = []
    sidebar.view_selected.connect(seen.append)

    QTest.mouseClick(sidebar.profile_card, Qt.MouseButton.RightButton, pos=QPoint(5, 5))

    assert seen == []


def test_sidebar_sizes_come_from_the_theme(qapp):
    sidebar = _sidebar()
    assert sidebar.expanded_width == Size.SIDEBAR_EXPANDED == 230
    assert sidebar.collapsed_width == Size.SIDEBAR_COLLAPSED == 60
    assert sidebar.profile_avatar.width() == Size.AVATAR_SM
    assert all(btn.height() == Size.NAV_BUTTON_HEIGHT for btn in sidebar.nav_buttons)
