# backend\controllers\base_controller.py

from PySide6.QtCore import QObject

class BaseController(QObject):
    def __init__(
        self,
        view=None,
        service=None,
        toast_manager=None,
        i18n=None,
        connected_platforms_provider=None,
        parent=None,
    ):
        super().__init__(parent)
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.i18n = i18n
        self.connected_platforms_provider = connected_platforms_provider
        self._view_connected = False

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            if hasattr(self, "load_initial_data"):
                self.load_initial_data()

    def _ensure_view_connected(self) -> bool:
        if not self.view or self._view_connected:
            return False
        self._view_connected = True
        return True

    def _connect_crud_signals(
        self,
        on_add=None,
        on_edit=None,
        on_delete=None,
        on_status_toggle=None
    ) -> bool:
        if not self._ensure_view_connected():
            return False
        if on_add and hasattr(self.view, "add_requested"):
            self.view.add_requested.connect(on_add)
        if on_edit and hasattr(self.view, "edit_requested"):
            self.view.edit_requested.connect(on_edit)
        if on_delete and hasattr(self.view, "delete_requested"):
            self.view.delete_requested.connect(on_delete)
        if on_status_toggle and hasattr(self.view, "status_toggled"):
            self.view.status_toggled.connect(on_status_toggle)
        return True
