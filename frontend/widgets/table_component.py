# frontend/widgets/table_component.py

from PySide6.QtWidgets import (QTableWidget, QFrame, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QWidget)
from PySide6.QtCore import Qt
from frontend.widgets.controls_component import ModernButton, ModernSwitch
from frontend.common.theme import COLOR_NEUTRAL_1000
from frontend.common.utils import get_icon_colored

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
                self.lbl_title.setProperty("role", "h4")
                self.header_layout.addWidget(self.lbl_title)
                
            self.header_layout.addStretch()
            
            if search_placeholder:
                self.txt_search = QLineEdit()
                self.txt_search.setPlaceholderText(search_placeholder)
                self.header_layout.addWidget(self.txt_search)
                
            if add_button_text:
                self.btn_add = ModernButton(add_button_text, role="action_accent")
                if add_button_icon:
                    self.btn_add.setIcon(get_icon_colored(add_button_icon, COLOR_NEUTRAL_1000, 16))
                self.header_layout.addWidget(self.btn_add)
                
            self.card_layout.addLayout(self.header_layout)
            
        self.table = ModernTable(headers or [])
        self.card_layout.addWidget(self.table)

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
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        return btn
