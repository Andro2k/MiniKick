# frontend\window\window_state.py

import logging
from typing import Callable

from PySide6.QtCore import QByteArray, QEvent, Qt
from PySide6.QtWidgets import QMainWindow

from backend.interfaces import IConfigProvider

logger = logging.getLogger("minikick.core")


class WindowStateManager:
    SETTING_MINIMIZE_TRAY = "minimize_to_tray"
    SETTING_WINDOW_MAXIMIZED = "window_is_maximized"
    SETTING_WINDOW_GEOMETRY = "window_geometry"

    def __init__(
        self,
        window: QMainWindow,
        config: IConfigProvider,
        on_hidden_to_tray: Callable[[], None],
    ) -> None:
        self._window = window
        self._config = config
        self._on_hidden_to_tray = on_hidden_to_tray
        self.was_maximized_before_tray = True

    def minimize_to_tray_enabled(self) -> bool:
        return self._config.load_bool(self.SETTING_MINIMIZE_TRAY, False)

    def restore(self) -> None:
        geom_hex = self._config.load_string(self.SETTING_WINDOW_GEOMETRY, "")
        if geom_hex:
            try:
                self._window.restoreGeometry(QByteArray.fromHex(geom_hex.encode("ascii")))
            except (UnicodeError, ValueError, RuntimeError):
                logger.exception("[MainWindow] Failed to restore window geometry.")

        is_max = self._config.load_bool(self.SETTING_WINDOW_MAXIMIZED, True)
        self.was_maximized_before_tray = is_max
        if is_max:
            self._window.showMaximized()
        else:
            self._window.show()

    def save(self) -> None:
        window = self._window
        try:
            if window.isMinimized():
                is_max = self.was_maximized_before_tray
            else:
                is_max = window.isMaximized()

            self._config.save_bool(self.SETTING_WINDOW_MAXIMIZED, is_max)
            if not is_max and not window.isMinimized():
                geom_hex = bytes(window.saveGeometry()).hex()
                self._config.save_string(self.SETTING_WINDOW_GEOMETRY, geom_hex)
            logger.debug("[MainWindow] Saved window state: maximized=%s", is_max)
        except Exception:
            logger.exception("[MainWindow] Failed to save window state.")

    def restore_from_tray(self) -> None:
        logger.info("[User Action] Window restored from system tray")
        if self.was_maximized_before_tray:
            self._window.showMaximized()
        else:
            self._window.showNormal()
        self._window.activateWindow()

    def handle_state_change(self, event: QEvent) -> None:
        if event.type() != QEvent.Type.WindowStateChange or not self._window.isMinimized():
            return
        self.was_maximized_before_tray = bool(event.oldState() & Qt.WindowState.WindowMaximized)
        if self.minimize_to_tray_enabled():
            logger.info("[User Action] Window minimized to system tray")
            self._window.hide()
            self._on_hidden_to_tray()
