# frontend/dialogs/timer_dialog.py

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QSpinBox, QSlider, QWidget, QScrollArea, QFrame, QCheckBox)
from PySide6.QtCore import Qt
from frontend.dialogs.base_dialog import ModernWizardPanel
from frontend.widgets.controls_component import ModernButton
from frontend.common.theme import COLOR_DANGER
from frontend.common.utils import get_icon_colored

class TimerConfigWizard(ModernWizardPanel):
    def __init__(self, i18n, parent=None, existing_config=None):
        self.i18n = i18n
        title_steps = [
            self.i18n.get("timer.dialog.title"),
            self.i18n.get("timer.dialog.title")
        ]
        subtitle_steps = [
            self.i18n.get("timer.dialog.subtitle"),
            self.i18n.get("timer.dialog.categories_desc")
        ]
        super().__init__(
            title_steps=title_steps,
            subtitle_steps=subtitle_steps,
            i18n=i18n,
            width=750,
            parent=parent
        )
        
        self.existing_config = existing_config
        self.timer_id = existing_config.get("id") if existing_config else None
        self.message_rows = []
        
        self._setup_ui()
        if self.existing_config:
            self._load_existing()
        else:
            self._add_message_field()
            
        self.start_wizard()

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
        self.chk_online.toggled.connect(self._on_online_toggled)
        
        online_controls = QHBoxLayout()
        self.slider_online = QSlider(Qt.Orientation.Horizontal)
        self.slider_online.setRange(1, 120)
        self.slider_online.setValue(5)
        self.spin_online = QSpinBox()
        self.spin_online.setRange(1, 120)
        self.spin_online.setValue(5)
        
        self.slider_online.valueChanged.connect(self.spin_online.setValue)
        self.spin_online.valueChanged.connect(self.slider_online.setValue)
        
        online_controls.addWidget(self.slider_online, stretch=1)
        online_controls.addWidget(self.spin_online)

        right_layout.addWidget(self.chk_online)
        right_layout.addLayout(online_controls)

        self.chk_offline = QCheckBox(self.i18n.get("timer.dialog.offline_interval_label"))
        self.chk_offline.setChecked(True)
        self.chk_offline.toggled.connect(self._on_offline_toggled)
        
        offline_controls = QHBoxLayout()
        self.slider_offline = QSlider(Qt.Orientation.Horizontal)
        self.slider_offline.setRange(1, 480)
        self.slider_offline.setValue(30)
        self.spin_offline = QSpinBox()
        self.spin_offline.setRange(1, 480)
        self.spin_offline.setValue(30)
        
        self.slider_offline.valueChanged.connect(self.spin_offline.setValue)
        self.spin_offline.valueChanged.connect(self.slider_offline.setValue)
        
        offline_controls.addWidget(self.slider_offline, stretch=1)
        offline_controls.addWidget(self.spin_offline)

        right_layout.addWidget(self.chk_offline)
        right_layout.addLayout(offline_controls)

        self.chk_lines = QCheckBox(self.i18n.get("timer.dialog.chat_lines_label"))
        self.chk_lines.setChecked(True)
        self.chk_lines.toggled.connect(self._on_lines_toggled)
        
        lines_controls = QHBoxLayout()
        self.slider_lines = QSlider(Qt.Orientation.Horizontal)
        self.slider_lines.setRange(0, 100)
        self.slider_lines.setValue(5)
        self.spin_lines = QSpinBox()
        self.spin_lines.setRange(0, 100)
        self.spin_lines.setValue(5)
        
        self.slider_lines.valueChanged.connect(self.spin_lines.setValue)
        self.spin_lines.valueChanged.connect(self.slider_lines.setValue)
        
        lines_controls.addWidget(self.slider_lines, stretch=1)
        lines_controls.addWidget(self.spin_lines)

        right_layout.addWidget(self.chk_lines)
        right_layout.addLayout(lines_controls)
        
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
        row_layout.addWidget(txt)
        
        btn_del = ModernButton("", role="action_danger_border")
        btn_del.setFixedSize(26, 26)
        btn_del.setIcon(get_icon_colored("trash.svg", COLOR_DANGER, 14))
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

    def _on_online_toggled(self, checked):
        self.slider_online.setEnabled(checked)
        self.spin_online.setEnabled(checked)

    def _on_offline_toggled(self, checked):
        self.slider_offline.setEnabled(checked)
        self.spin_offline.setEnabled(checked)

    def _on_lines_toggled(self, checked):
        self.slider_lines.setEnabled(checked)
        self.spin_lines.setEnabled(checked)

    def validate_step(self, step_index: int) -> bool:
        if step_index == 0:
            if not self.txt_name.text().strip():
                return False
            messages = [txt.text().strip() for row, txt in self.message_rows if txt.text().strip()]
            if not messages:
                return False
            if not self.chk_online.isChecked() and not self.chk_offline.isChecked():
                return False
        return True

    def _load_existing(self):
        self.txt_name.setText(self.existing_config.get("name", ""))
        
        messages = self.existing_config.get("messages", [])
        for m in messages:
            self._add_message_field(m)
            
        online_min = self.existing_config.get("interval_online")
        if online_min is not None and online_min > 0:
            self.chk_online.setChecked(True)
            self.slider_online.setValue(online_min)
            self.spin_online.setValue(online_min)
        else:
            self.chk_online.setChecked(False)
            self._on_online_toggled(False)

        offline_min = self.existing_config.get("interval_offline")
        if offline_min is not None and offline_min > 0:
            self.chk_offline.setChecked(True)
            self.slider_offline.setValue(offline_min)
            self.spin_offline.setValue(offline_min)
        else:
            self.chk_offline.setChecked(False)
            self._on_offline_toggled(False)

        lines = self.existing_config.get("chat_lines", 0)
        if lines is not None and lines > 0:
            self.chk_lines.setChecked(True)
            self.slider_lines.setValue(lines)
            self.spin_lines.setValue(lines)
        else:
            self.chk_lines.setChecked(False)
            self._on_lines_toggled(False)

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
