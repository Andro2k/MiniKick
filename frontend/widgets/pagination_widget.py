# frontend\widgets\pagination.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from frontend.common import Size
from .controls_widget import ModernButton

class SegmentedPagination(QFrame):
    first_requested = Signal()
    prev_requested = Signal()
    next_requested = Signal()
    last_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("role", "segmented_pagination")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*Size.Margin.MRG_NON)
        layout.setSpacing(Size.SPACING_NN)

        self.btn_first = ModernButton(icon_name="angles-left-filled.svg", role="", parent=self)
        self.btn_first.setObjectName("btn_first")
        self.btn_first.clicked.connect(self.first_requested.emit)

        self.btn_prev = ModernButton(icon_name="chevron-left-filled.svg", role="", parent=self)
        self.btn_prev.setObjectName("btn_prev")
        self.btn_prev.clicked.connect(self.prev_requested.emit)

        self.lbl_page_status = QLabel("1 / 1", self)
        self.lbl_page_status.setObjectName("lbl_page_status")
        self.lbl_page_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_next = ModernButton(icon_name="chevron-right-filled.svg", role="", parent=self)
        self.btn_next.setObjectName("btn_next")
        self.btn_next.clicked.connect(self.next_requested.emit)

        self.btn_last = ModernButton(icon_name="angles-right-filled.svg", role="", parent=self)
        self.btn_last.setObjectName("btn_last")
        self.btn_last.clicked.connect(self.last_requested.emit)

        layout.addWidget(self.btn_first)
        layout.addWidget(self.btn_prev)
        layout.addWidget(self.lbl_page_status)
        layout.addWidget(self.btn_next)
        layout.addWidget(self.btn_last)

    def set_page_info(self, current_page: int, total_pages: int):
        total_pages = max(1, total_pages)
        current_page = max(1, min(current_page, total_pages))

        self.lbl_page_status.setText(f"{current_page} / {total_pages}")
        self.btn_first.setEnabled(current_page > 1)
        self.btn_prev.setEnabled(current_page > 1)
        self.btn_next.setEnabled(current_page < total_pages)
        self.btn_last.setEnabled(current_page < total_pages)
