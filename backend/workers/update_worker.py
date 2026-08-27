# backend\workers\update_worker.py

from PySide6.QtCore import QThread, Signal
from backend.services.system.updater_service import UpdateManager

class UpdateCheckWorker(QThread):
    update_found = Signal(object)
    no_update = Signal()
    error = Signal(str)

    def __init__(self, manager: UpdateManager, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Update_Check")
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
    finished = Signal(bool)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, manager: UpdateManager, download_url: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Update_Download")
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

class ReleaseNotesWorker(QThread):
    release_fetched = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, repo_owner: str = "Andro2k", repo_name: str = "MiniKick", i18n=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Release_Notes")
        from backend.services.system.translation_service import TranslationService
        self.i18n = TranslationService()
        from backend.services.system.updater_service import GithubUpdateProvider
        self.provider = GithubUpdateProvider(repo_owner, repo_name)

    def run(self):
        try:
            data = self.provider.fetch_latest_release()
            if data and data.get("tag_name"):
                self.release_fetched.emit(data)
            else:
                err_msg = self.i18n.get("dialogs.release_notes.error")
                self.error_occurred.emit(err_msg)
        except Exception as e:
            self.error_occurred.emit(str(e))
