# frontend\components\chat\bot_mute.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListView, 
                               QFrame, QPushButton, QListWidgetItem)
from PySide6.QtCore import Qt, Signal, QEvent, QSize
from frontend.widgets import ModernButton
from frontend.common.theme import COLOR_BLACK, COLOR_RED
from frontend.common.utils import get_icon_colored

class BotMutePanel(QWidget):
    bot_add_requested = Signal(str)
    bot_remove_requested = Signal(str)
    word_add_requested = Signal(str)
    word_remove_requested = Signal(str)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel(self.i18n.get("chat.bots.title"))
        title.setProperty("role", "h3")
        layout.addWidget(title)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(6)
        
        self.txt_bot_input = QLineEdit()
        self.txt_bot_input.setPlaceholderText(self.i18n.get("chat.bots.input_placeholder"))
        
        self.btn_add_bot = ModernButton(self.i18n.get("common.buttons.add"), role="action_accent")
        self.btn_add_bot.setIcon(get_icon_colored("add.svg", COLOR_BLACK, size=16))
        self.btn_add_bot.setIconSize(QSize(16, 16))
            
        input_row.addWidget(self.txt_bot_input)
        input_row.addWidget(self.btn_add_bot)
        layout.addLayout(input_row)

        self.list_bots = QListWidget()
        self.list_bots.setFlow(QListView.Flow.LeftToRight) 
        self.list_bots.setWrapping(True) 
        self.list_bots.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_bots.setProperty("role", "transparent_list")
        self.list_bots.setFrameShape(QFrame.Shape.NoFrame)
        self.list_bots.setSpacing(2)
        layout.addWidget(self.list_bots)

        self.btn_add_bot.clicked.connect(lambda: self.bot_add_requested.emit(self.txt_bot_input.text()))
        self.txt_bot_input.returnPressed.connect(lambda: self.bot_add_requested.emit(self.txt_bot_input.text()))

        divider = QFrame()
        divider.setProperty("role", "divider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)
        title_words = QLabel(self.i18n.get("chat.banned_words.title"))
        title_words.setProperty("role", "h3")
        layout.addWidget(title_words)

        input_row_words = QHBoxLayout()
        input_row_words.setContentsMargins(0, 0, 0, 0)
        input_row_words.setSpacing(6)
        
        self.txt_word_input = QLineEdit()
        self.txt_word_input.setPlaceholderText(self.i18n.get("chat.banned_words.input_placeholder"))
        
        self.btn_add_word = ModernButton(self.i18n.get("common.buttons.add"), role="action_accent")
        self.btn_add_word.setIcon(get_icon_colored("add.svg", COLOR_BLACK, size=16))
        self.btn_add_word.setIconSize(QSize(16, 16))
            
        input_row_words.addWidget(self.txt_word_input)
        input_row_words.addWidget(self.btn_add_word)
        layout.addLayout(input_row_words)

        self.list_words = QListWidget()
        self.list_words.setFlow(QListView.Flow.LeftToRight) 
        self.list_words.setWrapping(True) 
        self.list_words.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_words.setProperty("role", "transparent_list")
        self.list_words.setFrameShape(QFrame.Shape.NoFrame)
        self.list_words.setSpacing(2)
        layout.addWidget(self.list_words)

        self.btn_add_word.clicked.connect(lambda: self.word_add_requested.emit(self.txt_word_input.text()))
        self.txt_word_input.returnPressed.connect(lambda: self.word_add_requested.emit(self.txt_word_input.text()))

    def clear_input(self):
        self.txt_bot_input.clear()

    def clear_word_input(self):
        self.txt_word_input.clear()

    def recalculate_item_sizes(self):
        for list_widget in [self.list_bots, self.list_words]:
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                tag_widget = list_widget.itemWidget(item)
                if tag_widget:
                    lbl_name = tag_widget.findChild(QLabel)
                    btn_delete = tag_widget.findChild(QPushButton)
                    if lbl_name and btn_delete:
                        lbl_name.ensurePolished()
                        btn_delete.ensurePolished()
                        
                        fm = lbl_name.fontMetrics()
                        font_height = fm.height()
                        icon_size = max(14, int(font_height * 0.75))
                        btn_size = max(22, font_height + 4)
                        
                        btn_delete.setIcon(get_icon_colored("trash.svg", COLOR_RED, size=icon_size))
                        btn_delete.setIconSize(QSize(icon_size, icon_size))
                        btn_delete.setFixedSize(btn_size, btn_size)
                        
                        text_width = fm.horizontalAdvance(lbl_name.text())
                        total_width = btn_size + text_width + 20
                        total_height = max(btn_size, font_height) + 14
                        
                        item.setSizeHint(QSize(total_width, total_height))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event and event.type() in (QEvent.Type.StyleChange, QEvent.Type.FontChange):
            self.recalculate_item_sizes()

    def add_bot_tag(self, bot_name: str):
        item = QListWidgetItem(bot_name)
        self.list_bots.addItem(item)
        
        tag_widget = QFrame()
        tag_widget.setProperty("role", "bot_tag")
        layout = QHBoxLayout(tag_widget)
        layout.setContentsMargins(4, 4, 8, 4) 
        layout.setSpacing(2)
        layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
        
        lbl_name = QLabel(bot_name)
        
        btn_delete = QPushButton()
        btn_delete.setProperty("role", "btn_ghost")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.clicked.connect(lambda checked=False, i=item: self._on_bot_remove_click(i))
        
        layout.addWidget(btn_delete)
        layout.addWidget(lbl_name)
        
        self.list_bots.setItemWidget(item, tag_widget)
        self.recalculate_item_sizes()

    def add_word_tag(self, word: str):
        item = QListWidgetItem(word)
        self.list_words.addItem(item)
        
        tag_widget = QFrame()
        tag_widget.setProperty("role", "bot_tag")
        layout = QHBoxLayout(tag_widget)
        layout.setContentsMargins(4, 4, 8, 4) 
        layout.setSpacing(2)
        layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
        
        lbl_name = QLabel(word)
        
        btn_delete = QPushButton()
        btn_delete.setProperty("role", "btn_ghost")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.clicked.connect(lambda checked=False, i=item: self._on_word_remove_click(i))
        
        layout.addWidget(btn_delete)
        layout.addWidget(lbl_name)
        
        self.list_words.setItemWidget(item, tag_widget)
        self.recalculate_item_sizes()

    def clear_list(self):
        self.list_bots.clear()

    def clear_words_list(self):
        self.list_words.clear()

    def _on_bot_remove_click(self, item: QListWidgetItem):
        bot_name = item.text()
        row = self.list_bots.row(item)
        self.list_bots.takeItem(row)
        self.bot_remove_requested.emit(bot_name)

    def _on_word_remove_click(self, item: QListWidgetItem):
        word = item.text()
        row = self.list_words.row(item)
        self.list_words.takeItem(row)
        self.word_remove_requested.emit(word)
