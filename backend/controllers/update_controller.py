# backend\controllers\update_controller.py

from PySide6.QtCore import QObject, Slot, Signal

class UpdateController(QObject):
    update_found_silent = Signal(object)

    update_check_started = Signal()
    update_found = Signal(object)
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
            lambda info: self.update_found_silent.emit(info)
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

    def show_update_dialog(self, parent_window, i18n, on_restart_callback=None):
        from frontend.dialogs import UpdateDialog

        dialog = UpdateDialog(i18n, parent=parent_window)
        update_info = {"url": ""}

        def on_update_found(info):
            update_info["url"] = info.get("download_url", "")
            dialog.show_update_available(info.get("version", ""))

        def on_download_finished(success):
            if success:
                dialog.show_complete()
            else:
                error_msg = i18n.get("dialogs.update.msg_unexpected_error")
                dialog.show_error(error_msg)

        def on_download_requested():
            dialog.show_downloading()
            self.start_download(update_info["url"])

        def on_restart_requested():
            dialog.accept()
            self.install_update()
            if on_restart_callback:
                on_restart_callback()

        self.update_found.connect(on_update_found)
        self.no_update.connect(dialog.show_no_update)
        self.error.connect(dialog.show_error)
        self.download_progress.connect(dialog.update_progress)
        self.download_finished.connect(on_download_finished)

        dialog.download_requested.connect(on_download_requested)
        dialog.restart_requested.connect(on_restart_requested)

        self.start_update_check()
        dialog.exec()

        try:
            self.update_found.disconnect(on_update_found)
            self.no_update.disconnect(dialog.show_no_update)
            self.error.disconnect(dialog.show_error)
            self.download_progress.disconnect(dialog.update_progress)
            self.download_finished.disconnect(on_download_finished)
        except Exception:
            pass
