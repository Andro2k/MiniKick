# frontend\views\schedule_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QBoxLayout, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from frontend.widgets import BaseView, ModernScrollArea
from frontend.components.schedule import (
    ScheduleQuickChangePanel,
    ScheduleFormPanel,
    ScheduleTablePanel
)

class ScheduleView(BaseView):
    refresh_info_requested = Signal()
    update_stream_requested = Signal(str, object, object, str, str)
    search_category_requested = Signal(str, str)
    save_schedule_requested = Signal(object)
    delete_schedule_requested = Signal(int)
    toggle_schedule_requested = Signal(int, bool)
    view_shown = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="stream_info.header.title", subtitle_key="stream_info.header.subtitle", parent=parent)
        self._last_direction = QBoxLayout.Direction.LeftToRight
        self._setup_ui()
        self._connect_internal_signals()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        direction = QBoxLayout.Direction.TopToBottom if width < 1080 else QBoxLayout.Direction.LeftToRight
        if direction != self._last_direction:
            self._last_direction = direction
            if hasattr(self, "columns_layout"):
                self.columns_layout.setDirection(direction)

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()

    def _setup_ui(self):
        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(16)

        self.columns_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)
        self.columns_layout.setSpacing(16)

        col1 = QWidget()
        self.col1_layout = QVBoxLayout(col1)
        self.col1_layout.setContentsMargins(0, 0, 0, 0)
        self.col1_layout.setSpacing(0)
        self.col1_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.quick_change_panel = ScheduleQuickChangePanel(self.i18n)
        self.schedule_form_panel = ScheduleFormPanel(self.i18n)

        self.tabs.addTab(ModernScrollArea(self.quick_change_panel), self.i18n.get("stream_info.tabs.quick_change"))
        self.tabs.addTab(ModernScrollArea(self.schedule_form_panel), self.i18n.get("stream_info.tabs.schedule_form"))

        self.col1_layout.addWidget(self.tabs)

        col2 = QWidget()
        self.col2_layout = QVBoxLayout(col2)
        self.col2_layout.setContentsMargins(0, 0, 0, 0)
        self.col2_layout.setSpacing(0)

        self.table_panel = ScheduleTablePanel(self.i18n)
        self.col2_layout.addWidget(self.table_panel)

        self.columns_layout.addWidget(col1, stretch=3)
        self.columns_layout.addWidget(col2, stretch=4)

        self.body_layout.addLayout(self.columns_layout)
        self.main_layout.addWidget(self.body_container)

    def _connect_internal_signals(self):
        self.quick_change_panel.refresh_info_requested.connect(self.refresh_info_requested.emit)
        self.quick_change_panel.update_stream_requested.connect(self.update_stream_requested.emit)
        self.quick_change_panel.search_category_requested.connect(self.search_category_requested.emit)
        self.schedule_form_panel.search_category_requested.connect(self.search_category_requested.emit)
        self.schedule_form_panel.schedule_saved.connect(self._on_schedule_form_saved)

        self.table_panel.new_schedule_clicked.connect(self._on_new_schedule_clicked)
        self.table_panel.edit_schedule_clicked.connect(self._on_edit_schedule_clicked)
        self.table_panel.delete_schedule_requested.connect(self.delete_schedule_requested.emit)
        self.table_panel.toggle_schedule_requested.connect(self.toggle_schedule_requested.emit)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index: int):
        if hasattr(self.quick_change_panel, "popup_suggestions"):
            self.quick_change_panel.popup_suggestions.hide()
        if hasattr(self.schedule_form_panel, "popup_kick"):
            self.schedule_form_panel.popup_kick.hide()
        if hasattr(self.schedule_form_panel, "popup_twitch"):
            self.schedule_form_panel.popup_twitch.hide()

    def _on_new_schedule_clicked(self):
        self.schedule_form_panel.clear_form()
        self.tabs.setCurrentIndex(1)

    def _on_edit_schedule_clicked(self, sched_data: dict):
        self.schedule_form_panel.load_schedule(sched_data)
        self.tabs.setCurrentIndex(1)

    def _on_schedule_form_saved(self, data: dict):
        self.save_schedule_requested.emit(data)
        self.tabs.setCurrentIndex(0)

    def set_current_stream_info(self, info: dict):
        self.quick_change_panel.set_current_stream_info(info)

    def set_category_search_results(self, platform: str, results: list[dict]):
        self.quick_change_panel.set_category_search_results(platform, results)
        self.schedule_form_panel.set_category_search_results(platform, results)

    def set_loading(self, is_loading: bool):
        self.quick_change_panel.set_loading(is_loading)

    def on_update_completed(self, results: dict):
        self.quick_change_panel.set_loading(False)

    def set_schedules(self, schedules: list[dict]):
        self.table_panel.set_schedules(schedules)

    def set_connected_platforms(self, connected_platforms: dict[str, bool]):
        if hasattr(self, "quick_change_panel"):
            self.quick_change_panel.set_connected_platforms(connected_platforms)
        if hasattr(self, "schedule_form_panel"):
            self.schedule_form_panel.set_connected_platforms(connected_platforms)
