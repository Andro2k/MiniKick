# frontend\components\alerts\variant_item.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from frontend.common import get_pixmap_colored, COLOR_GREEN, COLOR_PURPLE

class AlertVariantListItem(QFrame):
    clicked = Signal(str)

    def __init__(self, platform: str, alert_type: str, icon_name: str, i18n, parent=None):
        super().__init__(parent=parent)
        self.platform = platform
        self.alert_type = alert_type
        self.icon_name = icon_name
        self.i18n = i18n
        self._is_selected = False
        self._is_enabled = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("role", "banner_scope_card")
        self.setProperty("state", "normal")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        accent = COLOR_GREEN if self.platform == "kick" else COLOR_PURPLE
        self.icon_lbl = QLabel(parent=self)
        self.icon_lbl.setPixmap(get_pixmap_colored(self.icon_name, accent, size=20))
        self.icon_lbl.setFixedSize(22, 22)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel(self.i18n.get(f"alerts.events.{self.alert_type}"), parent=self)
        self.lbl_title.setProperty("role", "body")

        self.lbl_desc = QLabel(self.i18n.get(f"alerts.events.{self.alert_type}_desc"), parent=self)
        self.lbl_desc.setProperty("role", "caption")
        self.lbl_desc.setWordWrap(True)

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_desc)

        self.status_lbl = QLabel("●", parent=self)
        self.status_lbl.setProperty("role", "caption")
        self.status_lbl.setProperty("state", "normal")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.icon_lbl)
        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(self.status_lbl)

    def set_enabled_state(self, enabled: bool):
        self._is_enabled = enabled
        self.status_lbl.setProperty("state", "success" if enabled else "normal")
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

    def set_selected(self, selected: bool):
        self._is_selected = selected
        target_state = self.platform if selected else "normal"
        self.setProperty("state", target_state)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.alert_type)
        super().mousePressEvent(event)
