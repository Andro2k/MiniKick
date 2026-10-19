# resources\tests\test_dashboard_chatters.py

import pytest
import datetime
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from backend.services.system.translation_service import TranslationService
from frontend.components.dashboard.chatters_table import DashboardChattersTable
from backend.controllers.dashboard_controller import DashboardController

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def i18n():
    return TranslationService()

def test_chatters_table_empty_state_and_render(qapp, i18n):
    table_comp = DashboardChattersTable(i18n)

    table_comp.set_chatters([])
    assert table_comp.stack.currentIndex() == 1
    assert table_comp.table.rowCount() == 0

    sample_data = [
        {"user": "Alice", "count": 100, "color": "#2ecd70", "platform": "kick"},
        {"user": "Bob", "count": 50, "color": "#9146ff", "platform": "twitch"},
        {"user": "Charlie", "count": 25, "color": "#ff0000", "platform": "youtube"},
    ]
    table_comp.set_chatters(sample_data, total_messages=175)

    assert table_comp.stack.currentIndex() == 0
    assert table_comp.table.rowCount() == 3

    rank1_widget = table_comp.table.cellWidget(0, 0)
    assert rank1_widget is not None
    assert rank1_widget.text() == "#1"

    user1_widget = table_comp.table.cellWidget(0, 1)
    assert user1_widget is not None
    assert "Alice" in user1_widget.text()

    plat1_widget = table_comp.table.cellWidget(0, 2)
    assert plat1_widget is not None
    assert plat1_widget.text() == "Kick"

def test_chatters_table_date_signals(qapp, i18n):
    table_comp = DashboardChattersTable(i18n)
    emitted_dates = []
    table_comp.date_selected.connect(emitted_dates.append)

    table_comp.btn_today.click()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    assert emitted_dates[-1] == today_str

    table_comp.btn_yesterday.click()
    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    assert emitted_dates[-1] == yesterday_str

    table_comp.populate_available_dates(["2026-09-20", "2026-09-19"])
    assert table_comp.combo_dates.count() == 3

    table_comp.combo_dates.setCurrentIndex(1)
    assert emitted_dates[-1] == "2026-09-20"

def test_dashboard_controller_top_chatters_loading(qapp):
    mock_view = MagicMock()
    mock_avatar = MagicMock()
    mock_widget_service = MagicMock()

    mock_widget_service.get_available_chatter_dates.return_value = ["2026-09-27", "2026-09-26"]
    mock_widget_service.load_daily_chatters.return_value = {
        "alice": {"user": "Alice", "count": 120, "color": "#2ecd70", "platform": "kick"},
        "bob": {"user": "Bob", "count": 80, "color": "#9146ff", "platform": "twitch"}
    }

    controller = DashboardController(
        view=mock_view,
        avatar_service=mock_avatar,
        widget_service=mock_widget_service
    )

    mock_view.populate_chatter_dates.assert_called_with(["2026-09-27", "2026-09-26"])

    assert mock_view.render_top_chatters.called
    args = mock_view.render_top_chatters.call_args[0]
    chatters_arg = args[0]
    assert len(chatters_arg) == 2
    kwargs = mock_view.render_top_chatters.call_args[1]
    assert kwargs.get("total_messages") == 200

def test_chatters_table_banner_inactive_and_activation_signal(qapp, i18n):
    table_comp = DashboardChattersTable(i18n)
    
    table_comp.set_widget_active(True)
    assert table_comp.banner_inactive.isHidden()

    table_comp.set_widget_active(False)
    assert not table_comp.banner_inactive.isHidden()
    assert table_comp.lbl_empty_desc.text() == i18n.get("dashboard.chatters.empty_inactive_desc")

    activated_emitted = []
    table_comp.activate_widget_requested.connect(lambda: activated_emitted.append(True))
    table_comp.btn_activate_banner.click()
    assert len(activated_emitted) == 1

def test_dashboard_controller_live_auto_refresh_and_activation(qapp):
    mock_view = MagicMock()
    mock_avatar = MagicMock()
    mock_widget_service = MagicMock()
    mock_widgets_controller = MagicMock()
    mock_toast = MagicMock()

    mock_widget_service.get_available_chatter_dates.return_value = ["2026-09-27"]
    mock_widget_service.get_widget.return_value = {"is_active": False}
    mock_widgets_controller._chatters_counts = {
        "david": {"user": "David", "count": 15, "color": "#2ecd70", "platform": "kick"}
    }

    controller = DashboardController(
        view=mock_view,
        avatar_service=mock_avatar,
        widget_service=mock_widget_service,
        widgets_controller=mock_widgets_controller,
        toast_manager=mock_toast
    )

    mock_view.set_chatters_widget_active.assert_called_with(False)

    mock_view.render_top_chatters.reset_mock()
    controller._on_chatters_updated()
    assert mock_view.render_top_chatters.called
    render_args = mock_view.render_top_chatters.call_args[0][0]
    assert len(render_args) == 1
    assert render_args[0]["user"] == "David"

    mock_widgets_controller.set_widget_active.return_value = True
    controller._on_activate_chatters_requested()
    mock_widgets_controller.set_widget_active.assert_called_with("chatters", True)
    assert mock_toast.show_toast.called
