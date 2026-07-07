# frontend\views\network_view.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QLabel
from PySide6.QtCore import Qt, Signal
from frontend.widgets.blocks_component import ViewHeader
from frontend.widgets.controls_component import ModernButton
from frontend.common.theme import (
    COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED, 
    COLOR_ACCENT, COLOR_WARNING, COLOR_DANGER, COLOR_BLACK
)
from frontend.common.utils import get_icon_colored

class NetworkStatusCard(QFrame):
    def __init__(self, key: str, title: str, description: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setProperty("role", "card")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)
        
        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(36, 36)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_icon)
        
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(2)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setProperty("role", "h3")
        self.info_layout.addWidget(self.lbl_title)
        
        self.lbl_desc = QLabel(description)
        self.lbl_desc.setProperty("role", "body")
        self.lbl_desc.setWordWrap(True)
        self.info_layout.addWidget(self.lbl_desc)
        
        self.layout.addLayout(self.info_layout, stretch=1)
        
        self.status_layout = QVBoxLayout()
        self.status_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.status_layout.setSpacing(4)
        
        self.lbl_status = QLabel()
        self.lbl_status.setProperty("role", "h3")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_layout.addWidget(self.lbl_status)
        
        self.lbl_latency = QLabel()
        self.lbl_latency.setProperty("role", "caption")
        self.lbl_latency.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_layout.addWidget(self.lbl_latency)
        
        self.layout.addLayout(self.status_layout)
        
        self.icon_name = icon_name
        self.set_icon(COLOR_TEXT_PRIMARY)
        
    def set_icon(self, color_hex: str):
        icon = get_icon_colored(self.icon_name, color_hex, size=24)
        self.lbl_icon.setPixmap(icon.pixmap(24, 24))
        
    def set_status(self, status: str, latency: int, status_text: str):
        if status == "checking":
            color = COLOR_TEXT_MUTED
            self.lbl_status.setText(status_text)
            self.lbl_latency.setText("")
            self.set_icon(COLOR_TEXT_MUTED)
        elif status == "online":
            color = COLOR_ACCENT
            self.lbl_status.setText(status_text)
            self.lbl_latency.setText(f"{latency} ms")
            self.set_icon(COLOR_ACCENT)
        elif status == "warning":
            color = COLOR_WARNING
            self.lbl_status.setText(status_text)
            self.lbl_latency.setText(f"{latency} ms")
            self.set_icon(COLOR_WARNING)
        else:
            color = COLOR_DANGER
            self.lbl_status.setText(status_text)
            self.lbl_latency.setText("-")
            self.set_icon(COLOR_DANGER)
            
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold;")


class NetworkView(QWidget):
    check_requested = Signal()
    view_shown = Signal()

    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self.cards = {}
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)
        
        header = ViewHeader(
            title_text=self.i18n.get("network.header.title"),
            subtitle_text=self.i18n.get("network.header.subtitle"),
            icon_name="access-point.svg",
            icon_color=COLOR_TEXT_PRIMARY
        )
        self.main_layout.addWidget(header)
        self.main_layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        self.btn_check = ModernButton(self.i18n.get("network.btn_check"), role="action_accent")
        self.btn_check.setIcon(get_icon_colored("refresh.svg", COLOR_BLACK, 16))
        self.btn_check.setFixedWidth(200)
        self.btn_check.clicked.connect(self.check_requested.emit)
        btn_layout.addWidget(self.btn_check)
        btn_layout.addStretch()
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addSpacing(6)
        
        self._add_card("internet", self.i18n.get("network.services.internet"), self.i18n.get("network.services.internet_desc"), "wifi.svg")
        self._add_card("chat_websocket", self.i18n.get("network.services.chat_websocket"), self.i18n.get("network.services.chat_websocket_desc"), "message.svg")
        self._add_card("overlay", self.i18n.get("network.services.overlay"), self.i18n.get("network.services.overlay_desc"), "plug.svg")
        self._add_card("kick", self.i18n.get("network.services.kick"), self.i18n.get("network.services.kick_desc"), "kick.svg")
        self._add_card("spotify", self.i18n.get("network.services.spotify"), self.i18n.get("network.services.spotify_desc"), "spotify.svg")
        self._add_card("youtube", self.i18n.get("network.services.youtube"), self.i18n.get("network.services.youtube_desc"), "brand-youtube.svg")
        
        self.main_layout.addStretch()
        scroll.setWidget(content)
        base_layout.addWidget(scroll)

    def _add_card(self, key: str, title: str, description: str, icon: str):
        card = NetworkStatusCard(key, title, description, icon, self)
        self.cards[key] = card
        self.main_layout.addWidget(card)

    def set_checking_state(self):
        self.btn_check.setEnabled(False)
        for card in self.cards.values():
            card.set_status("checking", -1, self.i18n.get("network.status.checking"))

    def update_status(self, results: dict):
        self.btn_check.setEnabled(True)
        for key, info in results.items():
            if key in self.cards:
                status = info["status"]
                latency = info["latency"]
                
                status_text = self.i18n.get(f"network.status.{status}")
                self.cards[key].set_status(status, latency, status_text)

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()
