# frontend/components/blocks.py

from PySide6.QtWidgets import QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from frontend.utils import get_icon_colored
from frontend.theme import COLOR_ACCENT, COLOR_TEXT_PRIMARY

class ViewHeader(QFrame):
    def __init__(self, title_text: str, subtitle_text: str, icon_name: str, icon_color: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, icon_color, size=28).pixmap(28, 28))
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title = QLabel(title_text)
        title.setProperty("role", "h1")
        
        subtitle = QLabel(subtitle_text)
        subtitle.setProperty("role", "body")
        
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(text_layout)
        layout.addStretch()

class SettingRow(QWidget):
    def __init__(self, icon_name: str, title_text: str, desc_text: str, right_widget: QWidget, icon_color: str = COLOR_TEXT_PRIMARY, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, icon_color, size=18).pixmap(18, 18))

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        lbl_title = QLabel(title_text)
        lbl_title.setProperty("role", "h3")
        
        lbl_desc = QLabel(desc_text)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)

        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(right_widget, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

class SettingSliderRow(QWidget):
    def __init__(self, icon_name: str, title_text: str, desc_text: str, slider_widget: QWidget, value_label: QLabel, icon_color: str = COLOR_TEXT_PRIMARY, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, icon_color, size=18).pixmap(18, 18))

        lbl_title = QLabel(title_text)
        lbl_title.setProperty("role", "h3")

        header_row.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(lbl_title, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_row.addStretch()
        header_row.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        lbl_desc = QLabel(desc_text)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)

        layout.addLayout(header_row)
        layout.addWidget(lbl_desc)
        layout.addWidget(slider_widget)

class StatCard(QFrame):
    def __init__(self, title_text: str, icon_name: str, initial_value: str = "-", parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        self.setMinimumWidth(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, COLOR_ACCENT, size=16).pixmap(16, 16))

        self.lbl_title = QLabel(title_text)
        self.lbl_title.setProperty("role", "h3")

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.lbl_value = QLabel(initial_value)
        self.lbl_value.setProperty("role", "stat_value")
        self.lbl_value.setWordWrap(True)

        layout.addLayout(header_layout)
        layout.addWidget(self.lbl_value)
        layout.addStretch()

    def set_value(self, value: str):
        self.lbl_value.setText(str(value))