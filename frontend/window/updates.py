# frontend\window\updates.py

import logging
from typing import Callable

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QWidget

from frontend.dialogs import ModernConfirmDialog
from frontend.worker_shutdown import is_worker_running

logger = logging.getLogger("minikick.core")

_TOAST_TAG = "auto_update_download"


class AutoUpdateCoordinator(QObject):
    def __init__(
        self,
        parent: QWidget,
        updater_controller,
        settings_service,
        sidebar,
        toast,
        i18n,
        is_shutting_down: Callable[[], bool],
        request_quit: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self._parent_window = parent
        self._updater = updater_controller
        self._settings_service = settings_service
        self._sidebar = sidebar
        self._toast = toast
        self._i18n = i18n
        self._is_shutting_down = is_shutting_down
        self._request_quit = request_quit
        self.download_active = False
        self._info: dict = {}

    @Slot(object)
    def on_update_found(self, info) -> None:
        version = ""
        if isinstance(info, dict):
            version = info.get("version", "")
        elif isinstance(info, str):
            version = info
        self._sidebar.set_update_available(True, version=version)
        self._download_if_enabled(info)

    @Slot(bool)
    def on_download_finished(self, success: bool) -> None:
        if not self._finish_download():
            return
        version = str(self._info.get("version", ""))
        if not success:
            self._show_toast(
                self._i18n.get("settings.system.auto_update_download_failed_title"),
                self._i18n.get("dialogs.update.msg_unexpected_error"),
                "danger",
            )
            return

        dialog = ModernConfirmDialog(
            self._i18n,
            parent=self._parent_window,
            title_text=self._i18n.get("settings.system.auto_update_ready_title"),
            body_text=self._i18n.get("settings.system.auto_update_ready_desc").replace("{version}", version),
        )
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._updater.install_update()
            self._request_quit()
            return

        self._show_toast(
            self._i18n.get("settings.system.auto_update_download_complete_title"),
            self._i18n.get("settings.system.auto_update_download_complete_desc").replace("{version}", version),
            "success",
        )

    @Slot(str)
    def on_download_error(self, error_message: str) -> None:
        if not self._finish_download():
            return
        self._show_toast(
            self._i18n.get("settings.system.auto_update_download_failed_title"),
            error_message,
            "danger",
        )

    def _finish_download(self) -> bool:
        if not self.download_active:
            return False
        self.download_active = False
        return not self._is_shutting_down()

    def _download_if_enabled(self, info: object) -> None:
        if self._is_shutting_down():
            return
        if not self._settings_service.is_auto_update_download_enabled():
            return
        if not isinstance(info, dict):
            logger.error(
                "[Updater] Silent update result has an unsupported format: %s",
                type(info).__name__,
            )
            return

        download_url = info.get("download_url")
        if not isinstance(download_url, str) or not download_url.strip():
            logger.error(
                "[Updater] Automatic download skipped because the release has no download URL."
            )
            return
        if self.download_active:
            logger.debug("[Updater] Automatic update download is already in progress.")
            return
        if is_worker_running(self._updater.download_worker):
            logger.info(
                "[Updater] Automatic download skipped because another update download is active."
            )
            return

        self.download_active = True
        self._info = info
        try:
            started = self._updater.start_download(download_url.strip())
        except RuntimeError:
            self.download_active = False
            logger.exception("[Updater] Could not start automatic update download.")
            return

        if not started:
            self.download_active = False
            return

        self._toast.show_toast(
            title=self._i18n.get("settings.system.auto_update_download_started_title"),
            message=self._i18n.get("settings.system.auto_update_download_started_desc"),
            state="info",
            tag=_TOAST_TAG,
        )

    def _show_toast(self, title: str, message: str, state: str) -> None:
        self._toast.show_toast(
            title=title,
            message=message,
            state=state,
            tag=_TOAST_TAG,
        )
