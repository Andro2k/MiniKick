# frontend/views/settings.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        
        title = QLabel("Configuración")
        title.setProperty("role", "title")
        layout.addWidget(title)
        
        desc = QLabel("Sección en construcción...")
        desc.setProperty("role", "subtitle")
        layout.addWidget(desc)
        
        layout.addStretch()