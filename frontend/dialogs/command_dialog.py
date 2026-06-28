# frontend\dialogs\command_dialogs.py

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QTextEdit, QSpinBox, QCheckBox,
                               QWidget, QSizePolicy, QComboBox)
from frontend.dialogs.base_dialog import ModernWizardPanel

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
            width=520,
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
        basic_layout.addWidget(lbl_trigger)
        basic_layout.addWidget(self.txt_trigger)

        lbl_response = QLabel(self.i18n.get("command.dialog.response_label"))
        lbl_response.setProperty("role", "h3")
        self.txt_response = QTextEdit()
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
        self.combo_perm = QComboBox()
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
        adv_layout = QVBoxLayout(self.tab_adv)
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
        self.txt_regex = QLineEdit()
        self.txt_regex.setPlaceholderText(self.i18n.get("command.dialog.regex_placeholder"))
        self.txt_regex.setEnabled(False)
        
        adv_layout.addWidget(lbl_regex)
        adv_layout.addWidget(self.txt_regex)
        
        lbl_regex_help = QLabel(self.i18n.get("command.dialog.regex_help"))
        lbl_regex_help.setWordWrap(True)
        lbl_regex_help.setProperty("role", "caption")
        adv_layout.addWidget(lbl_regex_help)
        
        adv_layout.addStretch()

        self.add_page(self.tab_basic)
        self.add_page(self.tab_adv)

    def _on_regex_toggled(self, checked):
        self.txt_regex.setEnabled(checked)
        self.txt_aliases.setEnabled(not checked)

    def validate_step(self, step_index: int) -> bool:
        if step_index == 0:
            if not self.txt_trigger.text().strip():
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
        aliases_val = self.txt_regex.text().strip() if is_regex else self.txt_aliases.text().strip()
        
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