# frontend\widgets\inspector_widgets.py

from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt

from frontend.common import (
    get_pixmap_colored, COLOR_NEUTRAL_400,
    SPACING_SM, MARGIN_V_XS
)

class InspectorPropertyRow(QWidget):
    def __init__(
        self,
        label: str,
        content_widget: QWidget,
        icon_name: Optional[str] = None,
        tooltip: Optional[str] = None,
        stretch_content: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_V_XS)
        layout.setSpacing(SPACING_SM)

        if icon_name:
            self.lbl_icon = QLabel(self)
            self.lbl_icon.setPixmap(get_pixmap_colored(icon_name, COLOR_NEUTRAL_400, size=14))
            self.lbl_icon.setFixedSize(16, 16)
            self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.lbl_icon)

        self.lbl_title = QLabel(label, self)
        self.lbl_title.setProperty("role", "caption")
        self.lbl_title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.lbl_title)

        if tooltip:
            self.setToolTip(tooltip)
            self.lbl_title.setToolTip(tooltip)

        self.content_widget = content_widget
        if stretch_content:
            layout.addWidget(self.content_widget, 1)
        else:
            layout.addStretch(1)
            layout.addWidget(self.content_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
