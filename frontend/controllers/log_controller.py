# frontend/controllers/log_controller.py

from PySide6.QtCore import QObject, Slot, QUrl
from PySide6.QtGui import QDesktopServices

class LogController(QObject):
    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        self._connect_signals()
        
        # Carga inicial de datos
        self.refresh_file_list()

    def _connect_signals(self):
        self.view.refresh_requested.connect(self.refresh_file_list)
        self.view.read_file_requested.connect(self.read_file)
        self.view.delete_file_requested.connect(self.delete_file)
        self.view.report_bug_requested.connect(self.open_github_issues)

    @Slot()
    def refresh_file_list(self):
        try:
            files = self.service.get_log_files()
            self.view.set_file_list(files)
        except Exception as e:
            self.view.append_log("ERROR", f"Error al cargar archivos de log: {e}")

    @Slot(str)
    def read_file(self, file_name: str):
        try:
            content = self.service.read_log_file(file_name)
            self.view.show_historical_content(file_name, content)
        except Exception as e:
            self.view.show_message("error", "Error", f"No se pudo leer el archivo: {e}")

    @Slot(str)
    def delete_file(self, file_name: str):
        try:
            self.service.delete_log_file(file_name)
            self.view.append_log("INFO", f"Archivo {file_name} eliminado con éxito.")
            self.refresh_file_list()
        except PermissionError:
            self.view.show_message("warning", "Archivo en Uso", f"No se puede eliminar '{file_name}' porque la aplicación está escribiendo en él actualmente.")
        except Exception as e:
            self.view.show_message("error", "Error", f"Error al eliminar el archivo: {e}")

    @Slot()
    def open_github_issues(self):
        QDesktopServices.openUrl(QUrl("https://github.com/Andro2k/MiniKick/issues"))