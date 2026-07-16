# frontend\views\dashboard_view.py

import os
from PySide6.QtWidgets import (QBoxLayout, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QPainterPath
from frontend.common.theme import COLOR_BLACK, COLOR_RED, COLOR_NEUTRAL_800, COLOR_GREEN, COLOR_BLUE, COLOR_PURPLE
from frontend.common.utils import create_circular_pixmap, get_icon_colored, get_assets_path
from frontend.widgets.base_view import BaseView
from frontend.widgets.blocks import StatCard, SettingRow, ModernCard
from frontend.widgets.scalable_illustration import ScalableIllustration
from frontend.widgets.controls import ModernButton, ModernSwitch

class SegmentedDistributionBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self._segments = []

    def set_data(self, data: list[tuple[float, str]]):
        self._segments = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 8, 8)
        painter.setClipPath(path)
        
        total_p = sum(p for p, _ in self._segments)
        if total_p <= 0:
            painter.fillRect(rect, QColor(COLOR_NEUTRAL_800))
            return
            
        current_x = 0.0
        width = float(rect.width())
        height = float(rect.height())
        
        for percent, color_str in self._segments:
            if percent <= 0:
                continue
            seg_width = percent * width
            seg_rect = QRectF(current_x, 0, seg_width, height)
            painter.fillRect(seg_rect, QColor(color_str))
            current_x += seg_width

