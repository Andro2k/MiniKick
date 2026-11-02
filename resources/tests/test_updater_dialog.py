from frontend.common import get_global_qss
from frontend.dialogs.updater_dialog import UpdateDialog


class _Translations:
    _values = {
        "dialogs.update.title_default": "Actualización del Sistema",
        "dialogs.update.btn_restart": "Reiniciar ahora",
        "dialogs.update.btn_close": "Cerrar",
        "dialogs.update.subtitle_connecting": "Conectando...",
        "dialogs.update.lbl_progress": "Progreso",
        "dialogs.update.subtitle_downloading": "Descargando la nueva versión...",
        "dialogs.update.btn_downloading": "Descargando...",
        "dialogs.update.title_completed": "Actualización completada",
        "dialogs.update.subtitle_restart_req": "Se requiere reiniciar para completar la instalación.",
    }

    def get(self, key: str) -> str:
        return self._values.get(key, key)


def test_update_dialog_reserves_space_for_completed_content(qapp):
    previous_stylesheet = qapp.styleSheet()
    qapp.setStyleSheet(get_global_qss(13))
    dialog = UpdateDialog(_Translations())
    try:
        dialog.show()
        qapp.processEvents()

        dialog.show_downloading()
        assert dialog.btn_primary.isVisible()
        assert not dialog.btn_secondary.isVisible()

        qapp.processEvents()
        dialog.update_progress(100)
        dialog.show_complete()
        assert dialog.btn_primary.isVisible()
        assert dialog.btn_secondary.isVisible()

        qapp.processEvents()
        assert dialog.body.height() >= dialog.body.sizeHint().height()
        assert dialog.progress_container.height() >= dialog.progress_container.sizeHint().height()
        assert dialog.lbl_prog_text.height() >= dialog.lbl_prog_text.sizeHint().height()
        assert dialog.body.geometry().bottom() < dialog.footer.geometry().top()
        assert dialog.btn_secondary.geometry().right() < dialog.btn_primary.geometry().left()
        assert dialog.btn_primary.geometry().right() <= dialog.footer.width() - 20
    finally:
        dialog.close()
        qapp.setStyleSheet(previous_stylesheet)
