# frontend\dialogs\update_flow.py

import logging

from .updater_dialog import UpdateDialog

logger = logging.getLogger("minikick.dialogs.update_flow")


def present_update_dialog(updater_controller, parent_window, i18n, on_restart_callback=None) -> None:
    """Muestra el diálogo modal de actualización conectado al UpdaterController (solo señales y slots)."""
    logger.debug("[UpdateFlow] Presenting UpdateDialog modal to user.")
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
        updater_controller.start_download(update_info["url"])

    def on_restart_requested():
        dialog.accept()
        updater_controller.install_update()
        if on_restart_callback:
            on_restart_callback()

    updater_controller.update_found.connect(on_update_found)
    updater_controller.no_update.connect(dialog.show_no_update)
    updater_controller.error.connect(dialog.show_error)
    updater_controller.download_progress.connect(dialog.update_progress)
    updater_controller.download_finished.connect(on_download_finished)

    dialog.download_requested.connect(on_download_requested)
    dialog.restart_requested.connect(on_restart_requested)

    updater_controller.start_update_check()
    try:
        dialog.exec()
    finally:
        try:
            updater_controller.update_found.disconnect(on_update_found)
            updater_controller.no_update.disconnect(dialog.show_no_update)
            updater_controller.error.disconnect(dialog.show_error)
            updater_controller.download_progress.disconnect(dialog.update_progress)
            updater_controller.download_finished.disconnect(on_download_finished)
        except Exception as e:
            logger.debug("[UpdateFlow] Dialog signals disconnect notice: %s", e)
