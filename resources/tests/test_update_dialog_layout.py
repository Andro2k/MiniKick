# resources\tests\test_update_dialog_layout.py
"""Pruebas del diseño del diálogo de actualización (barra de progreso y alto del contenedor)."""

from PySide6.QtWidgets import QApplication, QWidget


class _FakeI18n:
    def get(self, key: str, **kwargs) -> str:
        return key


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_progress_bar_keeps_fixed_thin_height_while_downloading():
    from frontend.dialogs.updater_dialog import UpdateDialog

    _app()
    parent = QWidget()
    dialog = UpdateDialog(_FakeI18n(), parent=parent)
    dialog.show()
    dialog.show_update_available("v9.9.9")
    dialog.show_downloading()
    dialog.update_progress(81)

    assert dialog.progress_bar.height() == 8
    assert dialog.progress_bar.value() == 81


def test_container_is_tall_enough_for_its_content_after_each_state_change():
    from frontend.dialogs.updater_dialog import UpdateDialog

    _app()
    parent = QWidget()
    dialog = UpdateDialog(_FakeI18n(), parent=parent)
    dialog.show()

    for apply_state in (
        lambda: dialog.show_update_available("v9.9.9"),
        dialog.show_downloading,
        dialog.show_complete,
        dialog.show_no_update,
        lambda: dialog.show_error("error"),
    ):
        apply_state()
        root = dialog.container.layout()
        assert dialog.container.height() >= root.sizeHint().height()


def test_dialog_glow_does_not_use_graphics_effect():
    from frontend.dialogs.updater_dialog import UpdateDialog

    _app()
    parent = QWidget()
    dialog = UpdateDialog(_FakeI18n(), parent=parent)
    dialog.show()
    dialog.show_update_available("v9.9.9")
    dialog.show_complete()

    assert dialog.container.graphicsEffect() is None
