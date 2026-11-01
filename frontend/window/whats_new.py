# frontend\window\whats_new.py

import logging
from typing import Callable

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget

from backend.connections import WorkerSlot
from frontend.dialogs import WhatsNewDialog

logger = logging.getLogger("minikick.core")


class WhatsNewPresenter:
    def __init__(
        self,
        parent: QWidget,
        service,
        sidebar,
        i18n,
        app_version: str,
        slot: WorkerSlot,
        is_shutting_down: Callable[[], bool],
    ) -> None:
        self._parent = parent
        self._service = service
        self._sidebar = sidebar
        self._i18n = i18n
        self._app_version = app_version
        self._is_shutting_down = is_shutting_down
        self.slot = slot

    def init_badges(self) -> None:
        try:
            for section in self._service.get_unseen_badges():
                self._sidebar.set_tab_badge(section, True)
        except Exception as e:
            logger.warning("[WhatsNew] Error initializing feature badges: %s", e)

    def on_section_viewed(self, section_name: str) -> None:
        try:
            self._service.mark_section_seen(section_name)
        except Exception as e:
            logger.warning("[WhatsNew] Error marking section '%s' as seen: %s", section_name, e)

    def check_dialog(self) -> None:
        if self._is_shutting_down():
            return
        try:
            if not self._service.should_show_modal():
                return
            is_first = self._service.is_first_launch()
            highlights = self._service.get_highlights()
            if not highlights:
                self.fetch_remote_if_needed()
                return
            dialog = WhatsNewDialog(
                i18n=self._i18n,
                highlights=highlights,
                is_first_launch=is_first,
                app_version=self._app_version,
                parent=self._parent,
            )
            dialog.exec()
            self._service.mark_version_seen()
        except Exception as e:
            logger.error("[WhatsNew] Error displaying What's New dialog: %s", e)

    def fetch_remote_if_needed(self) -> None:
        if self._is_shutting_down():
            return
        self.slot.start(self._create_worker)

    def on_remote_fetched(self, highlights: list) -> None:
        if self._is_shutting_down():
            return
        try:
            self._service.set_highlights(highlights)
            self.init_badges()
            if self._service.should_show_modal():
                self.check_dialog()
        except Exception as e:
            logger.warning("[WhatsNew] Error handling remote highlights: %s", e)

    def _create_worker(self) -> QThread:
        from backend.workers import WhatsNewWorker

        worker = WhatsNewWorker(self._app_version, parent=self._parent)
        worker.highlights_fetched.connect(self.on_remote_fetched)
        worker.finished.connect(worker.deleteLater)
        return worker
