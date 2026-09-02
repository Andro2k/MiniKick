# backend\workers\update_worker.py

import logging
from PySide6.QtCore import QThread, Signal
from backend.services.system.updater_service import UpdateManager

logger = logging.getLogger("minikick.workers.updater")

class UpdateCheckWorker(QThread):
    update_found = Signal(object)
    no_update = Signal()
    error = Signal(str)

    def __init__(self, manager: UpdateManager, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Update_Check")
        self.manager = manager

    def run(self):
        logger.debug("[UpdateCheckWorker] Checking for updates on GitHub...")
        try:
            info = self.manager.check_for_updates()
            if info:
                logger.info("[UpdateCheckWorker] Found update: %s", info.get("version", ""))
                self.update_found.emit(info)
            else:
                logger.debug("[UpdateCheckWorker] No updates found.")
                self.no_update.emit()
        except Exception as e:
            logger.error("[UpdateCheckWorker] Error checking for updates: %s", e)
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
        logger.info("[UpdateDownloadWorker] Starting download from %s...", self.download_url)
        try:
            def progress_cb(pct):
                self.progress.emit(pct)
                
            success = self.manager.perform_update(self.download_url, progress_cb)
            logger.info("[UpdateDownloadWorker] Download completed with status: %s", success)
            self.finished.emit(success)
        except Exception as e:
            logger.error("[UpdateDownloadWorker] Error downloading update: %s", e)
            self.error.emit(str(e))

class ReleaseNotesWorker(QThread):
    release_fetched = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, repo_owner: str = "Andro2k", repo_name: str = "MiniKick", i18n=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Release_Notes")
        from backend.services.system.translation_service import TranslationService
        self.i18n = i18n or TranslationService()
        from backend.services.system.updater_service import GithubUpdateProvider
        self.provider = GithubUpdateProvider(repo_owner, repo_name)

    def run(self):
        logger.debug("[ReleaseNotesWorker] Fetching latest release notes...")
        try:
            data = self.provider.fetch_latest_release()
            if data and data.get("tag_name"):
                logger.debug("[ReleaseNotesWorker] Release notes fetched: %s", data.get("tag_name"))
                self.release_fetched.emit(data)
            else:
                err_msg = self.i18n.get("dialogs.release_notes.error")
                logger.error("[ReleaseNotesWorker] Failed to fetch release notes: %s", err_msg)
                self.error_occurred.emit(err_msg)
        except Exception as e:
            logger.error("[ReleaseNotesWorker] Exception fetching release notes: %s", e)
            self.error_occurred.emit(str(e))
