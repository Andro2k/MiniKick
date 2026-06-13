# frontend/workers/update_worker.py

from PySide6.QtCore import QThread, Signal
from backend.updater_manager import UpdateManager

class UpdateCheckWorker(QThread):
    """Hilo para buscar actualizaciones sin congelar la UI."""
    update_found = Signal(dict)
    no_update = Signal()
    error = Signal(str)

    def __init__(self, manager: UpdateManager):
        super().__init__()
        self.manager = manager

    def run(self):
        try:
            info = self.manager.check_for_updates()
            if info:
                self.update_found.emit(info)
            else:
                self.no_update.emit()
        except Exception as e:
            self.error.emit(str(e))

class UpdateDownloadWorker(QThread):
    """Hilo para descargar e instalar sin congelar la UI."""
    finished = Signal(bool)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, manager: UpdateManager, download_url: str):
        super().__init__()
        self.manager = manager
        self.download_url = download_url

    def run(self):
        try:
            def progress_cb(pct):
                self.progress.emit(pct)
                
            success = self.manager.perform_update(self.download_url, progress_cb)
            self.finished.emit(success)
        except Exception as e:
            self.error.emit(str(e))