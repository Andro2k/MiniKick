# frontend\dialogs\timer_dialog.py

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QSpinBox, QWidget, QScrollArea, QFrame, QCheckBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from .base_dialog import ModernWizardPanel, ModernModal
from frontend.widgets import ModernButton, VariableTextEdit
from frontend.common.theme import COLOR_RED, COLOR_GREEN
from frontend.common.utils import get_icon_colored, NoWheelSlider, get_assets_path

class TimerConfigWizard(ModernWizardPanel):
    def __init__(self, i18n, parent=None, existing_config=None):
        self.i18n = i18n
        title_steps = [self.i18n.get("timer.dialog.title"), self.i18n.get("timer.dialog.title")]
        subtitle_steps = [self.i18n.get("timer.dialog.subtitle"), self.i18n.get("timer.dialog.categories_desc")]
        super().__init__(title_steps=title_steps, subtitle_steps=subtitle_steps, i18n=i18n, width=750, parent=parent)        
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

    def _create_interval_controls(self, layout, min_val: int, max_val: int, default_val: int):
        controls_layout = QHBoxLayout()
        slider = NoWheelSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default_val)
        spin.setFixedWidth(100)
        
        slider.valueChanged.connect(spin.setValue)
        spin.spin.valueChanged.connect(slider.setValue) if hasattr(spin, "spin") else spin.valueChanged.connect(slider.setValue)
        
        controls_layout.addWidget(slider, stretch=1)
        controls_layout.addWidget(spin)
        layout.addLayout(controls_layout)
        return slider, spin

    def _setup_ui(self):
        self.tab_basic = QWidget()
        basic_main_layout = QHBoxLayout(self.tab_basic)
        basic_main_layout.setContentsMargins(0, 0, 0, 0)
        basic_main_layout.setSpacing(20)

        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        lbl_name = QLabel(self.i18n.get("timer.dialog.name_label"))
        lbl_name.setProperty("role", "h3")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText(self.i18n.get("timer.dialog.name_placeholder"))
        self.txt_name.textChanged.connect(self._update_btn_next_state)
        left_layout.addWidget(lbl_name)
        left_layout.addWidget(self.txt_name)

        lbl_response = QLabel(self.i18n.get("timer.dialog.response_label"))
        lbl_response.setProperty("role", "h3")
        left_layout.addWidget(lbl_response)

        self.scroll_messages = QScrollArea()
        self.scroll_messages.setWidgetResizable(True)
        self.scroll_messages.setMinimumHeight(150)
        self.scroll_messages.setFrameShape(QFrame.Shape.NoFrame)
        
        self.scroll_messages_content = QWidget()
        self.messages_layout = QVBoxLayout(self.scroll_messages_content)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        
        self.scroll_messages.setWidget(self.scroll_messages_content)
        left_layout.addWidget(self.scroll_messages)

        self.btn_add_msg = ModernButton(self.i18n.get("timer.dialog.btn_add_message"), role="action_accent_border")
        self.btn_add_msg.clicked.connect(lambda: self._add_message_field())
        left_layout.addWidget(self.btn_add_msg)

        basic_main_layout.addWidget(left_col, stretch=1)

        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)

        self.chk_online = QCheckBox(self.i18n.get("timer.dialog.online_interval_label"))
        self.chk_online.setChecked(True)
        right_layout.addWidget(self.chk_online)
        self.slider_online, self.spin_online = self._create_interval_controls(right_layout, 1, 120, 5)
        self.chk_online.toggled.connect(self.slider_online.setEnabled)
        self.chk_online.toggled.connect(self.spin_online.setEnabled)
        self.chk_online.toggled.connect(self._update_btn_next_state)

        self.chk_offline = QCheckBox(self.i18n.get("timer.dialog.offline_interval_label"))
        self.chk_offline.setChecked(True)
        right_layout.addWidget(self.chk_offline)
        self.slider_offline, self.spin_offline = self._create_interval_controls(right_layout, 1, 480, 30)
        self.chk_offline.toggled.connect(self.slider_offline.setEnabled)
        self.chk_offline.toggled.connect(self.spin_offline.setEnabled)
        self.chk_offline.toggled.connect(self._update_btn_next_state)

        self.chk_lines = QCheckBox(self.i18n.get("timer.dialog.chat_lines_label"))
        self.chk_lines.setChecked(True)
        right_layout.addWidget(self.chk_lines)
        self.slider_lines, self.spin_lines = self._create_interval_controls(right_layout, 0, 100, 5)
        self.chk_lines.toggled.connect(self.slider_lines.setEnabled)
        self.chk_lines.toggled.connect(self.spin_lines.setEnabled)
        
        lbl_lines_desc = QLabel(self.i18n.get("timer.dialog.chat_lines_desc"))
        lbl_lines_desc.setProperty("role", "caption")
        lbl_lines_desc.setWordWrap(True)
        right_layout.addWidget(lbl_lines_desc)

        right_layout.addStretch()
        basic_main_layout.addWidget(right_col, stretch=1)

        self.tab_filters = QWidget()
        filters_main_layout = QHBoxLayout(self.tab_filters)
        filters_main_layout.setContentsMargins(0, 0, 0, 0)
        filters_main_layout.setSpacing(20)

        left_filt_col = QWidget()
        left_filt_layout = QVBoxLayout(left_filt_col)
        left_filt_layout.setContentsMargins(0, 0, 0, 0)
        left_filt_layout.setSpacing(12)

        lbl_keywords = QLabel(self.i18n.get("timer.dialog.keywords_label"))
        lbl_keywords.setProperty("role", "h3")
        self.txt_keywords = QLineEdit()
        self.txt_keywords.setPlaceholderText(self.i18n.get("timer.dialog.keywords_placeholder"))
        left_filt_layout.addWidget(lbl_keywords)
        left_filt_layout.addWidget(self.txt_keywords)
        
        lbl_keywords_desc = QLabel(self.i18n.get("timer.dialog.keywords_desc"))
        lbl_keywords_desc.setProperty("role", "caption")
        lbl_keywords_desc.setWordWrap(True)
        left_filt_layout.addWidget(lbl_keywords_desc)

        lbl_categories = QLabel(self.i18n.get("timer.dialog.categories_label"))
        lbl_categories.setProperty("role", "h3")
        self.txt_categories = QLineEdit()
        self.txt_categories.setPlaceholderText(self.i18n.get("timer.dialog.categories_placeholder"))
        left_filt_layout.addWidget(lbl_categories)
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
        right_filt_layout.setContentsMargins(12, 12, 12, 12)
        
        lbl_help_title = QLabel(self.i18n.get("timer.dialog.title"))
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
        btn_edit.setFixedSize(26, 26)
        btn_edit.setIcon(self._icon_edit)
        btn_edit.setIconSize(QSize(14, 14))
        btn_edit.clicked.connect(lambda checked=False, line_edit=txt: self._open_message_editor(line_edit))
        row_layout.addWidget(btn_edit)
        
        btn_del = ModernButton("", role="action_danger_border")
        btn_del.setFixedSize(26, 26)
        btn_del.setIcon(self._icon_trash)
        btn_del.setIconSize(QSize(14, 14))
        btn_del.clicked.connect(lambda: self._remove_message_row(row))
        row_layout.addWidget(btn_del)
        
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, row)
        self.message_rows.append((row, txt))

    def _remove_message_row(self, row_widget):
        if len(self.message_rows) <= 1:
            return
        for item in list(self.message_rows):
            if item[0] == row_widget:
                self.message_rows.remove(item)
                self.messages_layout.removeWidget(row_widget)
                row_widget.deleteLater()
                break
        self._update_btn_next_state()

    def _open_message_editor(self, line_edit: QLineEdit):
        dialog = MessageEditorDialog(line_edit.text(), self.i18n, parent=self)
        if dialog.exec():
            line_edit.setText(dialog.get_text())

    def validate_step(self, step_index: int) -> bool:
        if step_index == 0:
            if not self.txt_name.text().strip():
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
            self.slider_online.setValue(online_min)
            self.spin_online.setValue(online_min)
        else:
            self.slider_online.setEnabled(False)
            self.spin_online.setEnabled(False)

        offline_min = self.existing_config.get("interval_offline")
        has_offline = offline_min is not None and offline_min > 0
        self.chk_offline.setChecked(has_offline)
        if has_offline:
            self.slider_offline.setValue(offline_min)
            self.spin_offline.setValue(offline_min)
        else:
            self.slider_offline.setEnabled(False)
            self.spin_offline.setEnabled(False)

        lines = self.existing_config.get("chat_lines", 0)
        has_lines = lines is not None and lines > 0
        self.chk_lines.setChecked(has_lines)
        if has_lines:
            self.slider_lines.setValue(lines)
            self.spin_lines.setValue(lines)
        else:
            self.slider_lines.setEnabled(False)
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
            "categories": categories
        }

    def _update_step_ui(self):
        super()._update_step_ui()
        self._update_btn_next_state()

    def _update_btn_next_state(self):
        self.btn_next.setEnabled(self.validate_step(self.current_step))
        if self.current_step == 0:
            for row, txt in self.message_rows:
                if len(txt.text().strip()) > 492:
                    txt.setStyleSheet("border: 1.5px solid #EF4444;")
                else:
                    txt.setStyleSheet("")


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
        self.text_edit.setPlaceholderText(self.i18n.get("timer.dialog.response_placeholder") or "Escribe tu mensaje aquí...")
        self.text_edit.setPlainText(current_text)
        self.text_edit.setMinimumHeight(150)
        self.text_edit.setAcceptRichText(False)
        self.content_layout.addWidget(self.text_edit)
        
        btn_cancel = ModernButton(self.i18n.get("common.buttons.cancel") or "Cancelar", role="action_outlined")
        btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = ModernButton(self.i18n.get("common.buttons.save") or "Guardar", role="action_accent")
        self.btn_save.clicked.connect(self.accept)
        
        self.add_action_buttons(btn_cancel, self.btn_save)
        
        self.text_edit.textChanged.connect(self._validate_text_length)
        self._validate_text_length()
        
    def _validate_text_length(self):
        text = self.text_edit.toPlainText()
        if len(text) > 492:
            self.text_edit.setStyleSheet("border: 1.5px solid #EF4444;")
            self.btn_save.setEnabled(False)
        else:
            self.text_edit.setStyleSheet("")
            self.btn_save.setEnabled(True)
        
    def get_text(self) -> str:
        return self.text_edit.toPlainText().replace("\n", " ").strip()
