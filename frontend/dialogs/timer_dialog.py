# frontend\dialogs\timer_dialog.py

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QSpinBox, QWidget, QScrollArea, QFrame, QCheckBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from .base_dialog import ModernWizardPanel, ModernModal
from frontend.widgets import ModernButton, ModernSwitch, VariableTextEdit, CategorySearchComboBox
from frontend.common.theme import COLOR_RED, COLOR_GREEN
from frontend.common import get_icon_colored, get_assets_path

class TimerConfigWizard(ModernWizardPanel):
    search_category_requested = Signal(str, str)

    def __init__(self, i18n, parent=None, existing_config=None, connected_platforms: dict[str, bool] = None):
        self.i18n = i18n
        self.connected_platforms = connected_platforms if isinstance(connected_platforms, dict) else {"kick": True, "twitch": True}
        title_steps = [
            self.i18n.get("timer.dialog.step_general_title"),
            self.i18n.get("timer.dialog.step_filters_title")
        ]
        subtitle_steps = [
            self.i18n.get("timer.dialog.step_general_subtitle"),
            self.i18n.get("timer.dialog.step_filters_subtitle")
        ]
        super().__init__(title_steps=title_steps, subtitle_steps=subtitle_steps, i18n=i18n, width=820, parent=parent)        
        self.existing_config = existing_config
        self.timer_id = existing_config.get("id") if existing_config else None
        self.message_rows = []       
        
        self._icon_edit = get_icon_colored("edit.svg", COLOR_GREEN, 14)
        self._icon_trash = get_icon_colored("trash.svg", COLOR_RED, 14)
        
        self._setup_ui()
        if self.existing_config:
            self._load_existing()
        else:
            self._add_message_field()            
        self.start_wizard()

    def _setup_ui(self):
        suffix_min = f" {self.i18n.get('timer.dialog.suffix_min')}"
        suffix_lines = f" {self.i18n.get('timer.dialog.suffix_lines')}"

        self.tab_basic = QWidget()
        basic_main_layout = QVBoxLayout(self.tab_basic)
        basic_main_layout.setContentsMargins(0, 0, 0, 0)
        basic_main_layout.setSpacing(12)

        top_card = QFrame()
        top_card.setProperty("role", "card")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(16, 14, 16, 14)
        top_layout.setSpacing(10)

        row_name_plat = QHBoxLayout()
        row_name_plat.setSpacing(20)

        name_box = QVBoxLayout()
        name_box.setSpacing(4)
        lbl_name = QLabel(self.i18n.get("timer.dialog.name_label"))
        lbl_name.setProperty("role", "h3")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText(self.i18n.get("timer.dialog.name_placeholder"))
        self.txt_name.textChanged.connect(self._update_btn_next_state)
        name_box.addWidget(lbl_name)
        name_box.addWidget(self.txt_name)
        row_name_plat.addLayout(name_box, stretch=3)

        plat_box = QVBoxLayout()
        plat_box.setSpacing(4)
        lbl_platform = QLabel(self.i18n.get("timer.dialog.platform_label"))
        lbl_platform.setProperty("role", "h3")
        
        switches_row = QHBoxLayout()
        switches_row.setSpacing(12)

        kick_on = self.connected_platforms.get("kick", False)
        twitch_on = self.connected_platforms.get("twitch", False)
        off_tip = self.i18n.get("timer.dialog.platform_offline")

        kick_switch_box = QHBoxLayout()
        kick_switch_box.setSpacing(6)
        self.switch_kick = ModernSwitch()
        self.switch_kick.setEnabled(kick_on)
        self.switch_kick.setChecked(kick_on)
        if not kick_on:
            self.switch_kick.setToolTip(off_tip)
        lbl_kick = QLabel("Kick")
        lbl_kick.setProperty("role", "body")
        kick_switch_box.addWidget(self.switch_kick)
        kick_switch_box.addWidget(lbl_kick)
        switches_row.addLayout(kick_switch_box)

        twitch_switch_box = QHBoxLayout()
        twitch_switch_box.setSpacing(6)
        self.switch_twitch = ModernSwitch()
        self.switch_twitch.setEnabled(twitch_on)
        self.switch_twitch.setChecked(twitch_on)
        if not twitch_on:
            self.switch_twitch.setToolTip(off_tip)
        lbl_twitch = QLabel("Twitch")
        lbl_twitch.setProperty("role", "body")
        twitch_switch_box.addWidget(self.switch_twitch)
        twitch_switch_box.addWidget(lbl_twitch)
        switches_row.addLayout(twitch_switch_box)
        switches_row.addStretch()

        plat_box.addWidget(lbl_platform)
        plat_box.addLayout(switches_row)
        row_name_plat.addLayout(plat_box, stretch=2)

        top_layout.addLayout(row_name_plat)

        lbl_intervals = QLabel(self.i18n.get("timer.dialog.intervals_label"))
        lbl_intervals.setProperty("role", "h3")
        top_layout.addWidget(lbl_intervals)

        row_intervals = QHBoxLayout()
        row_intervals.setSpacing(20)

        self.chk_online = QCheckBox(self.i18n.get("timer.dialog.online_interval"))
        self.chk_online.setChecked(True)
        self.spin_online = QSpinBox()
        self.spin_online.setRange(1, 1440)
        self.spin_online.setValue(5)
        self.spin_online.setSuffix(suffix_min)
        self.spin_online.setMinimumWidth(100)
        self.chk_online.toggled.connect(self.spin_online.setEnabled)
        self.chk_online.toggled.connect(self._update_btn_next_state)

        row_online = QHBoxLayout()
        row_online.addWidget(self.chk_online, stretch=1)
        row_online.addWidget(self.spin_online)
        row_intervals.addLayout(row_online, stretch=1)

        self.chk_offline = QCheckBox(self.i18n.get("timer.dialog.offline_interval"))
        self.chk_offline.setChecked(False)
        self.spin_offline = QSpinBox()
        self.spin_offline.setRange(1, 1440)
        self.spin_offline.setValue(15)
        self.spin_offline.setSuffix(suffix_min)
        self.spin_offline.setMinimumWidth(100)
        self.spin_offline.setEnabled(False)
        self.chk_offline.toggled.connect(self.spin_offline.setEnabled)
        self.chk_offline.toggled.connect(self._update_btn_next_state)

        row_offline = QHBoxLayout()
        row_offline.addWidget(self.chk_offline, stretch=1)
        row_offline.addWidget(self.spin_offline)
        row_intervals.addLayout(row_offline, stretch=1)

        top_layout.addLayout(row_intervals)

        row_lines = QHBoxLayout()
        row_lines.setSpacing(12)

        self.chk_lines = QCheckBox(self.i18n.get("timer.dialog.enable_chat_lines"))
        self.chk_lines.setChecked(False)
        self.spin_lines = QSpinBox()
        self.spin_lines.setRange(1, 500)
        self.spin_lines.setValue(5)
        self.spin_lines.setSuffix(suffix_lines)
        self.spin_lines.setMinimumWidth(120)
        self.spin_lines.setEnabled(False)
        self.chk_lines.toggled.connect(self.spin_lines.setEnabled)

        lbl_lines_desc = QLabel(self.i18n.get("timer.dialog.chat_lines_desc"))
        lbl_lines_desc.setProperty("role", "caption")
        lbl_lines_desc.setWordWrap(True)

        row_lines.addWidget(self.chk_lines)
        row_lines.addWidget(self.spin_lines)
        row_lines.addSpacing(10)
        row_lines.addWidget(lbl_lines_desc, stretch=1)

        top_layout.addLayout(row_lines)
        basic_main_layout.addWidget(top_card)

        bottom_card = QFrame()
        bottom_card.setProperty("role", "card")
        bottom_layout = QVBoxLayout(bottom_card)
        bottom_layout.setContentsMargins(16, 14, 16, 14)
        bottom_layout.setSpacing(8)

        lbl_msgs_title = QLabel(self.i18n.get("timer.dialog.responses_title"))
        lbl_msgs_title.setProperty("role", "h3")
        bottom_layout.addWidget(lbl_msgs_title)

        lbl_msgs_desc = QLabel(self.i18n.get("timer.dialog.responses_desc"))
        lbl_msgs_desc.setProperty("role", "caption")
        lbl_msgs_desc.setWordWrap(True)
        bottom_layout.addWidget(lbl_msgs_desc)

        self.scroll_msgs = QScrollArea()
        self.scroll_msgs.setWidgetResizable(True)
        self.scroll_msgs.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_msgs.setMinimumHeight(120)
        self.scroll_msgs_widget = QWidget()
        self.msgs_container_layout = QVBoxLayout(self.scroll_msgs_widget)
        self.msgs_container_layout.setContentsMargins(0, 0, 0, 0)
        self.msgs_container_layout.setSpacing(6)
        self.msgs_container_layout.addStretch()
        self.scroll_msgs.setWidget(self.scroll_msgs_widget)
        bottom_layout.addWidget(self.scroll_msgs, stretch=1)

        self.btn_add_msg = ModernButton(self.i18n.get("timer.dialog.btn_add_message"), role="action_outlined")
        self.btn_add_msg.clicked.connect(lambda: self._add_message_field())
        bottom_layout.addWidget(self.btn_add_msg)

        basic_main_layout.addWidget(bottom_card, stretch=1)

        self.tab_filters = QWidget()
        filters_main_layout = QHBoxLayout(self.tab_filters)
        filters_main_layout.setContentsMargins(0, 0, 0, 0)
        filters_main_layout.setSpacing(16)

        left_filt_col = QFrame()
        left_filt_col.setProperty("role", "card")
        left_filt_layout = QVBoxLayout(left_filt_col)
        left_filt_layout.setContentsMargins(16, 16, 16, 16)
        left_filt_layout.setSpacing(10)

        lbl_keywords = QLabel(self.i18n.get("timer.dialog.keywords_label"))
        lbl_keywords.setProperty("role", "h3")
        left_filt_layout.addWidget(lbl_keywords)

        self.txt_keywords = QLineEdit()
        self.txt_keywords.setPlaceholderText(self.i18n.get("timer.dialog.keywords_placeholder"))
        left_filt_layout.addWidget(self.txt_keywords)

        lbl_keywords_desc = QLabel(self.i18n.get("timer.dialog.keywords_desc"))
        lbl_keywords_desc.setProperty("role", "caption")
        lbl_keywords_desc.setWordWrap(True)
        left_filt_layout.addWidget(lbl_keywords_desc)

        lbl_categories = QLabel(self.i18n.get("timer.dialog.categories_label"))
        lbl_categories.setProperty("role", "h3")
        left_filt_layout.addWidget(lbl_categories)

        self.search_category = CategorySearchComboBox(
            placeholder=self.i18n.get("stream_info.quick_change.category_placeholder"),
            default_platform="both",
            parent=self
        )
        self.search_category.category_selected.connect(self._on_category_selected)
        self.search_category.search_requested.connect(self.search_category_requested.emit)
        self.search_category.returnPressed.connect(self._on_category_search_return_pressed)
        left_filt_layout.addWidget(self.search_category)

        self.txt_categories = QLineEdit()
        self.txt_categories.setPlaceholderText(self.i18n.get("timer.dialog.categories_placeholder"))
        left_filt_layout.addWidget(self.txt_categories)
        
        lbl_cat_desc = QLabel(self.i18n.get("timer.dialog.categories_desc"))
        lbl_cat_desc.setProperty("role", "caption")
        lbl_cat_desc.setWordWrap(True)
        left_filt_layout.addWidget(lbl_cat_desc)
        left_filt_layout.addStretch()

        filters_main_layout.addWidget(left_filt_col, stretch=1)

        right_filt_col = QFrame()
        right_filt_col.setProperty("role", "card")
        right_filt_layout = QVBoxLayout(right_filt_col)
        right_filt_layout.setContentsMargins(16, 16, 16, 16)
        right_filt_layout.setSpacing(10)
        
        lbl_help_title = QLabel(self.i18n.get("timer.dialog.help_title"))
        lbl_help_title.setProperty("role", "h3")
        lbl_help_desc = QLabel(self.i18n.get("timer.dialog.help_desc"))
        lbl_help_desc.setWordWrap(True)
        lbl_help_desc.setProperty("role", "body")
        
        right_filt_layout.addWidget(lbl_help_title)
        right_filt_layout.addWidget(lbl_help_desc)
        right_filt_layout.addStretch()
        
        filters_main_layout.addWidget(right_filt_col, stretch=1)

        self.add_page(self.tab_basic)
        self.add_page(self.tab_filters)

    def _on_category_search_return_pressed(self):
        text = self.search_category.text().strip()
        if text:
            current_cats = [c.strip() for c in self.txt_categories.text().split(",") if c.strip()]
            if text not in current_cats:
                current_cats.append(text)
            self.txt_categories.setText(", ".join(current_cats))
            self.search_category.clear()

    def set_category_search_results(self, platform: str, results: list[dict]):
        self.search_category.set_results(platform, results)

    def _on_category_selected(self, data: dict):
        cat_name = data.get("name", "")
        if cat_name:
            current_cats = [c.strip() for c in self.txt_categories.text().split(",") if c.strip()]
            if cat_name not in current_cats:
                current_cats.append(cat_name)
            self.txt_categories.setText(", ".join(current_cats))
            self.search_category.clear()

    def _add_message_field(self, text=""):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        
        txt = QLineEdit()
        txt.setPlaceholderText(self.i18n.get("timer.dialog.response_placeholder"))
        txt.setText(text)
        txt.textChanged.connect(self._update_btn_next_state)
        row_layout.addWidget(txt)
        
        btn_edit = ModernButton("", role="action_accent_border")
        btn_edit.setIcon(self._icon_edit)
        btn_edit.setFixedSize(32, 32)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(lambda: self._open_message_editor(txt))
        row_layout.addWidget(btn_edit)
        
        btn_del = ModernButton("", role="action_danger_border")
        btn_del.setIcon(self._icon_trash)
        btn_del.setFixedSize(32, 32)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.clicked.connect(lambda: self._remove_message_field(row))
        row_layout.addWidget(btn_del)
        
        self.message_rows.append((row, txt))
        self.msgs_container_layout.insertWidget(self.msgs_container_layout.count() - 1, row)
        self._update_btn_next_state()

    def _open_message_editor(self, line_edit: QLineEdit):
        editor = MessageEditorDialog(line_edit.text(), self.i18n, parent=self)
        if editor.exec():
            line_edit.setText(editor.get_text())

    def _remove_message_field(self, row_widget):
        if len(self.message_rows) <= 1:
            return
        
        for r, txt in self.message_rows:
            if r == row_widget:
                self.message_rows.remove((r, txt))
                self.msgs_container_layout.removeWidget(r)
                r.deleteLater()
                break
        self._update_btn_next_state()

    def validate_step(self, step_index: int) -> bool:
        if step_index == 0:
            name = self.txt_name.text().strip()
            if not name:
                return False
            messages = [txt.text().strip() for row, txt in self.message_rows if txt.text().strip()]
            if not messages:
                return False
            if any(len(m) > 492 for m in messages):
                return False
            if not self.chk_online.isChecked() and not self.chk_offline.isChecked():
                return False
        return True

    def _load_existing(self):
        self.txt_name.setText(self.existing_config.get("name", ""))
        kick_on = self.connected_platforms.get("kick", False)
        twitch_on = self.connected_platforms.get("twitch", False)
        self.switch_kick.setChecked(self.existing_config.get("apply_kick", True) if kick_on else False)
        self.switch_twitch.setChecked(self.existing_config.get("apply_twitch", True) if twitch_on else False)
        
        messages = self.existing_config.get("messages", [])
        if not messages:
            self._add_message_field()
        else:
            for m in messages:
                self._add_message_field(m)
            
        online_min = self.existing_config.get("interval_online")
        has_online = online_min is not None and online_min > 0
        self.chk_online.setChecked(has_online)
        if has_online:
            self.spin_online.setValue(online_min)
        else:
            self.spin_online.setEnabled(False)

        offline_min = self.existing_config.get("interval_offline")
        has_offline = offline_min is not None and offline_min > 0
        self.chk_offline.setChecked(has_offline)
        if has_offline:
            self.spin_offline.setValue(offline_min)
        else:
            self.spin_offline.setEnabled(False)

        lines = self.existing_config.get("chat_lines", 0)
        has_lines = lines is not None and lines > 0
        self.chk_lines.setChecked(has_lines)
        if has_lines:
            self.spin_lines.setValue(lines)
        else:
            self.spin_lines.setEnabled(False)

        keywords = self.existing_config.get("keywords", [])
        self.txt_keywords.setText(", ".join(keywords))
        
        categories = self.existing_config.get("categories", [])
        self.txt_categories.setText(", ".join(categories))

    def get_timer_data(self):
        messages = [txt.text().strip() for row, txt in self.message_rows if txt.text().strip()]
        keywords = [kw.strip() for kw in self.txt_keywords.text().split(",") if kw.strip()]
        categories = [cat.strip() for cat in self.txt_categories.text().split(",") if cat.strip()]
        
        interval_online = self.spin_online.value() if self.chk_online.isChecked() else None
        interval_offline = self.spin_offline.value() if self.chk_offline.isChecked() else None
        chat_lines = self.spin_lines.value() if self.chk_lines.isChecked() else 0
        
        is_active = self.existing_config.get("is_active", True) if self.existing_config else True

        return {
            "timer_id": self.timer_id,
            "name": self.txt_name.text().strip(),
            "messages": messages,
            "is_active": is_active,
            "interval_online": interval_online,
            "interval_offline": interval_offline,
            "chat_lines": chat_lines,
            "keywords": keywords,
            "categories": categories,
            "apply_kick": self.switch_kick.isChecked(),
            "apply_twitch": self.switch_twitch.isChecked()
        }

    def _update_step_ui(self):
        super()._update_step_ui()
        self._update_btn_next_state()

    def _update_btn_next_state(self):
        self.btn_next.setEnabled(self.validate_step(self.current_step))
        if self.current_step == 0:
            for row, txt in self.message_rows:
                is_invalid = len(txt.text().strip()) > 492
                txt.setProperty("state", "error" if is_invalid else "normal")
                txt.style().unpolish(txt)
                txt.style().polish(txt)

