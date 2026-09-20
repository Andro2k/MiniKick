# frontend\components\alerts\variants_tab_bar.py

from __future__ import annotations
from typing import Dict, List, Tuple, Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from frontend.common import (
    get_pixmap_colored, COLOR_GREEN, COLOR_PURPLE, COLOR_NEUTRAL_400,
    SPACING_XS, SPACING_SM, MARGIN_NONE, MARGIN_TAB_BAR
)
from frontend.widgets import ModernSwitch, ModernCard

class AlertVariantTabPill(QFrame):
    clicked = Signal(str)
    toggled = Signal(str, bool)

    def __init__(
        self,
        platform: str,
        alert_type: str,
        icon_name: str,
        i18n,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent=parent)
        self.platform = platform
        self.alert_type = alert_type
        self.icon_name = icon_name
        self.i18n = i18n
        self._is_selected = False
        self._is_enabled = True

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._setup_ui()
        self._update_appearance()

    def _setup_ui(self):
        self.setProperty("role", "banner_scope_card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_TAB_BAR)
        layout.setSpacing(SPACING_SM)

        self.icon_lbl = QLabel(parent=self)
        self.icon_lbl.setFixedSize(16, 16)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_text = self.i18n.get(f"alerts.events.{self.alert_type}")
        self.lbl_title = QLabel(title_text, parent=self)
        self.lbl_title.setProperty("role", "caption")
        self.lbl_title.setProperty("state", "bold")

        self.sw_enabled = ModernSwitch(parent=self)
        self.sw_enabled.setToolTip(self.i18n.get("alerts.fields.active"))
        self.sw_enabled.setFixedSize(32, 18)
        self.sw_enabled.toggled.connect(self._on_toggled)

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.lbl_title)
        layout.addSpacing(SPACING_XS)
        layout.addWidget(self.sw_enabled)

    def _on_toggled(self, checked: bool):
        self._is_enabled = checked
        self.toggled.emit(self.alert_type, checked)

    def set_enabled_state(self, enabled: bool):
        self._is_enabled = enabled
        self.sw_enabled.blockSignals(True)
        self.sw_enabled.setChecked(enabled)
        self.sw_enabled.blockSignals(False)
        self._update_appearance()

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._update_appearance()

    def _update_appearance(self):
        accent = COLOR_GREEN if self.platform == "kick" else COLOR_PURPLE

        if self._is_selected:
            self.setProperty("state", self.platform)
            self.lbl_title.setProperty("state", "white")
            self.icon_lbl.setPixmap(get_pixmap_colored(self.icon_name, accent, size=16))
        else:
            self.setProperty("state", "normal")
            self.lbl_title.setProperty("state", "normal")
            self.icon_lbl.setPixmap(get_pixmap_colored(self.icon_name, COLOR_NEUTRAL_400, size=16))

        if self.style():
            self.style().unpolish(self)
            self.style().polish(self)
            self.lbl_title.style().unpolish(self.lbl_title)
            self.lbl_title.style().polish(self.lbl_title)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.alert_type)
        super().mousePressEvent(event)

class AlertVariantsTabBar(ModernCard):
    variant_selected = Signal(str)
    variant_enabled_changed = Signal(str, bool)

    def __init__(
        self,
        platform: str,
        events: List[Tuple[str, str]],
        i18n,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent=parent, margin=SPACING_SM, spacing=SPACING_SM)
        self.platform = platform
        self.events = events
        self.i18n = i18n
        self.items: Dict[str, AlertVariantTabPill] = {}

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(60)

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(*MARGIN_NONE)
        container_layout.setSpacing(SPACING_SM)

        for alert_type, icon_name in self.events:
            tab = AlertVariantTabPill(
                platform=self.platform,
                alert_type=alert_type,
                icon_name=icon_name,
                i18n=self.i18n,
                parent=container
            )
            tab.clicked.connect(self._on_item_clicked)
            tab.toggled.connect(lambda at, enabled: self.variant_enabled_changed.emit(at, enabled))

            container_layout.addWidget(tab)
            self.items[alert_type] = tab

        container_layout.addStretch(1)
        scroll.setWidget(container)

        self.addWidget(scroll)

    def _on_item_clicked(self, alert_type: str):
        self.select_variant(alert_type)
        self.variant_selected.emit(alert_type)

    def select_variant(self, alert_type: str):
        for at, item in self.items.items():
            item.set_selected(at == alert_type)

    def set_item_enabled_state(self, alert_type: str, enabled: bool):
        item = self.items.get(alert_type)
        if item is not None:
            item.set_enabled_state(enabled)

    def set_responsive_mode(self, is_horizontal: bool):
        pass
