# frontend\components\schedule\quick_change_panel.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                               QLineEdit, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal
from frontend.widgets import ModernCard, ModernButton, ModernSwitch, CategorySearchComboBox
from frontend.common.theme import COLOR_NEUTRAL_400, COLOR_GREEN, COLOR_PURPLE
from frontend.common import get_icon_colored, get_pixmap_colored

class ScheduleQuickChangePanel(QWidget):
    refresh_info_requested = Signal()
    update_stream_requested = Signal(str, object, object, str, str)
    search_category_requested = Signal(str, str)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.kick_selected_category = None
        self.twitch_selected_category = None
        self._current_cols = -1

        self._icon_refresh = get_icon_colored("refresh.svg", COLOR_NEUTRAL_400, 16)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._setup_status_section(layout)
        self._setup_quick_change_card(layout)

    def _setup_status_section(self, parent_layout: QVBoxLayout):
        status_header = QHBoxLayout()
        status_header.setContentsMargins(10, 2, 10, 2)
        status_header.setSpacing(8)
        status_header.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_status_title = QLabel(self.i18n.get("stream_info.status.title"))
        lbl_status_title.setProperty("role", "h2")
        status_header.addWidget(lbl_status_title, alignment=Qt.AlignmentFlag.AlignVCenter)
        status_header.addStretch()

        self.btn_refresh = QPushButton()
        self.btn_refresh.setProperty("role", "action_outlined")
        self.btn_refresh.setIcon(self._icon_refresh)
        self.btn_refresh.setFixedSize(32, 32)
        self.btn_refresh.setToolTip(self.i18n.get("stream_info.status.refresh_tooltip"))
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_info_requested.emit)
        status_header.addWidget(self.btn_refresh, alignment=Qt.AlignmentFlag.AlignVCenter)

        parent_layout.addLayout(status_header)

        self.cards_grid = QGridLayout()
        self.cards_grid.setContentsMargins(0, 0, 0, 0)
        self.cards_grid.setSpacing(12)

        self.kick_card = ModernCard(parent=self, margin=12, spacing=10)
        kick_header = QHBoxLayout()
        kick_header.setSpacing(8)

        icon_kick = QLabel()
        icon_kick.setPixmap(get_pixmap_colored("brand-kick.svg", COLOR_GREEN, size=18))
        lbl_kick_badge = QLabel("KICK")
        lbl_kick_badge.setProperty("role", "badge_kick")
        self.lbl_kick_status = QLabel(self.i18n.get("stream_info.status.loading"))
        self.lbl_kick_status.setProperty("role", "caption")

        kick_header.addWidget(icon_kick)
        kick_header.addWidget(lbl_kick_badge)
        kick_header.addStretch()
        kick_header.addWidget(self.lbl_kick_status)
        self.kick_card.addLayout(kick_header)

        self.kick_title_box = QFrame()
        self.kick_title_box.setProperty("role", "card")
        kick_title_layout = QVBoxLayout(self.kick_title_box)
        kick_title_layout.setContentsMargins(10, 8, 10, 8)
        kick_title_layout.setSpacing(3)
        lbl_kick_t_header = QLabel(self.i18n.get("stream_info.quick_change.stream_title"))
        lbl_kick_t_header.setProperty("role", "caption")
        self.lbl_kick_title = QLabel("-")
        self.lbl_kick_title.setProperty("role", "h3")
        self.lbl_kick_title.setWordWrap(True)
        kick_title_layout.addWidget(lbl_kick_t_header)
        kick_title_layout.addWidget(self.lbl_kick_title)
        self.kick_card.addWidget(self.kick_title_box)

        self.kick_cat_box = QFrame()
        self.kick_cat_box.setProperty("role", "card")
        kick_cat_layout = QVBoxLayout(self.kick_cat_box)
        kick_cat_layout.setContentsMargins(10, 8, 10, 8)
        kick_cat_layout.setSpacing(3)
        lbl_kick_c_header = QLabel(self.i18n.get("stream_info.quick_change.category"))
        lbl_kick_c_header.setProperty("role", "caption")
        self.lbl_kick_cat = QLabel(self.i18n.get("stream_info.status.no_category"))
        self.lbl_kick_cat.setProperty("role", "body")
        self.lbl_kick_cat.setWordWrap(True)
        kick_cat_layout.addWidget(lbl_kick_c_header)
        kick_cat_layout.addWidget(self.lbl_kick_cat)
        self.kick_card.addWidget(self.kick_cat_box)

        self.twitch_card = ModernCard(parent=self, margin=12, spacing=10)
        twitch_header = QHBoxLayout()
        twitch_header.setSpacing(8)

        icon_twitch = QLabel()
        icon_twitch.setPixmap(get_pixmap_colored("brand-twitch.svg", COLOR_PURPLE, size=18))
        lbl_twitch_badge = QLabel("TWITCH")
        lbl_twitch_badge.setProperty("role", "badge_twitch")
        self.lbl_twitch_status = QLabel(self.i18n.get("stream_info.status.loading"))
        self.lbl_twitch_status.setProperty("role", "caption")

        twitch_header.addWidget(icon_twitch)
        twitch_header.addWidget(lbl_twitch_badge)
        twitch_header.addStretch()
        twitch_header.addWidget(self.lbl_twitch_status)
        self.twitch_card.addLayout(twitch_header)

        self.twitch_title_box = QFrame()
        self.twitch_title_box.setProperty("role", "card")
        twitch_title_layout = QVBoxLayout(self.twitch_title_box)
        twitch_title_layout.setContentsMargins(10, 8, 10, 8)
        twitch_title_layout.setSpacing(3)
        lbl_twitch_t_header = QLabel(self.i18n.get("stream_info.quick_change.stream_title"))
        lbl_twitch_t_header.setProperty("role", "caption")
        self.lbl_twitch_title = QLabel("-")
        self.lbl_twitch_title.setProperty("role", "h3")
        self.lbl_twitch_title.setWordWrap(True)
        twitch_title_layout.addWidget(lbl_twitch_t_header)
        twitch_title_layout.addWidget(self.lbl_twitch_title)
        self.twitch_card.addWidget(self.twitch_title_box)

        self.twitch_cat_box = QFrame()
        self.twitch_cat_box.setProperty("role", "card")
        twitch_cat_layout = QVBoxLayout(self.twitch_cat_box)
        twitch_cat_layout.setContentsMargins(10, 8, 10, 8)
        twitch_cat_layout.setSpacing(3)
        lbl_twitch_c_header = QLabel(self.i18n.get("stream_info.quick_change.category"))
        lbl_twitch_c_header.setProperty("role", "caption")
        self.lbl_twitch_cat = QLabel(self.i18n.get("stream_info.status.no_category"))
        self.lbl_twitch_cat.setProperty("role", "body")
        self.lbl_twitch_cat.setWordWrap(True)
        twitch_cat_layout.addWidget(lbl_twitch_c_header)
        twitch_cat_layout.addWidget(self.lbl_twitch_cat)
        self.twitch_card.addWidget(self.twitch_cat_box)

        self.cards_grid.addWidget(self.kick_card, 0, 0)
        self.cards_grid.addWidget(self.twitch_card, 0, 1)
        parent_layout.addLayout(self.cards_grid)

    def relayout(self, width: int = None):
        self._update_grid_layout(width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_grid_layout()

    def _update_grid_layout(self, width: int = None):
        w = width if width is not None else self.width()
        cols = 1 if w < 680 else 2

        if cols == self._current_cols:
            return

        self._current_cols = cols

        self.cards_grid.removeWidget(self.kick_card)
        self.cards_grid.removeWidget(self.twitch_card)

        if cols == 1:
            self.cards_grid.addWidget(self.kick_card, 0, 0)
            self.cards_grid.addWidget(self.twitch_card, 1, 0)
        else:
            self.cards_grid.addWidget(self.kick_card, 0, 0)
            self.cards_grid.addWidget(self.twitch_card, 0, 1)

    def _setup_quick_change_card(self, parent_layout: QVBoxLayout):
        change_card = ModernCard(parent=self, margin=16, spacing=14)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        lbl_title = QLabel(self.i18n.get("stream_info.quick_change.title"))
        lbl_title.setProperty("role", "h2")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        change_card.addLayout(header_layout)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        lbl_target = QLabel(self.i18n.get("stream_info.quick_change.target_platform"))
        lbl_target.setProperty("role", "h3")
        form_layout.addWidget(lbl_target)

        switches_row = QHBoxLayout()
        switches_row.setSpacing(24)

        kick_switch_box = QHBoxLayout()
        kick_switch_box.setSpacing(8)
        self.switch_kick = ModernSwitch()
        self.switch_kick.setChecked(True)
        lbl_kick = QLabel("Kick")
        lbl_kick.setProperty("role", "body")
        kick_switch_box.addWidget(self.switch_kick)
        kick_switch_box.addWidget(lbl_kick)
        switches_row.addLayout(kick_switch_box)

        twitch_switch_box = QHBoxLayout()
        twitch_switch_box.setSpacing(8)
        self.switch_twitch = ModernSwitch()
        self.switch_twitch.setChecked(True)
        lbl_twitch = QLabel("Twitch")
        lbl_twitch.setProperty("role", "body")
        twitch_switch_box.addWidget(self.switch_twitch)
        twitch_switch_box.addWidget(lbl_twitch)
        switches_row.addLayout(twitch_switch_box)
        switches_row.addStretch()

        form_layout.addLayout(switches_row)

        lbl_title_field = QLabel(self.i18n.get("stream_info.quick_change.stream_title"))
        lbl_title_field.setProperty("role", "h3")
        form_layout.addWidget(lbl_title_field)

        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText(self.i18n.get("stream_info.quick_change.title_placeholder"))
        form_layout.addWidget(self.txt_title)

        lbl_category = QLabel(self.i18n.get("stream_info.quick_change.category"))
        lbl_category.setProperty("role", "h3")
        form_layout.addWidget(lbl_category)

        self.search_category = CategorySearchComboBox(
            placeholder=self.i18n.get("stream_info.quick_change.category_placeholder"),
            default_platform="both",
            parent=self
        )
        self.search_category.category_selected.connect(self._on_category_selected)
        self.search_category.search_requested.connect(self._on_search_requested)
        form_layout.addWidget(self.search_category)

        form_layout.addSpacing(6)
        action_row = QHBoxLayout()
        action_row.addStretch()

        self.btn_apply = ModernButton(self.i18n.get("stream_info.quick_change.btn_update"), role="action_accent")
        self.btn_apply.setFixedWidth(200)
        self.btn_apply.clicked.connect(self._on_update_clicked)
        action_row.addWidget(self.btn_apply)
        form_layout.addLayout(action_row)

        change_card.addLayout(form_layout)
        parent_layout.addWidget(change_card)

    def get_selected_platform(self) -> str:
        kick_on = self.switch_kick.isChecked()
        twitch_on = self.switch_twitch.isChecked()
        if kick_on and twitch_on:
            return "all"
        elif kick_on:
            return "kick"
        elif twitch_on:
            return "twitch"
        return "all"

    def set_target_platform(self, platform_str: str):
        if platform_str == "kick":
            self.switch_kick.setChecked(True)
            self.switch_twitch.setChecked(False)
        elif platform_str == "twitch":
            self.switch_kick.setChecked(False)
            self.switch_twitch.setChecked(True)
        else:
            self.switch_kick.setChecked(True)
            self.switch_twitch.setChecked(True)

    def _on_search_requested(self, query: str, _platform: str):
        target_platform = self.get_selected_platform()
        self.search_category_requested.emit(query, target_platform)

    def set_category_search_results(self, platform: str, results: list[dict]):
        self.search_category.set_results(platform, results)

    def _on_category_selected(self, data: dict):
        platform = data.get("platform")
        name = data.get("name", "")
        cat_id = data.get("id")

        if platform == "kick":
            self.kick_selected_category = {"id": cat_id, "name": name}
        elif platform == "twitch":
            self.twitch_selected_category = {"id": cat_id, "name": name}
        else:
            self.kick_selected_category = {"id": cat_id, "name": name}
            self.twitch_selected_category = {"id": cat_id, "name": name}

    def _on_update_clicked(self):
        title = self.txt_title.text().strip()
        cat_query = self.search_category.text().strip()
        kick_id = self.kick_selected_category.get("id") if self.kick_selected_category else None
        twitch_id = self.twitch_selected_category.get("id") if self.twitch_selected_category else None
        
        self.update_stream_requested.emit(title, kick_id, twitch_id, self.get_selected_platform(), cat_query)

    def set_current_stream_info(self, info: dict):
        kick_info = info.get("kick", {}) or {}
        twitch_info = info.get("twitch", {}) or {}

        if "error" in kick_info or not kick_info:
            self.lbl_kick_status.setText(self.i18n.get("stream_info.status.disconnected"))
            self.lbl_kick_title.setText("-")
            self.lbl_kick_cat.setText("-")
        else:
            self.lbl_kick_status.setText(self.i18n.get("stream_info.status.connected"))
            self.lbl_kick_title.setText(kick_info.get("stream_title") or "-")
            self.lbl_kick_cat.setText(kick_info.get("category_name") or self.i18n.get("stream_info.status.no_category"))

        if "error" in twitch_info or not twitch_info:
            self.lbl_twitch_status.setText(self.i18n.get("stream_info.status.disconnected"))
            self.lbl_twitch_title.setText("-")
            self.lbl_twitch_cat.setText("-")
        else:
            self.lbl_twitch_status.setText(self.i18n.get("stream_info.status.connected"))
            self.lbl_twitch_title.setText(twitch_info.get("title") or "-")
            self.lbl_twitch_cat.setText(twitch_info.get("game_name") or self.i18n.get("stream_info.status.no_category"))

    def set_loading(self, is_loading: bool):
        self.btn_apply.setEnabled(not is_loading)
        self.btn_refresh.setEnabled(not is_loading)
