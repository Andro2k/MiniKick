# frontend/controllers/update_controller.py

from PySide6.QtCore import QObject, Slot
from frontend.dialogs.update_dialog import UpdateDialog
from frontend.workers.update_worker import UpdateCheckWorker, UpdateDownloadWorker

class UpdateController(QObject):
    def __init__(self, main_window, updater_manager, i18n):
        super().__init__()
        self.main_window = main_window
        self.updater_manager = updater_manager
        self.i18n = i18n
        self.bg_update_worker = None

    def check_updates_silently(self, sidebar):
        self.bg_update_worker = UpdateCheckWorker(self.updater_manager)
        self.bg_update_worker.update_found.connect(
            lambda info: sidebar.set_update_available(True)
        )
        self.bg_update_worker.start()

    @Slot()
    def handle_update_check(self):
        dialog = UpdateDialog(self.i18n, parent=self.main_window)       
        update_info = {"url": ""}
        
        self.check_worker = UpdateCheckWorker(self.updater_manager)
        
        def on_update_found(info):
            update_info["url"] = info['download_url']
            dialog.show_update_available(info['version'])
            
        self.check_worker.update_found.connect(on_update_found)
        self.check_worker.no_update.connect(dialog.show_no_update)
        self.check_worker.error.connect(dialog.show_error)

        def on_download_requested():
            dialog.show_downloading()
            self.download_worker = UpdateDownloadWorker(self.updater_manager, update_info["url"])
            self.download_worker.progress.connect(dialog.update_progress)

            def on_download_finished(success):
                if success:
                    dialog.show_complete()
                else:
                    error_msg = self.i18n.get("main.dialogs.update.msg_unexpected_error")
                    dialog.show_error(error_msg)
                    
            self.download_worker.finished.connect(on_download_finished)
            self.download_worker.error.connect(dialog.show_error)
            self.download_worker.start()

        def on_restart_requested():
            dialog.accept()
            self.main_window._force_quit()
            
        dialog.download_requested.connect(on_download_requested)
        dialog.restart_requested.connect(on_restart_requested)
        self.check_worker.start()
        dialog.exec()