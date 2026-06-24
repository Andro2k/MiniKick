# frontend\navigation\bot_panel_component.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QListWidget, QListView, 
                               QFrame, QPushButton, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from frontend.widgets.controls_component import ModernButton
from frontend.common.theme import COLOR_BLACK, COLOR_DANGER
from frontend.common.utils import get_icon_colored

class BotMutePanel(QWidget):
    bot_add_requested = Signal(str)
    bot_remove_requested = Signal(str)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(self.i18n.get("chat.bots.title"))
        title.setProperty("role", "h3")
        layout.addWidget(title)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(6)
        
        self.txt_bot_input = QLineEdit()
        self.txt_bot_input.setPlaceholderText(self.i18n.get("chat.bots.input_placeholder"))
        
        self.btn_add_bot = ModernButton(self.i18n.get("chat.bots.btn_add"), role="action_accent")
        self.btn_add_bot.setIcon(get_icon_colored("add.svg", COLOR_BLACK, size=16))
            
        input_row.addWidget(self.txt_bot_input)
        input_row.addWidget(self.btn_add_bot)
        layout.addLayout(input_row)

        self.list_bots = QListWidget()
        self.list_bots.setFlow(QListView.Flow.LeftToRight) 
        self.list_bots.setWrapping(True) 
        self.list_bots.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_bots.setProperty("role", "transparent_list")
        
        self.list_bots.setFrameShape(QFrame.Shape.NoFrame)
        self.list_bots.setViewportMargins(0, 0, 0, 0)
        self.list_bots.setContentsMargins(0, 0, 0, 0)
        self.list_bots.setSpacing(2)

        layout.addWidget(self.list_bots)

        self.btn_add_bot.clicked.connect(lambda: self.bot_add_requested.emit(self.txt_bot_input.text()))
        self.txt_bot_input.returnPressed.connect(lambda: self.bot_add_requested.emit(self.txt_bot_input.text()))

    def clear_input(self):
        self.txt_bot_input.clear()

    def add_bot_tag(self, bot_name: str):
        item = QListWidgetItem(bot_name)
        self.list_bots.addItem(item)
        
        tag_widget = QFrame()
        tag_widget.setProperty("role", "tag")
        layout = QHBoxLayout(tag_widget)
        layout.setContentsMargins(4, 4, 8, 4) 
        layout.setSpacing(4)
        layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
        
        lbl_name = QLabel(bot_name)
        btn_delete = QPushButton()
        btn_delete.setProperty("role", "btn_ghost")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setIcon(get_icon_colored("trash.svg", COLOR_DANGER, size=16))
        btn_delete.setFixedSize(24, 24)
        btn_delete.clicked.connect(lambda checked=False, i=item: self._on_bot_remove_click(i))
        
        layout.addWidget(btn_delete)
        layout.addWidget(lbl_name)
        
        item.setSizeHint(tag_widget.sizeHint())
        self.list_bots.setItemWidget(item, tag_widget)

    def clear_list(self):
        self.list_bots.clear()

    def _on_bot_remove_click(self, item: QListWidgetItem):
        bot_name = item.text()
        row = self.list_bots.row(item)
        self.list_bots.takeItem(row)
        self.bot_remove_requested.emit(bot_name)