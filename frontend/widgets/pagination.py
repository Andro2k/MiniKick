# frontend\widgets\pagination.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QSize
from frontend.common.utils import get_icon_colored
from frontend.common.theme import COLOR_NEUTRAL_200

class SegmentedPagination(QFrame):
    first_requested = Signal()
    prev_requested = Signal()
    next_requested = Signal()
    last_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("role", "segmented_pagination")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_first = QPushButton(self)
        self.btn_first.setObjectName("btn_first")
        self.btn_first.setIcon(get_icon_colored("chevrons-left.svg", COLOR_NEUTRAL_200, 16))
        self.btn_first.setIconSize(QSize(16, 16))
        self.btn_first.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_first.clicked.connect(self.first_requested.emit)

        self.btn_prev = QPushButton(self)
        self.btn_prev.setObjectName("btn_prev")
        self.btn_prev.setIcon(get_icon_colored("chevron-left.svg", COLOR_NEUTRAL_200, 16))
        self.btn_prev.setIconSize(QSize(16, 16))
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.clicked.connect(self.prev_requested.emit)

        self.lbl_page_status = QLabel("1 / 1", self)
        self.lbl_page_status.setObjectName("lbl_page_status")
        self.lbl_page_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_next = QPushButton(self)
        self.btn_next.setObjectName("btn_next")
        self.btn_next.setIcon(get_icon_colored("chevron-right.svg", COLOR_NEUTRAL_200, 16))
        self.btn_next.setIconSize(QSize(16, 16))
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self.next_requested.emit)

        self.btn_last = QPushButton(self)
        self.btn_last.setObjectName("btn_last")
        self.btn_last.setIcon(get_icon_colored("chevrons-right.svg", COLOR_NEUTRAL_200, 16))
        self.btn_last.setIconSize(QSize(16, 16))
        self.btn_last.setCursor(Qt.CursorShape.PointingHandCursor)
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
