# frontend\widgets\blocks_component.py

from PySide6.QtWidgets import QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from frontend.common.utils import get_icon_colored
from frontend.common.theme import COLOR_NEUTRAL_200

class ViewHeader(QFrame):
    def __init__(self, title_text: str, subtitle_text: str, icon_name: str, icon_color: str, title_color: str = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, icon_color, size=28).pixmap(28, 28))
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title = QLabel(title_text)
        title.setProperty("role", "h1")
        if title_color:
            title.setStyleSheet(f"color: {title_color};")
        
        subtitle = QLabel(subtitle_text)
        subtitle.setProperty("role", "body")
        subtitle.setWordWrap(True)
        subtitle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(text_layout)
        layout.addStretch()

class SettingRow(QWidget):
    def __init__(self, icon_name: str, title_text: str, desc_text: str, right_widget: QWidget, icon_color: str = COLOR_NEUTRAL_200, title_color: str = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, icon_color, size=18).pixmap(18, 18))

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        lbl_title = QLabel(title_text)
        lbl_title.setProperty("role", "h3")
        if title_color:
            lbl_title.setStyleSheet(f"color: {title_color};")
        
        lbl_desc = QLabel(desc_text)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)

        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(right_widget, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

class SliderRow(QWidget):
    def __init__(self, icon_name: str, title_text: str, desc_text: str, slider_widget: QWidget, value_label: QLabel, icon_color: str = COLOR_NEUTRAL_200, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        header_row = QHBoxLayout()
        header_row.setSpacing(6)

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
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, COLOR_NEUTRAL_200, size=14).pixmap(14, 14))

        self.lbl_title = QLabel(title_text)
        self.lbl_title.setProperty("role", "h3")

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.lbl_value = QLabel(initial_value)
        self.lbl_value.setProperty("role", "body")
        self.lbl_value.setWordWrap(True)

        layout.addLayout(header_layout)
        layout.addWidget(self.lbl_value)
        layout.addStretch()

    def set_value(self, value: str):
        self.lbl_value.setText(str(value))

class ModernCard(QFrame):
    def __init__(self, parent=None, margin=8, spacing=6, orientation="vertical"):
        super().__init__(parent)
        self.setProperty("role", "card")
        
        if orientation == "horizontal":
            self.card_layout = QHBoxLayout(self)
        else:
            self.card_layout = QVBoxLayout(self)
            
        self.card_layout.setContentsMargins(margin, margin, margin, margin)
        self.card_layout.setSpacing(spacing)
        
    def addWidget(self, widget, *args, **kwargs):
        self.card_layout.addWidget(widget, *args, **kwargs)
        
    def addLayout(self, layout, *args, **kwargs):
        self.card_layout.addLayout(layout, *args, **kwargs)

    def addSpacing(self, spacing: int):
        self.card_layout.addSpacing(spacing)

    def addStretch(self, stretch: int = 0):
        self.card_layout.addStretch(stretch)