class MessageEditorDialog(ModernModal):
    def __init__(self, current_text: str, i18n, parent=None):
        super().__init__(
            title=i18n.get("timer.dialog.editor_title"),
            icon_path=get_assets_path("icons/clock.svg"),
            icon_bg_color=COLOR_GREEN,
            width=500,
            parent=parent
        )
        self.i18n = i18n
        self.set_dialog_state("accent", QColor(46, 205, 112, 60))
        
        self.text_edit = VariableTextEdit()
        self.text_edit.setPlaceholderText(self.i18n.get("timer.dialog.response_placeholder"))
        self.text_edit.setPlainText(current_text)
        self.text_edit.setMinimumHeight(150)
        self.text_edit.setAcceptRichText(False)
        self.content_layout.addWidget(self.text_edit)
        
        btn_cancel = ModernButton(self.i18n.get("common.buttons.cancel"), role="action_outlined")
        btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = ModernButton(self.i18n.get("common.buttons.save"), role="action_accent")
        self.btn_save.clicked.connect(self.accept)
        
        self.add_action_buttons(btn_cancel, self.btn_save)
        
        self.text_edit.textChanged.connect(self._validate_text_length)
        self._validate_text_length()
        
    def _validate_text_length(self):
        text = self.text_edit.toPlainText()
        is_invalid = len(text) > 492
        self.text_edit.setProperty("state", "error" if is_invalid else "normal")
        self.text_edit.style().unpolish(self.text_edit)
        self.text_edit.style().polish(self.text_edit)
        self.btn_save.setEnabled(not is_invalid)
        
    def get_text(self) -> str:
        return self.text_edit.toPlainText().replace("\n", " ").strip()
