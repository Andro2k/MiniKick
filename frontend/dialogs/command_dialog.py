# frontend\dialogs\command_dialog.py

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QWidget, QSizePolicy
from .base_dialog import ModernWizardPanel
from frontend.widgets import VariableTextEdit, NoWheelComboBox, NoWheelSpinBox, create_badge
from frontend.common import validate_trigger_prefix

class CommandConfigWizard(ModernWizardPanel):
    def __init__(self, i18n, parent=None, existing_config=None):
        self.i18n = i18n
        title_steps = [self.i18n.get("command.dialog.title"), self.i18n.get("command.dialog.tab_advanced")]
        subtitle_steps = [self.i18n.get("command.dialog.subtitle"), self.i18n.get("command.dialog.regex_help")]       
        super().__init__(title_steps=title_steps, subtitle_steps=subtitle_steps, i18n=i18n, width=520, parent=parent)       
        self.existing_config = existing_config
        self.original_trigger = existing_config.get("trigger", "") if existing_config else None       
        self._setup_ui()
        if self.existing_config:
            self._load_existing()           
        self.start_wizard()

    def _setup_ui(self):
        self.tab_basic = QWidget()
        basic_layout = QVBoxLayout(self.tab_basic)
        basic_layout.setContentsMargins(0, 0, 0, 0)
        basic_layout.setSpacing(10)

        lbl_trigger = QLabel(self.i18n.get("command.dialog.trigger_label"))
        lbl_trigger.setProperty("role", "h3")
        self.txt_trigger = QLineEdit()
        self.txt_trigger.textChanged.connect(self._validate_trigger_prefix)
        self.txt_trigger.textChanged.connect(self._update_btn_next_state)
        basic_layout.addWidget(lbl_trigger)
        basic_layout.addWidget(self.txt_trigger)

        lbl_response_layout = QHBoxLayout()
        lbl_response = QLabel(self.i18n.get("command.dialog.response_label"))
        lbl_response.setProperty("role", "h3")
        
        self.badge_plugin = create_badge(self.i18n.get("command.dialog.plugin_tag"), state="plugin")
        self.badge_plugin.setVisible(False)
        
        lbl_response_layout.addWidget(lbl_response)
        lbl_response_layout.addSpacing(6)
        lbl_response_layout.addWidget(self.badge_plugin)
        lbl_response_layout.addStretch()

        self.txt_response = VariableTextEdit()
        self.txt_response.textChanged.connect(self._update_btn_next_state)
        self.txt_response.setMinimumHeight(90) 
        self.txt_response.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        basic_layout.addLayout(lbl_response_layout)
        basic_layout.addWidget(self.txt_response)

        row_configs = QHBoxLayout()
        row_configs.setSpacing(12)

        col_cooldown = QVBoxLayout()
        col_cooldown.setSpacing(4)
        lbl_cooldown = QLabel(self.i18n.get("command.dialog.cooldown_label"))
        lbl_cooldown.setProperty("role", "h3")
        col_cooldown.addWidget(lbl_cooldown)

        self.spin_cooldown = NoWheelSpinBox()
        self.spin_cooldown.setRange(0, 300)
        self.spin_cooldown.setValue(5)
        self.spin_cooldown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        col_cooldown.addWidget(self.spin_cooldown)
        row_configs.addLayout(col_cooldown, stretch=1)
        
        col_perm = QVBoxLayout()
        col_perm.setSpacing(4)
        lbl_perm = QLabel(self.i18n.get("command.dialog.permission_label"))
        lbl_perm.setProperty("role", "h3")
        col_perm.addWidget(lbl_perm)

        self.combo_perm = NoWheelComboBox()
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_everyone"), "everyone")
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_subscriber"), "subscriber")
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_vip"), "vip")
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_moderator"), "moderator")
        self.combo_perm.addItem(self.i18n.get("command.dialog.perm_broadcaster"), "broadcaster")
        self.combo_perm.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        col_perm.addWidget(self.combo_perm)
        row_configs.addLayout(col_perm, stretch=1)
        
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
        self.txt_regex = VariableTextEdit(
            autocomplete_data={"\\": [
                "\\w (Letras/Dígitos)", "\\d (Dígitos)", "\\s (Espacios)", "\\b (Límite de palabra)", 
                ".* (Cualquier texto)", ".+ (Texto no vacío)", "^ (Inicio de texto)", "$ (Fin de texto)",
                "[a-z] (Letras minúsculas)", "[0-9] (Dígitos)", "a|b (Opción A o B)",
                "(?:...) (Grupo sin captura)", "(?=...) (Lookahead positivo)", "(?!...) (Lookahead negativo)"
            ]},
            highlight_pattern=r"\\.|\[\^?[^\]]+\]|\(\?[^)]+\)|[*+?^$|]|\(|\)",
            highlight_color="#F59E0B",
            highlight_bg=None
        )
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



    def _validate_trigger_prefix(self, text: str):
        is_valid = validate_trigger_prefix(text)
        self.txt_trigger.setProperty("state", "normal" if is_valid else "error")
        self.txt_trigger.style().unpolish(self.txt_trigger)
        self.txt_trigger.style().polish(self.txt_trigger)

    def _update_step_ui(self):
        super()._update_step_ui()
        self._update_btn_next_state()

    def _update_btn_next_state(self):
        if self.current_step == 0:
            trigger_text = self.txt_trigger.text().strip()
            response_text = self.txt_response.toPlainText().strip()
            is_plugin = "[PLUGIN_" in response_text
            
            if hasattr(self, "badge_plugin"):
                self.badge_plugin.setVisible(is_plugin)
            self.txt_response.setReadOnly(is_plugin)
            
            if is_plugin:
                self.txt_response.setProperty("state", "plugin")
                is_valid = bool(trigger_text.startswith("!") and response_text)
            else:
                is_over_limit = len(response_text) > 492
                self.txt_response.setProperty("state", "error" if is_over_limit else "normal")
                is_valid = not is_over_limit and bool(trigger_text.startswith("!") and response_text)
                
            self.txt_response.style().unpolish(self.txt_response)
            self.txt_response.style().polish(self.txt_response)
            self.btn_next.setEnabled(is_valid)
        else:
            self.btn_next.setEnabled(True)
