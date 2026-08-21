# backend\workers\update_worker.py

from PySide6.QtCore import QThread, Signal
from backend.services.system.updater_service import UpdateManager

class UpdateCheckWorker(QThread):
    update_found = Signal(object)
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

class ReleaseNotesWorker(QThread):
    release_fetched = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, repo_owner: str = "Andro2k", repo_name: str = "MiniKick", parent=None):
        super().__init__(parent)
        from backend.services.system.updater_service import GithubUpdateProvider
        self.provider = GithubUpdateProvider(repo_owner, repo_name)

    def run(self):
        try:
            data = self.provider.fetch_latest_release()
            if data and data.get("tag_name"):
                self.release_fetched.emit(data)
            else:
                self.error_occurred.emit("No release data found")
        except Exception as e:
            self.error_occurred.emit(str(e))
