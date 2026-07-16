# frontend\dialogs\command_dialogs.py

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QTextEdit, QSpinBox, QCheckBox,
                               QWidget, QSizePolicy, QScrollArea, QFrame)
from PySide6.QtCore import Qt, QSize
from .base_dialog import ModernWizardPanel
from frontend.widgets import ModernButton
from frontend.common.theme import COLOR_WHITE
from frontend.common.utils import get_icon_colored, NoWheelComboBox, validate_trigger_prefix

class CommandConfigWizard(ModernWizardPanel):
    def __init__(self, i18n, parent=None, existing_config=None):
        self.i18n = i18n
        title_steps = [
            self.i18n.get("command.dialog.title"),
            self.i18n.get("command.dialog.tab_advanced")
        ]
        subtitle_steps = [
            self.i18n.get("command.dialog.subtitle"),
            self.i18n.get("command.dialog.regex_help")
        ]
        super().__init__(
            title_steps=title_steps,
            subtitle_steps=subtitle_steps,
            i18n=i18n,
            width=700,
            parent=parent
        )
        
        self.existing_config = existing_config
        self.original_trigger = existing_config.get("trigger", "") if existing_config else None
        
        self._setup_ui()
        if self.existing_config:
            self._load_existing()
            
        self.start_wizard()

    def _setup_ui(self):
        self.tab_basic = QWidget()
        basic_layout = QVBoxLayout(self.tab_basic)
        basic_layout.setSpacing(12)

        lbl_trigger = QLabel(self.i18n.get("command.dialog.trigger_label"))
        lbl_trigger.setProperty("role", "h3")
        self.txt_trigger = QLineEdit()
        self.txt_trigger.textChanged.connect(self._validate_trigger_prefix)
        self.txt_trigger.textChanged.connect(self._update_btn_next_state)
        basic_layout.addWidget(lbl_trigger)
        basic_layout.addWidget(self.txt_trigger)

        lbl_response = QLabel(self.i18n.get("command.dialog.response_label"))
        lbl_response.setProperty("role", "h3")
        self.txt_response = QTextEdit()
        self.txt_response.textChanged.connect(self._update_btn_next_state)
        self.txt_response.setMinimumHeight(80) 
        self.txt_response.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        basic_layout.addWidget(lbl_response)
        basic_layout.addWidget(self.txt_response)

        row_configs = QHBoxLayout()
        col_cooldown = QVBoxLayout()
        col_cooldown.addWidget(QLabel(self.i18n.get("command.dialog.cooldown_label")))
        self.spin_cooldown = QSpinBox()
        self.spin_cooldown.setRange(0, 300)
        self.spin_cooldown.setValue(5)
        col_cooldown.addWidget(self.spin_cooldown)
        row_configs.addLayout(col_cooldown)
        
        col_perm = QVBoxLayout()
        col_perm.addWidget(QLabel(self.i18n.get("command.dialog.permission_label")))
        self.combo_perm = NoWheelComboBox()
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_everyone"), "everyone")
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_subscriber"), "subscriber")
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_vip"), "vip")
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_moderator"), "moderator")
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_broadcaster"), "broadcaster")
        col_perm.addWidget(self.combo_perm)
        row_configs.addLayout(col_perm)
        
        basic_layout.addLayout(row_configs)

        self.chk_active = QCheckBox(self.i18n.get("command.dialog.active_checkbox"))
        self.chk_active.setChecked(True)
        basic_layout.addWidget(self.chk_active)

        self.tab_adv = QWidget()
        adv_main_layout = QHBoxLayout(self.tab_adv)
        adv_main_layout.setContentsMargins(0, 0, 0, 0)
        adv_main_layout.setSpacing(12)

        left_col = QWidget()
        adv_layout = QVBoxLayout(left_col)
        adv_layout.setContentsMargins(0, 0, 0, 0)
        adv_layout.setSpacing(12)

        lbl_aliases = QLabel(self.i18n.get("command.dialog.aliases_label"))
        lbl_aliases.setProperty("role", "h3")
        self.txt_aliases = QLineEdit()
        self.txt_aliases.setPlaceholderText(self.i18n.get("command.dialog.aliases_placeholder"))
        adv_layout.addWidget(lbl_aliases)
        adv_layout.addWidget(self.txt_aliases)

        adv_layout.addSpacing(10)

        self.chk_regex = QCheckBox(self.i18n.get("command.dialog.regex_checkbox"))
        self.chk_regex.toggled.connect(self._on_regex_toggled)
        adv_layout.addWidget(self.chk_regex)

        lbl_regex = QLabel(self.i18n.get("command.dialog.regex_label"))
        lbl_regex.setProperty("role", "h3")
        self.txt_regex = QTextEdit()
        self.txt_regex.setPlaceholderText(self.i18n.get("command.dialog.regex_placeholder"))
        self.txt_regex.setMinimumHeight(60)
        self.txt_regex.setEnabled(False)
        
        adv_layout.addWidget(lbl_regex)
        adv_layout.addWidget(self.txt_regex)
        
        lbl_regex_help = QLabel(self.i18n.get("command.dialog.regex_help"))
        lbl_regex_help.setWordWrap(True)
        lbl_regex_help.setProperty("role", "caption")
        adv_layout.addWidget(lbl_regex_help)
        
        adv_layout.addStretch()

        adv_main_layout.addWidget(left_col, stretch=1)
        
        right_col = self._build_regex_helper()
        adv_main_layout.addWidget(right_col)

        self.add_page(self.tab_basic)
        self.add_page(self.tab_adv)

    def _on_regex_toggled(self, checked):
        self.txt_regex.setEnabled(checked)
        self.txt_aliases.setEnabled(not checked)

    def validate_step(self, step_index: int) -> bool:
        if step_index == 0:
            trigger_text = self.txt_trigger.text().strip()
            response_text = self.txt_response.toPlainText().strip()
            if not trigger_text.startswith("!") or not response_text:
                return False
        return True

    def _load_existing(self):
        self.txt_trigger.setText(self.existing_config.get("trigger", ""))
        self.txt_response.setText(self.existing_config.get("response", ""))
        self.spin_cooldown.setValue(self.existing_config.get("cooldown", 5))
        self.chk_active.setChecked(self.existing_config.get("is_active", True))
        
        permission = self.existing_config.get("permission", "everyone")
        index = self.combo_perm.findData(permission)
        if index >= 0:
            self.combo_perm.setCurrentIndex(index)
        
        is_regex = self.existing_config.get("is_regex", False)
        self.chk_regex.setChecked(is_regex)
        
        if is_regex:
            self.txt_regex.setText(self.existing_config.get("aliases", ""))
        else:
            self.txt_aliases.setText(self.existing_config.get("aliases", ""))

    def get_command_data(self):
        is_regex = self.chk_regex.isChecked()
        aliases_val = self.txt_regex.toPlainText().strip() if is_regex else self.txt_aliases.text().strip()
        
        return {
            "original_trigger": self.original_trigger,
            "trigger": self.txt_trigger.text().strip(),
            "response": self.txt_response.toPlainText().strip(),
            "cooldown": self.spin_cooldown.value(),
            "aliases": aliases_val,
            "is_regex": is_regex,
            "is_active": self.chk_active.isChecked(),
            "permission": self.combo_perm.currentData()
        }

    def _build_regex_helper(self) -> QWidget:
        right_panel = QFrame()
        right_panel.setProperty("role", "card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 0, 10)
        right_layout.setSpacing(6)
        
        lbl_sheet_title = QLabel(self.i18n.get("command.dialog.regex_helper_title"))
        lbl_sheet_title.setProperty("role", "h3")
        right_layout.addWidget(lbl_sheet_title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 10, 0)
        scroll_layout.setSpacing(0)
        
        def add_category(title):
            lbl = QLabel(title)
            lbl.setProperty("role", "category")
            scroll_layout.addWidget(lbl)
            
        add_category(self.i18n.get("command.dialog.regex_helper_cat_syntax"))
        scroll_layout.addWidget(self._create_cheat_row(".", self.i18n.get("command.dialog.regex_helper_desc_any"), "."))
        scroll_layout.addWidget(self._create_cheat_row("\\w", self.i18n.get("command.dialog.regex_helper_desc_word"), "\\w"))
        scroll_layout.addWidget(self._create_cheat_row("\\d", self.i18n.get("command.dialog.regex_helper_desc_digit"), "\\d"))
        scroll_layout.addWidget(self._create_cheat_row("\\s", self.i18n.get("command.dialog.regex_helper_desc_space"), "\\s"))
        scroll_layout.addWidget(self._create_cheat_row("\\b", self.i18n.get("command.dialog.regex_helper_desc_boundary"), "\\b"))
        
        add_category(self.i18n.get("command.dialog.regex_helper_cat_quantifiers"))
        scroll_layout.addWidget(self._create_cheat_row("*", self.i18n.get("command.dialog.regex_helper_desc_zero_more"), "*"))
        scroll_layout.addWidget(self._create_cheat_row("+", self.i18n.get("command.dialog.regex_helper_desc_one_more"), "+"))
        scroll_layout.addWidget(self._create_cheat_row("?", self.i18n.get("command.dialog.regex_helper_desc_optional"), "?"))
        scroll_layout.addWidget(self._create_cheat_row("{3}", self.i18n.get("command.dialog.regex_helper_desc_exact"), "{3}"))
        scroll_layout.addWidget(self._create_cheat_row("{3,}", self.i18n.get("command.dialog.regex_helper_desc_more"), "{3,}"))
        scroll_layout.addWidget(self._create_cheat_row("{3,5}", self.i18n.get("command.dialog.regex_helper_desc_range"), "{3,5}"))
        
        add_category(self.i18n.get("command.dialog.regex_helper_cat_anchors"))
        scroll_layout.addWidget(self._create_cheat_row("^", self.i18n.get("command.dialog.regex_helper_desc_start"), "^"))
        scroll_layout.addWidget(self._create_cheat_row("$", self.i18n.get("command.dialog.regex_helper_desc_end"), "$"))
        scroll_layout.addWidget(self._create_cheat_row("a|b", self.i18n.get("command.dialog.regex_helper_desc_alt"), "a|b"))
        scroll_layout.addWidget(self._create_cheat_row("( )", self.i18n.get("command.dialog.regex_helper_desc_capture"), "(abc)"))
        scroll_layout.addWidget(self._create_cheat_row("(?: )", self.i18n.get("command.dialog.regex_helper_desc_noncapture"), "(?:abc)"))

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)
        
        return right_panel

    def _create_cheat_row(self, label_text: str, desc_text: str, insert_val: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(6)
        
        lbl_code = QLabel(label_text)
        lbl_code.setProperty("role", "code")
        
        lbl_desc = QLabel(desc_text)
        lbl_desc.setProperty("role", "monospace")
        lbl_desc.setWordWrap(True)
        
        btn_insert = ModernButton("", role="action_outlined")
        btn_insert.setIcon(get_icon_colored("add.svg", COLOR_WHITE, size=12))
        btn_insert.setIconSize(QSize(12, 12))
        btn_insert.setFixedSize(20, 20)
        btn_insert.clicked.connect(lambda checked=False, val=insert_val: self._insert_regex(val))
        
        layout.addWidget(lbl_code)
        layout.addWidget(lbl_desc, stretch=1)
        layout.addWidget(btn_insert)
        return row

    def _insert_regex(self, text_to_insert: str):
        if not self.chk_regex.isChecked():
            self.chk_regex.setChecked(True)
        self.txt_regex.insertPlainText(text_to_insert)
        self.txt_regex.setFocus()

    def _validate_trigger_prefix(self, text: str):
        if validate_trigger_prefix(text):
            self.txt_trigger.setStyleSheet("")
        else:
            self.txt_trigger.setStyleSheet("border: 1.5px solid #ff4444;")

    def _update_step_ui(self):
        super()._update_step_ui()
        self._update_btn_next_state()

    def _update_btn_next_state(self):
        if self.current_step == 0:
            trigger_text = self.txt_trigger.text().strip()
            response_text = self.txt_response.toPlainText().strip()
            is_valid = bool(trigger_text.startswith("!") and response_text)
            self.btn_next.setEnabled(is_valid)
        else:
            self.btn_next.setEnabled(True)
