# frontend\components\alerts\sidebar_panel.py

from typing import Dict, List, Tuple
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Signal
from frontend.widgets import ModernCard, ModernDivider
from .variant_item import AlertVariantListItem

class AlertsSidebarPanel(ModernCard):
    variant_selected = Signal(str)

    def __init__(self, platform: str, events: List[Tuple[str, str]], i18n, parent=None):
        super().__init__(parent=parent, margin=10, spacing=8)
        self.platform = platform
        self.events = events
        self.i18n = i18n
        self.items: Dict[str, AlertVariantListItem] = {}

        self.setFixedWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._setup_ui()

    def _setup_ui(self):
        lbl_sidebar_title = QLabel(self.i18n.get("alerts.sidebar.title"), parent=self)
        lbl_sidebar_title.setProperty("role", "h3")
        self.addWidget(lbl_sidebar_title)
        self.addWidget(ModernDivider(self))

        for alert_type, icon_name in self.events:
            item = AlertVariantListItem(self.platform, alert_type, icon_name, self.i18n, parent=self)
            item.clicked.connect(self._on_item_clicked)
            self.addWidget(item)
            self.items[alert_type] = item

        self.addStretch()

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
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        if is_horizontal:
            self.setFixedWidth(240)
