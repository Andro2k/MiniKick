# frontend/components/dialogs/update_dialog.py

from PySide6.QtWidgets import QLabel, QHBoxLayout, QProgressBar, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, Signal

from frontend.components.dialogs.base_dialogs import ModernBaseDialog
from frontend.theme import COLOR_ACCENT, PATH_ICON_UPDATE

class UpdateDialog(ModernBaseDialog):
    """Diálogo para buscar, mostrar progreso y descargar actualizaciones de MiniKick."""
    download_requested = Signal() 

    def __init__(self, parent=None):
        super().__init__(title="Buscando Actualizaciones", icon_path=PATH_ICON_UPDATE, icon_bg_color=COLOR_ACCENT, width=420, parent=parent)
        
        self.status_label = QLabel("Conectando con el servidor...")
        self.status_label.setProperty("role", "status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.content_layout.addWidget(self.status_label)

        pb_layout = QHBoxLayout()
        pb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(280)
        sp = self.progress_bar.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.progress_bar.setSizePolicy(sp)
        
        pb_layout.addWidget(self.progress_bar)
        self.content_layout.addSpacing(10)
        self.content_layout.addLayout(pb_layout)

        self.action_button = QPushButton("Descargar e Instalar")
        self.action_button.setProperty("role", "action_accent")
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.setMinimumWidth(160)
        self.action_button.setVisible(False)
        self.action_button.clicked.connect(self.download_requested.emit)

        self.btn_close = QPushButton("Cancelar")
        self.btn_close.setProperty("role", "action_outlined")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setMinimumWidth(120)
        self.btn_close.clicked.connect(self.reject)

        self.add_action_buttons(self.action_button, self.btn_close)

    def show_update_available(self, version: str):
        self.title_lbl.setText("Actualización Disponible")
        self.status_label.setText(f"¡Nueva versión {version} está lista para descargar!")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.action_button.setVisible(True) 
        self.btn_close.setText("Quizás luego")

    def show_downloading(self):
        self.title_lbl.setText("Descargando Actualización")
        self.status_label.setText("Por favor espera, no cierres la aplicación.")
        self.progress_bar.setRange(0, 0) 
        self.action_button.setEnabled(False)
        self.btn_close.setVisible(False) 

    def show_no_update(self):
        self.title_lbl.setText("Sistema Actualizado")
        self.status_label.setText("Tu versión de MiniKick ya es la última disponible.")
        self.progress_bar.setVisible(False)
        self.btn_close.setText("Cerrar")
        self.btn_close.setProperty("role", "action_accent")
        self.btn_close.style().unpolish(self.btn_close)
        self.btn_close.style().polish(self.btn_close)

    def show_error(self, message: str):
        self.title_lbl.setText("Error de Actualización")
        self.status_label.setText(f"Ocurrió un fallo: {message}")
        self.progress_bar.hide()
        self.action_button.setVisible(False)
        self.btn_close.setText("Cerrar")
        self.btn_close.setVisible(True)
        self.btn_close.setEnabled(True)