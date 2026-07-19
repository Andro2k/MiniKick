# frontend\widgets\table.py

import os
from PySide6.QtWidgets import QTableWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QWidget, QStackedWidget
from PySide6.QtCore import Qt, QSize
from .controls import ModernButton, ModernSwitch
from .scalable_illustration import ScalableIllustration
from frontend.common.theme import COLOR_BLACK
from frontend.common.utils import get_icon_colored, get_assets_path

class ModernTable(QTableWidget):
    def __init__(self, headers: list[str], parent=None):
        super().__init__(0, len(headers), parent)
        self.setHorizontalHeaderLabels(headers)     
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(38)
        self.setShowGrid(False)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

class ModernTableCard(QFrame):
    def __init__(self, title_text: str = None, headers: list[str] = None, 
                 search_placeholder: str = None, add_button_text: str = None, 
                 add_button_icon: str = "add.svg", parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(8, 8, 8, 8)
        self.card_layout.setSpacing(6)
        
        self.header_layout = None
        self.lbl_title = None
        self.txt_search = None
        self.btn_add = None
        
        if title_text or search_placeholder or add_button_text:
            self.header_layout = QHBoxLayout()
            
            if title_text:
                self.lbl_title = QLabel(title_text)
                self.lbl_title.setProperty("role", "h3")
                self.header_layout.addWidget(self.lbl_title)
                
            self.header_layout.addStretch()
            
            if search_placeholder:
                self.txt_search = QLineEdit()
                self.txt_search.setPlaceholderText(search_placeholder)
                self.header_layout.addWidget(self.txt_search)
                
            if add_button_text:
                self.btn_add = ModernButton(add_button_text, role="action_accent")
                if add_button_icon:
                    self.btn_add.setIcon(get_icon_colored(add_button_icon, COLOR_BLACK, 16))
                    self.btn_add.setIconSize(QSize(16, 16))
                self.header_layout.addWidget(self.btn_add)
                
            self.card_layout.addLayout(self.header_layout)
            
        self.stack = QStackedWidget()
        
        self.table = ModernTable(headers or [])
        self.stack.addWidget(self.table)
        
        self.empty_widget = None
        self.lbl_illustration = None
        
        self.card_layout.addWidget(self.stack)

    def setup_empty_state(self, title: str, desc: str, icon_name: str, button_text: str, on_button_clicked):
        self.empty_widget = QWidget()
        layout = QVBoxLayout(self.empty_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        illustration_path = get_assets_path(os.path.join("icons", icon_name))
        self.lbl_illustration = ScalableIllustration(
            icon_path=illustration_path,
            aspect_ratio=1.0,
            min_size=80,
            max_size=160,
            size_offset=200,
            parent=self
        )
        
        lbl_title = QLabel(title)
        lbl_title.setProperty("role", "h2")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_desc = QLabel(desc)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setMaximumWidth(450)
        
        self.btn_empty_action = ModernButton(button_text, role="action_accent")
        self.btn_empty_action.setIcon(get_icon_colored("add.svg", COLOR_BLACK, 16))
        self.btn_empty_action.setIconSize(QSize(16, 16))
        self.btn_empty_action.setFixedWidth(200)
        self.btn_empty_action.clicked.connect(on_button_clicked)
        
        layout.addStretch(1)
        layout.addWidget(self.lbl_illustration, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addSpacing(8)
        layout.addWidget(self.btn_empty_action, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(2)
        
        self.stack.addWidget(self.empty_widget)

    def set_empty(self, is_empty: bool):
        if is_empty and self.stack.count() > 1:
            self.stack.setCurrentIndex(1)
            if self.txt_search and not self.txt_search.text().strip():
                self.txt_search.setVisible(False)
        else:
            self.stack.setCurrentIndex(0)
            if self.txt_search:
                self.txt_search.setVisible(True)
        if is_empty and hasattr(self, "lbl_illustration") and self.lbl_illustration:
            card_h = max(self.height(), 300)
            self.lbl_illustration.update_image(card_h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "lbl_illustration") and self.lbl_illustration and self.stack.currentIndex() == 1:
            card_h = max(self.height(), 300)
            self.lbl_illustration.update_image(card_h)

class TableActionCell(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 4, 0)
        self.layout.setSpacing(6)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def add_switch(self, checked: bool, callback) -> ModernSwitch:
        sw = ModernSwitch()
        sw.setChecked(checked)
        sw.toggled.connect(callback)
        self.layout.addWidget(sw)
        self.layout.addSpacing(4)
        return sw
        
    def add_button(self, icon_name: str, color: str, role: str, tooltip: str, callback) -> ModernButton:
        btn = ModernButton("", role=role)
        btn.setFixedSize(28, 28)
        btn.setIcon(get_icon_colored(icon_name, color, size=16))
        btn.setIconSize(QSize(16, 16))
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        return btn
