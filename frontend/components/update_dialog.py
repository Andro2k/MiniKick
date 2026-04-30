from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar
from PySide6.QtCore import Qt
from backend.updater_manager import UpdateManager
from frontend.workers.update_worker import UpdateCheckWorker, UpdateDownloadWorker

class UpdateDialog(QDialog):
    def __init__(self, manager: UpdateManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Actualización del Sistema")
        self.setFixedSize(350, 150)
        
        # --- UI Setup ---
        self.layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Buscando actualizaciones en el servidor...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Rango 0,0 crea una animación de carga infinita (YAGNI)
        self.layout.addWidget(self.progress_bar)
        
        self.action_button = QPushButton("Cancelar")
        self.action_button.clicked.connect(self.reject)
        self.layout.addWidget(self.action_button)
        
        # --- Inicio de la lógica ---
        self._start_checking()

    def _start_checking(self):
        self.check_worker = UpdateCheckWorker(self.manager)
        self.check_worker.update_found.connect(self.on_update_found)
        self.check_worker.no_update.connect(self.on_no_update)
        self.check_worker.error.connect(self.on_error)
        self.check_worker.start() # Ejecuta el método run() en 2do plano

    def on_update_found(self, info: dict):
        self.progress_bar.setRange(0, 100) # Detenemos la animación infinita
        self.progress_bar.setValue(0)
        self.status_label.setText(f"¡Nueva versión {info['version']} disponible!")
        self.action_button.setText("Descargar e Instalar")
        
        # Cambiamos lo que hace el botón: Ahora descargará la actualización
        self.action_button.clicked.disconnect()
        self.action_button.clicked.connect(lambda: self._start_download(info['download_url']))

    def _start_download(self, url: str):
        self.action_button.setEnabled(False)
        self.progress_bar.setRange(0, 0) # Volvemos a la animación de carga infinita
        self.status_label.setText("Descargando... Por favor espera, no cierres la app.")
        
        self.download_worker = UpdateDownloadWorker(self.manager, url)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_error)
        self.download_worker.start()

    def on_download_finished(self, success: bool):
        if success:
            self.status_label.setText("Instalación completada. Reiniciando...")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
        else:
            self.on_error("Fallo inesperado al descargar el archivo.")

    def on_no_update(self):
        self.progress_bar.hide()
        self.status_label.setText("Tu sistema ya está en la última versión.")
        self.action_button.setText("Cerrar")
        self.action_button.clicked.disconnect()
        self.action_button.clicked.connect(self.accept)

    def on_error(self, message: str):
        self.progress_bar.hide()
        self.status_label.setText(f"Error: {message}")
        self.action_button.setText("Cerrar")
        self.action_button.setEnabled(True)
        self.action_button.clicked.disconnect()
        self.action_button.clicked.connect(self.reject)