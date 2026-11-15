# resources\tests\test_dashboard_quick_access.py
"""Pruebas de los accesos rápidos del dashboard y de la navegación desde ellos."""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from frontend.navigation import Sidebar
from frontend.views.dashboard_view import DashboardView


class KeyTranslations:
    @staticmethod
    def get(key, default=""):
        return default or key


def test_quick_access_cards_emit_the_target_view_name(qapp):
    view = DashboardView(KeyTranslations())
    seen = []
    view.quick_access_requested.connect(seen.append)
    cards = {card.view_name: card for card in view.quick_access_cards}

    assert set(cards) == {"Stats", "Alerts", "Webhooks", "Music"}
    QTest.mouseClick(cards["Stats"], Qt.MouseButton.LeftButton, pos=QPoint(5, 5))
    QTest.mouseClick(cards["Webhooks"], Qt.MouseButton.LeftButton, pos=QPoint(5, 5))

    assert seen == ["Stats", "Webhooks"]


def test_quick_access_grid_is_responsive(qapp):
    view = DashboardView(KeyTranslations())
    view.resize(1200, 800)
    view.show()
    qapp.processEvents()
    wide_columns = {view.quick_access_grid.getItemPosition(i)[1] for i in range(4)}
    view.resize(600, 800)
    qapp.processEvents()
    narrow_columns = {view.quick_access_grid.getItemPosition(i)[1] for i in range(4)}

    assert wide_columns == {0, 1, 2, 3}
    assert narrow_columns == {0}


def test_sidebar_select_tab_checks_the_button_and_navigates(qapp):
    sidebar = Sidebar(KeyTranslations(), app_version="1.6.8")
    sidebar.add_tab("Dashboard", "home.svg", is_active=True)
    sidebar.add_tab("Stats", "chart.svg", position="main")
    seen = []
    sidebar.view_selected.connect(lambda name: seen.append((name, sidebar.button_group.checkedButton().property("view_name"))))

    sidebar.select_tab("Stats")
    sidebar.select_tab("Unknown")

    assert seen == [("Stats", "Stats")]


def test_dashboard_platform_cards_keep_a_compact_status_pill(qapp):
    from PySide6.QtWidgets import QSizePolicy

    view = DashboardView(KeyTranslations())
    pill_policy = view.card_kick.lbl_status_pill.sizePolicy()

    assert pill_policy.verticalPolicy() == QSizePolicy.Policy.Fixed
    assert pill_policy.horizontalPolicy() == QSizePolicy.Policy.Fixed
