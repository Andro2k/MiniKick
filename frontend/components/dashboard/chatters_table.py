# frontend\components\dashboard\chatters_table.py

import datetime
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
    QTableWidget, QHeaderView, QProgressBar, QSizePolicy,
    QBoxLayout
)
from PySide6.QtCore import Qt, Signal, QSize
from frontend.common import (
    COLOR_GREEN, COLOR_AMBER, COLOR_NEUTRAL_500,
    get_pixmap_colored, MARGIN_NONE, MARGIN_MD, MARGIN_LG,
    SPACING_XS, SPACING_SM, SPACING_MD
)
from frontend.widgets import ModernCard, ModernButton, NoWheelComboBox, create_col_layout

class DashboardChattersTable(ModernCard):
    date_selected = Signal(str)
    activate_widget_requested = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent=parent, margin=MARGIN_MD, spacing=SPACING_SM)
        self.i18n = i18n
        self._current_date = datetime.date.today().strftime("%Y-%m-%d")
        self._available_dates: list[str] = []
        self._is_populating_dates = False
        self._is_widget_active = True
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Preferred)
        self._setup_ui()

    def minimumSizeHint(self):
        return QSize(280, 200)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        direction = QBoxLayout.Direction.TopToBottom if width < 480 else QBoxLayout.Direction.LeftToRight
        if hasattr(self, "header_layout") and self.header_layout.direction() != direction:
            self.header_layout.setDirection(direction)

    def _setup_ui(self):
        self.header_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.header_layout.setContentsMargins(*MARGIN_NONE)
        self.header_layout.setSpacing(SPACING_MD)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(*MARGIN_NONE)
        title_col.setSpacing(SPACING_XS)

        self.lbl_title = QLabel(self.i18n.get("dashboard.chatters.title"), self)
        self.lbl_title.setProperty("role", "h3")

        self.lbl_subtitle = QLabel(self.i18n.get("dashboard.chatters.subtitle"), self)
        self.lbl_subtitle.setProperty("role", "caption")

        title_col.addWidget(self.lbl_title)
        title_col.addWidget(self.lbl_subtitle)
        self.header_layout.addLayout(title_col, stretch=1)

        filters_row = QHBoxLayout()
        filters_row.setContentsMargins(*MARGIN_NONE)
        filters_row.setSpacing(SPACING_XS)

        self.btn_today = ModernButton(
            self.i18n.get("dashboard.chatters.filter_today"),
            role="action_kick",
            parent=self
        )
        self.btn_today.setFixedHeight(28)
        self.btn_today.clicked.connect(self._on_today_clicked)

        self.btn_yesterday = ModernButton(
            self.i18n.get("dashboard.chatters.filter_yesterday"),
            role="action_outlined",
            parent=self
        )
        self.btn_yesterday.setFixedHeight(28)
        self.btn_yesterday.clicked.connect(self._on_yesterday_clicked)

        self.combo_dates = NoWheelComboBox(self)
        self.combo_dates.setFixedHeight(28)
        self.combo_dates.setMinimumWidth(140)
        self.combo_dates.addItem(self.i18n.get("dashboard.chatters.filter_date_placeholder"), "")
        self.combo_dates.currentIndexChanged.connect(self._on_combo_date_changed)

        filters_row.addWidget(self.btn_today)
        filters_row.addWidget(self.btn_yesterday)
        filters_row.addWidget(self.combo_dates)
        self.header_layout.addLayout(filters_row)

        self.addLayout(self.header_layout)

        self.banner_inactive = QFrame(self)
        self.banner_inactive.setProperty("role", "banner_warning")
        self.banner_inactive.setVisible(False)
        banner_layout = QHBoxLayout(self.banner_inactive)
        banner_layout.setContentsMargins(12, 8, 12, 8)
        banner_layout.setSpacing(SPACING_SM)

        lbl_banner_icon = QLabel(self.banner_inactive)
        lbl_banner_icon.setPixmap(get_pixmap_colored("alert-triangle-filled.svg", COLOR_AMBER, 18))
        lbl_banner_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_banner_msg = QLabel(self.i18n.get("dashboard.chatters.inactive_suggestion"), self.banner_inactive)
        self.lbl_banner_msg.setProperty("role", "body")
        self.lbl_banner_msg.setProperty("state", "warning")
        self.lbl_banner_msg.setWordWrap(True)

        self.btn_activate_banner = ModernButton(
            self.i18n.get("dashboard.chatters.btn_activate"),
            role="action_kick",
            parent=self.banner_inactive
        )
        self.btn_activate_banner.setFixedHeight(28)
        self.btn_activate_banner.clicked.connect(self.activate_widget_requested.emit)

        banner_layout.addWidget(lbl_banner_icon)
        banner_layout.addWidget(self.lbl_banner_msg, stretch=1)
        banner_layout.addWidget(self.btn_activate_banner)

        self.addWidget(self.banner_inactive)

        self.stack = QStackedWidget(self)
        self.stack.setContentsMargins(*MARGIN_NONE)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        headers = [
            self.i18n.get("dashboard.chatters.col_rank"),
            self.i18n.get("dashboard.chatters.col_user"),
            self.i18n.get("dashboard.chatters.col_platform"),
            self.i18n.get("dashboard.chatters.col_messages"),
            self.i18n.get("dashboard.chatters.col_share"),
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(240)

        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(25)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 48)
        self.table.setColumnWidth(2, 95)
        self.table.setColumnWidth(3, 85)
        self.table.setColumnWidth(4, 185)

        self.stack.addWidget(self.table)

        self.empty_widget = QWidget(self)
        empty_layout = create_col_layout(spacing=SPACING_SM, margins=MARGIN_LG, parent=self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_empty_icon = QLabel(self.empty_widget)
        lbl_empty_icon.setPixmap(get_pixmap_colored("users-filled.svg", COLOR_NEUTRAL_500, 36))
        lbl_empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_empty_title = QLabel(self.i18n.get("dashboard.chatters.empty_title"), self.empty_widget)
        self.lbl_empty_title.setProperty("role", "h3")
        self.lbl_empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_empty_desc = QLabel(self.i18n.get("dashboard.chatters.empty_desc"), self.empty_widget)
        self.lbl_empty_desc.setProperty("role", "body")
        self.lbl_empty_desc.setProperty("state", "normal")
        self.lbl_empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty_desc.setWordWrap(True)

        empty_layout.addWidget(lbl_empty_icon)
        empty_layout.addWidget(self.lbl_empty_title)
        empty_layout.addWidget(self.lbl_empty_desc)

        self.stack.addWidget(self.empty_widget)
        self.addWidget(self.stack)

        self.stack.setCurrentIndex(1)

    def _update_button_states(self, selected_date: str):
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        is_today = (selected_date == today_str)
        is_yesterday = (selected_date == yesterday_str)

        self.btn_today.setProperty("role", "action_kick" if is_today else "action_outlined")
        self.btn_today.style().unpolish(self.btn_today)
        self.btn_today.style().polish(self.btn_today)

        self.btn_yesterday.setProperty("role", "action_kick" if is_yesterday else "action_outlined")
        self.btn_yesterday.style().unpolish(self.btn_yesterday)
        self.btn_yesterday.style().polish(self.btn_yesterday)

    def _on_today_clicked(self):
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        self._current_date = today_str
        self._update_button_states(today_str)
        self._sync_combo_without_event(today_str)
        self.date_selected.emit(today_str)

    def _on_yesterday_clicked(self):
        yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self._current_date = yesterday_str
        self._update_button_states(yesterday_str)
        self._sync_combo_without_event(yesterday_str)
        self.date_selected.emit(yesterday_str)

    def _on_combo_date_changed(self, index: int):
        if self._is_populating_dates or index <= 0:
            return
        selected_date = self.combo_dates.itemData(index)
        if selected_date and selected_date != self._current_date:
            self._current_date = selected_date
            self._update_button_states(selected_date)
            self.date_selected.emit(selected_date)

    def _sync_combo_without_event(self, date_str: str):
        self._is_populating_dates = True
        try:
            idx = self.combo_dates.findData(date_str)
            if idx >= 0:
                self.combo_dates.setCurrentIndex(idx)
            else:
                self.combo_dates.setCurrentIndex(0)
        finally:
            self._is_populating_dates = False

    def populate_available_dates(self, dates: list[str]):
        self._is_populating_dates = True
        try:
            self.combo_dates.clear()
            self.combo_dates.addItem(self.i18n.get("dashboard.chatters.filter_date_placeholder"), "")
            self._available_dates = list(dates)
            for d in dates:
                self.combo_dates.addItem(d, d)
            idx = self.combo_dates.findData(self._current_date)
            if idx >= 0:
                self.combo_dates.setCurrentIndex(idx)
        finally:
            self._is_populating_dates = False

    def set_widget_active(self, is_active: bool):
        self._is_widget_active = bool(is_active)
        self.banner_inactive.setVisible(not self._is_widget_active)
        if not self._is_widget_active:
            self.lbl_empty_desc.setText(self.i18n.get("dashboard.chatters.empty_inactive_desc"))
        else:
            self.lbl_empty_desc.setText(self.i18n.get("dashboard.chatters.empty_desc"))

    def set_chatters(self, chatters_list: list[dict], total_messages: int = 0):
        if not chatters_list:
            self.table.setRowCount(0)
            self.stack.setCurrentIndex(1)
            return

        self.table.setRowCount(len(chatters_list))
        calc_total = total_messages if total_messages > 0 else sum(c.get("count", 0) for c in chatters_list)

        for row_idx, item in enumerate(chatters_list):
            user = item.get("user", "-")
            count = int(item.get("count", 0))
            color = item.get("color") or COLOR_GREEN
            platform = (item.get("platform") or "kick").lower()
            rank = row_idx + 1

            lbl_rank = QLabel(f"#{rank}")
            lbl_rank.setProperty("role", "rank_number")
            lbl_rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if rank == 1:
                lbl_rank.setProperty("state", "gold")
            elif rank == 2:
                lbl_rank.setProperty("state", "silver")
            elif rank == 3:
                lbl_rank.setProperty("state", "bronze")
            else:
                lbl_rank.setProperty("state", "normal")
            self.table.setCellWidget(row_idx, 0, lbl_rank)

            lbl_user = QLabel()
            lbl_user.setText(f"<span style='color: {color}; font-weight: 600;'>{user}</span>")
            lbl_user.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setCellWidget(row_idx, 1, lbl_user)

            lbl_plat = QLabel(platform.capitalize())
            lbl_plat.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if platform == "kick":
                lbl_plat.setProperty("role", "badge_kick")
            elif platform == "twitch":
                lbl_plat.setProperty("role", "badge_twitch")
            else:
                lbl_plat.setProperty("role", "badge")
            self.table.setCellWidget(row_idx, 2, lbl_plat)

            lbl_msgs = QLabel(f"{count:,}")
            lbl_msgs.setProperty("role", "body")
            lbl_msgs.setProperty("state", "white")
            lbl_msgs.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            self.table.setCellWidget(row_idx, 3, lbl_msgs)

            share_pct = (count / calc_total * 100) if calc_total > 0 else 0.0
            share_widget = QWidget()
            share_layout = QHBoxLayout(share_widget)
            share_layout.setContentsMargins(4, 2, 8, 2)
            share_layout.setSpacing(SPACING_XS)

            pbar = QProgressBar(share_widget)
            pbar.setProperty("role", "top_command_progress")
            pbar.setTextVisible(False)
            pbar.setRange(0, 100)
            pbar.setValue(min(100, int(share_pct)))
            pbar.setFixedHeight(6)

            lbl_pct = QLabel(f"{share_pct:.1f}%", share_widget)
            lbl_pct.setProperty("role", "caption")
            lbl_pct.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

            share_layout.addWidget(pbar, stretch=1)
            share_layout.addWidget(lbl_pct)
            self.table.setCellWidget(row_idx, 4, share_widget)

            self.table.setRowHeight(row_idx, 34)

        self.stack.setCurrentIndex(0)