class DashboardView(BaseView):
    connect_requested = Signal()
    autostart_toggled = Signal(bool)
    reauth_requested = Signal()
    
    def __init__(self, i18n):
        super().__init__(
            i18n=i18n,
            title_key="dashboard.header.title",
            subtitle_key="dashboard.header.subtitle"
        )
        self._stats_cols = -1
        self._setup_ui()

    def _setup_ui(self):
        self.banner_scopes = QFrame()
        self.banner_scopes.setProperty("role", "banner_danger")
        self.banner_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.banner_scopes)
        self.banner_layout.setSpacing(8)
        
        lbl_warn_icon = QLabel()
        lbl_warn_icon.setPixmap(get_icon_colored("help.svg", COLOR_RED, 24).pixmap(24, 24))
        lbl_warn_icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.lbl_warn_text = QLabel()
        self.lbl_warn_text.setWordWrap(True)
        
        self.btn_reauth = ModernButton(self.i18n.get("dashboard.banner.btn_update"), role="action_danger_border")
        self.btn_reauth.clicked.connect(self.reauth_requested.emit)
        
        self.banner_layout.addWidget(lbl_warn_icon)
        self.banner_layout.addWidget(self.lbl_warn_text, stretch=1)
        self.banner_layout.addWidget(self.btn_reauth)
        
        self.banner_scopes.setVisible(False)
        self.main_layout.addWidget(self.banner_scopes)
        
        self._setup_connection_card()
        
        self.disconnected_container = QWidget()
        disconnected_layout = QVBoxLayout(self.disconnected_container)
        disconnected_layout.setContentsMargins(24, 24, 24, 24)
        disconnected_layout.setSpacing(12)
        disconnected_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        illustration_path = get_assets_path(os.path.join("icons", "install_small.svg"))
        self.lbl_illustration = ScalableIllustration(
            icon_path=illustration_path, aspect_ratio=1.0, min_size=120, 
            max_size=300, size_offset=320, parent=self
        )
        
        self.lbl_disconnected_title = QLabel(self.i18n.get("dashboard.empty.title"))
        self.lbl_disconnected_title.setProperty("role", "h2")
        self.lbl_disconnected_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_disconnected_desc = QLabel(self.i18n.get("dashboard.empty.desc"))
        self.lbl_disconnected_desc.setProperty("role", "body")
        self.lbl_disconnected_desc.setWordWrap(True)
        self.lbl_disconnected_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_disconnected_desc.setMaximumWidth(450)
        
        disconnected_layout.addStretch(1)
        disconnected_layout.addWidget(self.lbl_illustration, alignment=Qt.AlignmentFlag.AlignCenter)
        disconnected_layout.addWidget(self.lbl_disconnected_title)
        disconnected_layout.addWidget(self.lbl_disconnected_desc)
        disconnected_layout.addStretch(2)
        
        self.main_layout.addWidget(self.disconnected_container, stretch=1)
        
        self._setup_profile_section()
        self.main_layout.addStretch()

    def _setup_connection_card(self):
        conn_card = ModernCard()

        self.sw_autostart = ModernSwitch()
        self.sw_autostart.toggled.connect(self.autostart_toggled.emit)
        
        row_autostart = SettingRow(
            "plug.svg", 
            self.i18n.get("dashboard.connection.autostart_title"), 
            self.i18n.get("dashboard.connection.autostart_desc"), 
            self.sw_autostart
        )

        status_layout = QHBoxLayout()
        self.status_label = QLabel(self.i18n.get("dashboard.connection.status_waiting"))
        self.status_label.setProperty("role", "body")
        self.status_label.setWordWrap(True)

        self.btn_connect = ModernButton(self.i18n.get("dashboard.connection.btn_connect"), role="action_accent")
        self.btn_connect.setIcon(get_icon_colored("kick.svg", COLOR_BLACK, 16))
        self.btn_connect.clicked.connect(self.connect_requested.emit)

        status_layout.addWidget(self.status_label, stretch=1)
        status_layout.addWidget(self.btn_connect, alignment=Qt.AlignmentFlag.AlignVCenter)

        conn_card.addWidget(row_autostart)
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setProperty("role", "divider")
        conn_card.addWidget(divider)
        
        conn_card.addLayout(status_layout)
        self.main_layout.addWidget(conn_card)

    def _setup_profile_section(self):
        self.profile_container = QWidget()
        self.profile_container.setVisible(False)
        profile_layout = QVBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(12) 

        self.top_row_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.top_row_layout.setSpacing(12) 

        avatar_card = ModernCard()
        avatar_card.card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(140, 140)
        self.lbl_avatar.setScaledContents(True) 
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_avatar.setText("?")
        avatar_card.addWidget(self.lbl_avatar)

        info_card = ModernCard()

        self.lbl_username = QLabel("-")
        self.lbl_username.setProperty("role", "h1")
        self.lbl_username.setWordWrap(True)

        self.lbl_bio = QLabel("-")
        self.lbl_bio.setProperty("role", "body")
        self.lbl_bio.setWordWrap(True)

        info_card.addWidget(self.lbl_username)
        info_card.addWidget(self.lbl_bio)
        info_card.card_layout.addStretch()
        
        self.top_row_layout.addWidget(avatar_card)
        self.top_row_layout.addWidget(info_card, stretch=1)

        stats_container = QWidget()
        self.stats_grid = QGridLayout(stats_container)
        self.stats_grid.setContentsMargins(0, 0, 0, 0)
        self.stats_grid.setSpacing(12)
        
        self.card_followers = StatCard(self.i18n.get("dashboard.stats.followers"), "users.svg")
        self.card_room = StatCard(self.i18n.get("dashboard.stats.room_id"), "hash.svg")
        self.card_category = StatCard(self.i18n.get("dashboard.stats.category"), "category.svg") 
        self.card_affiliate = StatCard(self.i18n.get("dashboard.stats.affiliate"), "star.svg")
        self.card_vods = StatCard(self.i18n.get("dashboard.stats.vods"), "video.svg")

        self.stats_grid.addWidget(self.card_followers, 0, 0)
        self.stats_grid.addWidget(self.card_room, 0, 1)
        self.stats_grid.addWidget(self.card_category, 0, 2)
        self.stats_grid.addWidget(self.card_affiliate, 1, 0)
        self.stats_grid.addWidget(self.card_vods, 1, 1)

        profile_layout.addLayout(self.top_row_layout)
        profile_layout.addWidget(stats_container) 

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setProperty("role", "divider")
        profile_layout.addWidget(divider)

        lbl_session_title = QLabel(self.i18n.get("dashboard.session.title"))
        lbl_session_title.setProperty("role", "h2")
        profile_layout.addWidget(lbl_session_title)

        bar_card = ModernCard(margin=8)
        self.session_bar = SegmentedDistributionBar()
        bar_card.addWidget(self.session_bar)
        profile_layout.addWidget(bar_card)

        session_stats_container = QWidget()
        self.session_grid = QGridLayout(session_stats_container)
        self.session_grid.setContentsMargins(0, 0, 0, 0)
        self.session_grid.setSpacing(12)

        self.card_msg_processed = StatCard(self.i18n.get("dashboard.session.messages"), "message.svg", "0")
        self.card_cmd_executed = StatCard(self.i18n.get("dashboard.session.commands"), "code.svg", "0")
        self.card_timers_sent = StatCard(self.i18n.get("dashboard.session.timers"), "clock.svg", "0")
        self.card_spam_blocked = StatCard(self.i18n.get("dashboard.session.spam"), "shield-half.svg", "0")

        self.session_grid.addWidget(self.card_msg_processed, 0, 0)
        self.session_grid.addWidget(self.card_cmd_executed, 0, 1)
        self.session_grid.addWidget(self.card_timers_sent, 0, 2)
        self.session_grid.addWidget(self.card_spam_blocked, 0, 3)

        profile_layout.addWidget(session_stats_container)

        self.main_layout.addWidget(self.profile_container)

    def set_autostart_state(self, enabled: bool):
        self.sw_autostart.blockSignals(True)
        self.sw_autostart.setChecked(enabled)
        self.sw_autostart.blockSignals(False)

    def update_connection_status(self, is_connecting: bool, has_error: bool = False, error_msg: str = ""):
        if is_connecting:
            self.status_label.setText(self.i18n.get("dashboard.connection.status_auth"))
            self.status_label.setProperty("state", "normal")
            self.btn_connect.setEnabled(False)
            self.profile_container.setVisible(False)
            self.lbl_avatar.setPixmap(QPixmap())
            self.disconnected_container.setVisible(True)
        elif has_error:
            self.status_label.setText(f"{self.i18n.get('common.status.error')}: {error_msg}")
            self.status_label.setProperty("state", "error")
            self.btn_connect.setEnabled(True)
            self.btn_connect.setText(self.i18n.get("dashboard.connection.btn_retry"))
            self.profile_container.setVisible(False)
            self.disconnected_container.setVisible(True)
        else:
            self.status_label.setText(self.i18n.get("dashboard.connection.status_connected"))
            self.status_label.setProperty("state", "normal")
            self.btn_connect.setText(self.i18n.get("dashboard.connection.btn_active"))
            self.btn_connect.setEnabled(False)
            self.profile_container.setVisible(True)
            self.disconnected_container.setVisible(False)
            
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def update_profile_info(self, username: str, bio: str):
        self.lbl_username.setText(username)
        self.lbl_bio.setText(bio)

    def update_stats(self, followers: str, room_id: str, category: str, affiliate_text: str, vods_text: str):
        self.card_followers.set_value(followers)
        self.card_room.set_value(room_id)
        self.card_category.set_value(category)
        self.card_affiliate.set_value(affiliate_text)
        self.card_vods.set_value(vods_text)

    def update_session_metrics(self, msg_count: int, cmd_count: int, timer_count: int, spam_count: int):
        total = msg_count + cmd_count + timer_count + spam_count
        
        if total > 0:
            p_msg = msg_count / total
            p_cmd = cmd_count / total
            p_timer = timer_count / total
            p_spam = spam_count / total
            
            pct_msg = f"{p_msg * 100:.1f}%"
            pct_cmd = f"{p_cmd * 100:.1f}%"
            pct_timer = f"{p_timer * 100:.1f}%"
            pct_spam = f"{p_spam * 100:.1f}%"
            
            self.card_msg_processed.set_value(f"{msg_count}   ·   {pct_msg}")
            self.card_cmd_executed.set_value(f"{cmd_count}   ·   {pct_cmd}")
            self.card_timers_sent.set_value(f"{timer_count}   ·   {pct_timer}")
            self.card_spam_blocked.set_value(f"{spam_count}   ·   {pct_spam}")
            
            if hasattr(self, 'session_bar'):
                self.session_bar.set_data([
                    (p_msg, COLOR_PURPLE),
                    (p_cmd, COLOR_BLUE),
                    (p_timer, COLOR_GREEN),
                    (p_spam, COLOR_RED)
                ])
        else:
            self.card_msg_processed.set_value("0   ·   0.0%")
            self.card_cmd_executed.set_value("0   ·   0.0%")
            self.card_timers_sent.set_value("0   ·   0.0%")
            self.card_spam_blocked.set_value("0   ·   0.0%")
            if hasattr(self, 'session_bar'):
                self.session_bar.set_data([])

    def set_avatar_from_bytes(self, image_data: bytes):
        pixmap = create_circular_pixmap(image_data)
        if not pixmap.isNull():
            self.lbl_avatar.setPixmap(pixmap)
            self.lbl_avatar.setProperty("has_image", True)
            self.lbl_avatar.style().unpolish(self.lbl_avatar)
            self.lbl_avatar.style().polish(self.lbl_avatar)
    
    def reset_to_disconnected(self):
        self.status_label.setText(self.i18n.get("dashboard.connection.status_waiting"))
        self.status_label.setProperty("state", "normal")
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText(self.i18n.get("dashboard.connection.btn_connect"))
        self.profile_container.setVisible(False)
        self.lbl_avatar.setPixmap(QPixmap())
        self.disconnected_container.setVisible(True)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def show_scope_warning(self, missing_scope_keys: list):
        if not missing_scope_keys:
            self.banner_scopes.setVisible(False)
            return
        scope_names = ", ".join(
            f"<b>{self.i18n.get(key)}</b>" for key in missing_scope_keys
        )
        prefix = self.i18n.get("dashboard.banner.text_prefix")
        self.lbl_warn_text.setText(f"{prefix} {scope_names}.")
        self.banner_scopes.setVisible(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        if hasattr(self, 'banner_layout'):
            if width < 480:
                self.banner_layout.setDirection(QBoxLayout.Direction.TopToBottom)
                self.lbl_warn_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            else:
                self.banner_layout.setDirection(QBoxLayout.Direction.LeftToRight)
                self.lbl_warn_text.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        if hasattr(self, 'top_row_layout'):
            if width < 600:
                self.top_row_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            else:
                self.top_row_layout.setDirection(QBoxLayout.Direction.LeftToRight)
        if hasattr(self, 'stats_grid'):
            if width < 650:
                cols = 1
            elif width < 950:
                cols = 2
            else:
                cols = 3
            if cols != self._stats_cols:
                self._stats_cols = cols
                cards = [self.card_followers, self.card_room, self.card_category, self.card_affiliate, self.card_vods]
                for i, card in enumerate(cards):
                    self.stats_grid.addWidget(card, i // cols, i % cols)
        if hasattr(self, 'session_grid'):
            if width < 650:
                cols = 1
            elif width < 950:
                cols = 2
            else:
                cols = 4
            if cols != getattr(self, '_session_cols', -1):
                self._session_cols = cols
                cards = [self.card_msg_processed, self.card_cmd_executed, self.card_timers_sent, self.card_spam_blocked]
                for i, card in enumerate(cards):
                    self.session_grid.addWidget(card, i // cols, i % cols)
                    
        if hasattr(self, "disconnected_container") and self.disconnected_container.isVisible():
            self.lbl_illustration.update_image(self.height())
