# backend\controllers\update_controller.py

from PySide6.QtCore import QObject, Slot, Signal

class UpdateController(QObject):
    update_found_silent = Signal()
    
    update_check_started = Signal()
    update_found = Signal(dict)
    no_update = Signal()
    error = Signal(str)
    
    download_started = Signal()
    download_progress = Signal(int)
    download_finished = Signal(bool)

    def __init__(self, updater_manager):
        super().__init__()
        self.updater_manager = updater_manager
        self.bg_update_worker = None
        self.check_worker = None
        self.download_worker = None

    def check_updates_silently(self):   
        from backend.workers import UpdateCheckWorker
        self.bg_update_worker = UpdateCheckWorker(self.updater_manager)
        self.bg_update_worker.update_found.connect(
            lambda info: self.update_found_silent.emit()
        )
        self.bg_update_worker.start()

    @Slot()
    def start_update_check(self):
        from backend.workers import UpdateCheckWorker
        self.update_check_started.emit()
        self.check_worker = UpdateCheckWorker(self.updater_manager)
        self.check_worker.update_found.connect(self.update_found.emit)
        self.check_worker.no_update.connect(self.no_update.emit)
        self.check_worker.error.connect(self.error.emit)
        self.check_worker.start()

    @Slot(str)
    def start_download(self, url: str):
        from backend.workers import UpdateDownloadWorker
        self.download_started.emit()
        self.download_worker = UpdateDownloadWorker(self.updater_manager, url)
        self.download_worker.progress.connect(self.download_progress.emit)
        self.download_worker.finished.connect(self.download_finished.emit)
        self.download_worker.error.connect(self.error.emit)
        self.download_worker.start()

    @Slot()
    def install_update(self):
        self.updater_manager.install_update()
