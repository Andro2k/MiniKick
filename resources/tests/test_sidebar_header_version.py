# resources\tests\test_sidebar_header_version.py

import time

from frontend.navigation import Sidebar


class _I18n:
    _TEXTS = {"main.sidebar.version": "Versión {version}"}

    def get(self, key: str, default: str = "") -> str:
        return self._TEXTS.get(key, default or key)


def _wait_for_width(qapp, sidebar: Sidebar, width: int, timeout: float = 2.0) -> None:
    deadline = time.time() + timeout
    while sidebar.width() != width and time.time() < deadline:
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()


def _header_widgets(sidebar: Sidebar) -> list:
    layout = sidebar.header_layout
    return [layout.itemAt(index).widget() for index in range(layout.count())]


def test_version_badge_sits_right_after_the_app_name(qapp):
    sidebar = Sidebar(_I18n(), app_version="1.6.7")
    widgets = _header_widgets(sidebar)

    assert widgets.index(sidebar.lbl_version) == widgets.index(sidebar.title_label) + 1
    assert sidebar.lbl_version.text() == "v1.6.7"
    assert sidebar.lbl_version.toolTip() == "Versión 1.6.7"
    assert sidebar.lbl_version.property("role") == "badge_kick"


def test_version_prefix_is_not_duplicated():
    sidebar = Sidebar(_I18n(), app_version="v1.6.7")
    assert sidebar.lbl_version.text() == "v1.6.7"
    assert sidebar.lbl_version.toolTip() == "Versión 1.6.7"


def test_version_badge_is_hidden_without_a_version(qapp):
    sidebar = Sidebar(_I18n(), app_version="")
    sidebar.show()
    qapp.processEvents()
    assert not sidebar.lbl_version.isVisible()


def test_version_badge_follows_the_title_when_collapsing_and_expanding(qapp):
    sidebar = Sidebar(_I18n(), app_version="1.6.7")
    sidebar.show()
    qapp.processEvents()
    assert sidebar.lbl_version.isVisible()

    sidebar.toggle_sidebar()
    _wait_for_width(qapp, sidebar, sidebar.collapsed_width)
    assert not sidebar.title_label.isVisible()
    assert not sidebar.lbl_version.isVisible()

    sidebar.toggle_sidebar()
    _wait_for_width(qapp, sidebar, sidebar.expanded_width)
    assert sidebar.title_label.isVisible()
    assert sidebar.lbl_version.isVisible()
