# frontend/views/dashboard_view.py

from PySide6.QtWidgets import (QBoxLayout, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from frontend.theme import COLOR_ACCENT
from frontend.utils import create_circular_pixmap, get_icon_colored
from frontend.components.blocks import StatCard, ViewHeader, SettingRow
from frontend.components.controls import ModernButton, ModernSwitch

class DashboardView(QWidget):
    connect_requested = Signal()
    autostart_toggled = Signal(bool)
    reauth_requested = Signal()
    
    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContent")
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        self.header = ViewHeader(
            title_text=self.i18n.get("dashboard.header.title"),
            subtitle_text=self.i18n.get("dashboard.header.subtitle"),
            icon_name="kick.svg",
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        self.banner_scopes = QFrame()
        self.banner_scopes.setProperty("role", "banner_danger")
        banner_layout = QHBoxLayout(self.banner_scopes)
        
        lbl_warn_icon = QLabel()
        lbl_warn_icon.setPixmap(get_icon_colored("help.svg", "#EF4444", 24).pixmap(24, 24))
        lbl_warn_text = QLabel(self.i18n.get("dashboard.banner.text"))
        
        self.btn_reauth = ModernButton(self.i18n.get("dashboard.banner.btn_update"), role="action_danger")
        self.btn_reauth.clicked.connect(self.reauth_requested.emit)
        
        banner_layout.addWidget(lbl_warn_icon)
        banner_layout.addWidget(lbl_warn_text, stretch=1)
        banner_layout.addWidget(self.btn_reauth)
        
        self.banner_scopes.setVisible(False)
        self.main_layout.addWidget(self.banner_scopes)
        self._setup_connection_card()
        self._setup_profile_section()

        self.main_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def _setup_connection_card(self):
        conn_card = QFrame()
        conn_card.setProperty("role", "card")
        conn_layout = QVBoxLayout(conn_card)
        conn_layout.setContentsMargins(10, 10, 10, 10)
        conn_layout.setSpacing(10)

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
        self.status_label.setProperty("role", "subtitle")

        self.btn_connect = ModernButton(self.i18n.get("dashboard.connection.btn_connect"), role="action_accent")
        self.btn_connect.setFixedSize(160, 36)
        self.btn_connect.clicked.connect(self.connect_requested.emit)

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.btn_connect)

        conn_layout.addWidget(row_autostart)
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setProperty("role", "divider")
        conn_layout.addWidget(divider)
        
        conn_layout.addLayout(status_layout)
        self.main_layout.addWidget(conn_card)

    def _setup_profile_section(self):
        self.profile_container = QWidget()
        self.profile_container.setVisible(False)
        profile_layout = QVBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(12) 

        self.top_row_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.top_row_layout.setSpacing(12) 

        avatar_card = QFrame()
        avatar_card.setProperty("role", "card")
        avatar_layout = QVBoxLayout(avatar_card)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(140, 140)
        self.lbl_avatar.setScaledContents(True) 
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_avatar.setText("?")
        avatar_layout.addWidget(self.lbl_avatar)

        info_card = QFrame()
        info_card.setProperty("role", "card")
        info_card.setMinimumHeight(160)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(10, 10, 10, 10)

        self.lbl_username = QLabel("-")
        self.lbl_username.setProperty("role", "h1")
        self.lbl_username.setWordWrap(True)

        self.lbl_bio = QLabel("-")
        self.lbl_bio.setProperty("role", "body")
        self.lbl_bio.setWordWrap(True)

        info_layout.addWidget(self.lbl_username)
        info_layout.addWidget(self.lbl_bio)
        info_layout.addStretch()
        
        self.top_row_layout.addWidget(avatar_card)
        self.top_row_layout.addWidget(info_card, stretch=1)

        stats_container = QWidget()
        self.stats_grid = QGridLayout(stats_container)
        self.stats_grid.setContentsMargins(0, 0, 0, 0)
        self.stats_grid.setSpacing(12)
        
        self.card_followers = StatCard(self.i18n.get("dashboard.stats.followers"), "users.svg")
        self.card_room = StatCard(self.i18n.get("dashboard.stats.room_id"), "hash.svg")
        self.card_category = StatCard(self.i18n.get("dashboard.stats.category"), "device-gamepad.svg") 
        self.card_affiliate = StatCard(self.i18n.get("dashboard.stats.affiliate"), "star.svg")
        self.card_vods = StatCard(self.i18n.get("dashboard.stats.vods"), "video.svg")

        self.stats_grid.addWidget(self.card_followers, 0, 0)
        self.stats_grid.addWidget(self.card_room, 0, 1)
        self.stats_grid.addWidget(self.card_category, 0, 2)
        self.stats_grid.addWidget(self.card_affiliate, 1, 0)
        self.stats_grid.addWidget(self.card_vods, 1, 1)

        profile_layout.addLayout(self.top_row_layout)
        profile_layout.addWidget(stats_container) 
        self.main_layout.addWidget(self.profile_container)

    def set_autostart_state(self, enabled: bool):
        self.sw_autostart.blockSignals(True)
        self.sw_autostart.setChecked(enabled)
        self.sw_autostart.blockSignals(False)

    def update_connection_status(self, is_connecting: bool, has_error: bool = False, error_msg: str = ""):
        if is_connecting:
            self.status_label.setText(self.i18n.get("dashboard.connection.status_auth"))
            self.btn_connect.setEnabled(False)
            self.profile_container.setVisible(False)
            self.lbl_avatar.setPixmap(QPixmap())
        elif has_error:
            self.status_label.setText(f"{self.i18n.get('dashboard.connection.status_error')}: {error_msg}")
            self.status_label.setProperty("state", "error")
            self.btn_connect.setEnabled(True)
            self.btn_connect.setText(self.i18n.get("dashboard.connection.btn_retry"))
            self.profile_container.setVisible(False)
        else:
            self.status_label.setText(self.i18n.get("dashboard.connection.status_connected"))
            self.status_label.setObjectName("State_Connected") 
            self.btn_connect.setText(self.i18n.get("dashboard.connection.btn_active"))
            self.btn_connect.setEnabled(False)
            self.profile_container.setVisible(True)
            
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

    def set_avatar_from_bytes(self, image_data: bytes):
        pixmap = create_circular_pixmap(image_data)
        if not pixmap.isNull():
            self.lbl_avatar.setPixmap(pixmap)
            self.lbl_avatar.setProperty("has_image", True)
            self.lbl_avatar.style().unpolish(self.lbl_avatar)
            self.lbl_avatar.style().polish(self.lbl_avatar)
    
    def reset_to_disconnected(self):
        self.status_label.setText(self.i18n.get("dashboard.connection.status_waiting"))
        self.status_label.setProperty("state", "idle")
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText(self.i18n.get("dashboard.connection.btn_connect"))
        self.profile_container.setVisible(False)
        self.lbl_avatar.setPixmap(QPixmap())
        
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def show_scope_warning(self, show: bool):
        self.banner_scopes.setVisible(show)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()

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
            cards = [self.card_followers, self.card_room, self.card_category, self.card_affiliate, self.card_vods]
            for i, card in enumerate(cards):
                self.stats_grid.addWidget(card, i // cols, i % cols)