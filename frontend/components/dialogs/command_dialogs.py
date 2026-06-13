# frontend/components/dialogs/command_dialogs.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QTextEdit, QSpinBox, QCheckBox, 
                               QTabWidget, QWidget, QSizePolicy)
from frontend.components.controls import ModernButton

class CommandConfigWizard(QDialog):
    """Diálogo con pestañas para configurar comandos básicos o RegEx avanzado."""
    def __init__(self, parent=None, existing_config=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Comando de Chat")
        self.setMinimumWidth(500)
        self.setObjectName("SquareDialog")
        
        self.existing_config = existing_config
        self.original_trigger = existing_config.get("trigger", "") if existing_config else None
        
        self._setup_ui()
        if self.existing_config:
            self._load_existing()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        self.tabs = QTabWidget()
        
        self.tab_basic = QWidget()
        basic_layout = QVBoxLayout(self.tab_basic)
        basic_layout.setSpacing(12)

        lbl_trigger = QLabel("Nombre del Comando (Ej: !discord):")
        lbl_trigger.setProperty("role", "section_small")
        self.txt_trigger = QLineEdit()
        basic_layout.addWidget(lbl_trigger)
        basic_layout.addWidget(self.txt_trigger)

        lbl_response = QLabel("Respuesta del bot (puedes usar {user}):")
        lbl_response.setProperty("role", "section_small")
        self.txt_response = QTextEdit()
        
        self.txt_response.setMinimumHeight(80) 
        self.txt_response.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        basic_layout.addWidget(lbl_response)
        basic_layout.addWidget(self.txt_response)

        row_configs = QHBoxLayout()
        col_cooldown = QVBoxLayout()
        col_cooldown.addWidget(QLabel("Cooldown (seg):"))
        self.spin_cooldown = QSpinBox()
        self.spin_cooldown.setRange(0, 300)
        self.spin_cooldown.setValue(5)
        col_cooldown.addWidget(self.spin_cooldown)
        row_configs.addLayout(col_cooldown)

        self.col_aliases = QVBoxLayout()
        self.col_aliases.addWidget(QLabel("Aliases (separados por coma):"))
        self.txt_aliases = QLineEdit()
        self.txt_aliases.setPlaceholderText("!dc, !discordia")
        self.col_aliases.addWidget(self.txt_aliases)
        row_configs.addLayout(self.col_aliases, stretch=1)
        
        basic_layout.addLayout(row_configs)

        self.chk_active = QCheckBox("Comando Activo")
        self.chk_active.setChecked(True)
        basic_layout.addWidget(self.chk_active)
        
        self.tab_adv = QWidget()
        adv_layout = QVBoxLayout(self.tab_adv)
        adv_layout.setSpacing(12)

        self.chk_regex = QCheckBox("Usar RegEx (Ignora Prefijos y Aliases)")
        self.chk_regex.toggled.connect(self._on_regex_toggled)
        adv_layout.addWidget(self.chk_regex)

        lbl_regex = QLabel("Sintaxis de Expresión Regular:")
        lbl_regex.setProperty("role", "section_small")
        self.txt_regex = QLineEdit()
        self.txt_regex.setPlaceholderText("Ej: \\b(hola|buenas)\\b")
        self.txt_regex.setEnabled(False)
        
        adv_layout.addWidget(lbl_regex)
        adv_layout.addWidget(self.txt_regex)
        
        lbl_regex_help = QLabel("Si activas RegEx, el bot buscará este patrón en todo el mensaje. Usa el 'Nombre del Comando' en la pestaña básica solo como un identificador visual.")
        lbl_regex_help.setWordWrap(True)
        lbl_regex_help.setStyleSheet("color: #94A3B8; font-style: italic;")
        adv_layout.addWidget(lbl_regex_help)
        
        adv_layout.addStretch()

        self.tabs.addTab(self.tab_basic, "Básico")
        self.tabs.addTab(self.tab_adv, "Avanzado")
        main_layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        btn_cancel = ModernButton("Cancelar", role="action_outlined")
        btn_cancel.clicked.connect(self.reject)
        self.btn_save = ModernButton("Guardar Comando", role="action_accent")
        self.btn_save.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_save)
        main_layout.addLayout(btn_layout)

    def _on_regex_toggled(self, checked):
        self.txt_regex.setEnabled(checked)
        self.txt_aliases.setEnabled(not checked)

    def _load_existing(self):
        self.txt_trigger.setText(self.existing_config.get("trigger", ""))
        self.txt_response.setText(self.existing_config.get("response", ""))
        self.spin_cooldown.setValue(self.existing_config.get("cooldown", 5))
        self.chk_active.setChecked(self.existing_config.get("is_active", True))
        
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
            "is_active": self.chk_active.isChecked()
        }