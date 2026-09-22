# frontend\components\chat\bot_mute.py

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListView, 
                               QFrame, QPushButton, QListWidgetItem, QVBoxLayout)
from PySide6.QtCore import Qt, Signal, QEvent, QSize
from frontend.widgets import ModernButton, ModernCard, ModernSwitch, SettingRow, SectionHeader
from frontend.common import (
    COLOR_RED, get_icon_colored,
    MARGIN_NONE, MARGIN_MD, MARGIN_SETTING_ROW_COMPACT, MARGIN_TAG_BADGE, MARGIN_TAB_PANEL,
    SPACING_NONE, SPACING_2XS, SPACING_SM, SPACING_MD
)

class BotMutePanel(QWidget):
    bot_add_requested = Signal(str)
    bot_remove_requested = Signal(str)
    word_add_requested = Signal(str)
    word_remove_requested = Signal(str)
    settings_changed = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.setProperty("role", "tab_panel")
        self.i18n = i18n
        self._trash_icon_cache = {}
        self._setup_ui()

    def addWidget(self, widget, *args, **kwargs):
        self.panel_layout.addWidget(widget, *args, **kwargs)

    def addLayout(self, layout, *args, **kwargs):
        self.panel_layout.addLayout(layout, *args, **kwargs)

    def addStretch(self, stretch: int = 0):
        self.panel_layout.addStretch(stretch)

    def _setup_ui(self):
        self.panel_layout = QVBoxLayout(self)
        self.panel_layout.setContentsMargins(*MARGIN_TAB_PANEL)
        self.panel_layout.setSpacing(SPACING_MD)

        header_commands = SectionHeader(self.i18n.get("chat.mod_commands.section_title"), parent=self, first=True)
        self.panel_layout.addWidget(header_commands)

        commands_card = ModernCard(parent=self, margin=MARGIN_NONE, spacing=SPACING_NONE, orientation="vertical")
        self.sw_cmd_mute = ModernSwitch(self)
        self.sw_cmd_mute.setChecked(True)
        self.sw_cmd_block = ModernSwitch(self)
        self.sw_cmd_block.setChecked(True)

        row_cmd_mute = SettingRow(
            "shield-user-filled.svg",
            self.i18n.get("chat.mod_commands.mute_cmd_title"),
            self.i18n.get("chat.mod_commands.mute_cmd_desc"),
            self.sw_cmd_mute,
            contents_margins=MARGIN_SETTING_ROW_COMPACT
        )
        row_cmd_block = SettingRow(
            "shield-filled.svg",
            self.i18n.get("chat.mod_commands.block_cmd_title"),
            self.i18n.get("chat.mod_commands.block_cmd_desc"),
            self.sw_cmd_block,
            contents_margins=MARGIN_SETTING_ROW_COMPACT
        )
        commands_card.addWidget(row_cmd_mute)
        commands_card.add_separator()
        commands_card.addWidget(row_cmd_block)
        self.panel_layout.addWidget(commands_card)

        self.sw_cmd_mute.toggled.connect(lambda _: self.settings_changed.emit())
        self.sw_cmd_block.toggled.connect(lambda _: self.settings_changed.emit())

        header_bots = SectionHeader(self.i18n.get("chat.bots.title"), parent=self)
        self.panel_layout.addWidget(header_bots)

        bots_card = ModernCard(parent=self, margin=MARGIN_MD, spacing=SPACING_SM, orientation="vertical")
        input_row = QHBoxLayout()
        input_row.setContentsMargins(*MARGIN_NONE)
        input_row.setSpacing(SPACING_SM)
        
        self.txt_bot_input = QLineEdit()
        self.txt_bot_input.setPlaceholderText(self.i18n.get("chat.bots.input_placeholder"))
        
        self.btn_add_bot = ModernButton(self.i18n.get("common.buttons.add"), role="action_outlined", parent=self)
        self.btn_add_bot.set_icon("plus-filled.svg", size=16)
            
        input_row.addWidget(self.txt_bot_input)
        input_row.addWidget(self.btn_add_bot)
        bots_card.addLayout(input_row)

        self.list_bots = QListWidget()
        self.list_bots.setFlow(QListView.Flow.LeftToRight) 
        self.list_bots.setWrapping(True) 
        self.list_bots.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_bots.setProperty("role", "transparent_list")
        self.list_bots.setFrameShape(QFrame.Shape.NoFrame)
        self.list_bots.setSpacing(SPACING_2XS)
        bots_card.addWidget(self.list_bots)
        self.panel_layout.addWidget(bots_card)

        self.btn_add_bot.clicked.connect(lambda: self.bot_add_requested.emit(self.txt_bot_input.text()))
        self.txt_bot_input.returnPressed.connect(lambda: self.bot_add_requested.emit(self.txt_bot_input.text()))

        header_words = SectionHeader(self.i18n.get("chat.banned_words.title"), parent=self)
        self.panel_layout.addWidget(header_words)

        words_card = ModernCard(parent=self, margin=MARGIN_MD, spacing=SPACING_SM, orientation="vertical")
        input_row_words = QHBoxLayout()
        input_row_words.setContentsMargins(*MARGIN_NONE)
        input_row_words.setSpacing(SPACING_SM)
        
        self.txt_word_input = QLineEdit()
        self.txt_word_input.setPlaceholderText(self.i18n.get("chat.banned_words.input_placeholder"))
        
        self.btn_add_word = ModernButton(self.i18n.get("common.buttons.add"), role="action_outlined", parent=self)
        self.btn_add_word.set_icon("plus-filled.svg", size=16)
            
        input_row_words.addWidget(self.txt_word_input)
        input_row_words.addWidget(self.btn_add_word)
        words_card.addLayout(input_row_words)

        self.list_words = QListWidget()
        self.list_words.setFlow(QListView.Flow.LeftToRight) 
        self.list_words.setWrapping(True) 
        self.list_words.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_words.setProperty("role", "transparent_list")
        self.list_words.setFrameShape(QFrame.Shape.NoFrame)
        self.list_words.setSpacing(SPACING_2XS)
        words_card.addWidget(self.list_words)
        self.panel_layout.addWidget(words_card)

        self.btn_add_word.clicked.connect(lambda: self.word_add_requested.emit(self.txt_word_input.text()))
        self.txt_word_input.returnPressed.connect(lambda: self.word_add_requested.emit(self.txt_word_input.text()))

        self.panel_layout.addStretch()

    def clear_input(self):
        self.txt_bot_input.clear()

    def clear_word_input(self):
        self.txt_word_input.clear()

    def set_command_toggles(self, mute_enabled: bool, block_enabled: bool) -> None:
        self.sw_cmd_mute.blockSignals(True)
        self.sw_cmd_block.blockSignals(True)
        try:
            self.sw_cmd_mute.setChecked(mute_enabled)
            self.sw_cmd_block.setChecked(block_enabled)
        finally:
            self.sw_cmd_mute.blockSignals(False)
            self.sw_cmd_block.blockSignals(False)

    @property
    def mod_mute_command_enabled(self) -> bool:
        return self.sw_cmd_mute.isChecked()

    @mod_mute_command_enabled.setter
    def mod_mute_command_enabled(self, value: bool) -> None:
        self.sw_cmd_mute.blockSignals(True)
        self.sw_cmd_mute.setChecked(value)
        self.sw_cmd_mute.blockSignals(False)

    @property
    def mod_block_command_enabled(self) -> bool:
        return self.sw_cmd_block.isChecked()

    @mod_block_command_enabled.setter
    def mod_block_command_enabled(self, value: bool) -> None:
        self.sw_cmd_block.blockSignals(True)
        self.sw_cmd_block.setChecked(value)
        self.sw_cmd_block.blockSignals(False)

    def _configure_tag_item(self, item: QListWidgetItem, tag_widget: QFrame):
        lbl_name = tag_widget.findChild(QLabel)
        btn_delete = tag_widget.findChild(QPushButton)
        if lbl_name and btn_delete:
            lbl_name.ensurePolished()
            btn_delete.ensurePolished()
            
            fm = lbl_name.fontMetrics()
            font_height = fm.height()
            icon_size = max(14, int(font_height * 0.75))
            btn_size = max(22, font_height + 4)
            
            if icon_size not in self._trash_icon_cache:
                self._trash_icon_cache[icon_size] = get_icon_colored("trash-filled.svg", COLOR_RED, size=icon_size)
            
            btn_delete.setIcon(self._trash_icon_cache[icon_size])
            btn_delete.setIconSize(QSize(icon_size, icon_size))
            btn_delete.setFixedSize(btn_size, btn_size)
            
            text_width = fm.horizontalAdvance(lbl_name.text())
            total_width = btn_size + text_width + 20
            total_height = max(btn_size, font_height) + 14
            
            item.setSizeHint(QSize(total_width, total_height))

    def recalculate_item_sizes(self):
        for list_widget in [self.list_bots, self.list_words]:
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                tag_widget = list_widget.itemWidget(item)
                if tag_widget:
                    self._configure_tag_item(item, tag_widget)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event and event.type() in (QEvent.Type.StyleChange, QEvent.Type.FontChange):
            self.recalculate_item_sizes()

    def _add_tag_item(self, list_widget: QListWidget, text: str, remove_callback):
        item = QListWidgetItem(text)
        list_widget.addItem(item)
        
        tag_widget = QFrame()
        tag_widget.setProperty("role", "bot_tag")
        layout = QHBoxLayout(tag_widget)
        layout.setContentsMargins(*MARGIN_TAG_BADGE)
        layout.setSpacing(SPACING_2XS)
        layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
        
        lbl_name = QLabel(text)
        
        btn_delete = QPushButton()
        btn_delete.setProperty("role", "btn_ghost")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.clicked.connect(lambda checked=False, i=item: remove_callback(i))
        
        layout.addWidget(btn_delete)
        layout.addWidget(lbl_name)
        
        list_widget.setItemWidget(item, tag_widget)
        self._configure_tag_item(item, tag_widget)

    def add_bot_tag(self, bot_name: str):
        self._add_tag_item(self.list_bots, bot_name, self._on_bot_remove_click)

    def remove_bot_tag(self, bot_name: str):
        clean = bot_name.lower()
        for i in range(self.list_bots.count()):
            item = self.list_bots.item(i)
            if item and item.text().lower() == clean:
                self.list_bots.takeItem(i)
                break

    def add_word_tag(self, word: str):
        self._add_tag_item(self.list_words, word, self._on_word_remove_click)

    def remove_word_tag(self, word: str):
        clean = word.lower()
        for i in range(self.list_words.count()):
            item = self.list_words.item(i)
            if item and item.text().lower() == clean:
                self.list_words.takeItem(i)
                break

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
