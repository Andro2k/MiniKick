# backend\controllers\spam_controller.py

import logging
from PySide6.QtCore import QObject, Slot

logger = logging.getLogger("minikick.controllers.spam")

class SpamController(QObject):
    def __init__(self, view, service, toast_manager=None, connected_platforms_provider=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.connected_platforms_provider = connected_platforms_provider
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def _connect_signals(self):
        self.view.filter_updated.connect(self._handle_filter_update)

    def load_initial_data(self):
        self.service.reload_filters()
        if self.view is not None:
            if callable(self.connected_platforms_provider) and hasattr(self.view, "set_connected_platforms"):
                self.view.set_connected_platforms(self.connected_platforms_provider())
            filters = self.service.filters
            self.view.populate_filters(filters)

    @Slot(str, object)
    def _handle_filter_update(self, filter_id: str, config: dict):
        previous_config = self.service.filters.get(filter_id, {})
        was_active = previous_config.get("is_active", False)
        is_active = config.get("is_active", False)
        logger.info("[User Action] Updated spam filter '%s': is_active=%s, was_active=%s, params=%s",
                    filter_id, is_active, was_active, {k: v for k, v in config.items() if k != "is_active"})
        self.service.save_filter(filter_id, config)
        filter_keys = {
            "caps_protection": "spam.filters.caps.title",
            "link_protection": "spam.filters.link.title",
            "emote_protection": "spam.filters.emote.title",
            "paragraph_protection": "spam.filters.paragraph.title",
            "symbol_protection": "spam.filters.symbol.title",
            "repetition_protection": "spam.filters.repetition.title",
        }
        i18n_key = filter_keys.get(filter_id)
        filter_name = self.view.i18n.get(i18n_key) if i18n_key else filter_id
        
        if was_active != is_active:
            title_key = "spam.status.activated" if is_active else "spam.status.deactivated"
            msg_key = "spam.status.activated_msg" if is_active else "spam.status.deactivated_msg"
            title = self.view.i18n.get(title_key)
            message = self.view.i18n.get(msg_key).replace("{filter_name}", filter_name)
            state = "success" if is_active else "info"

            if self.toast:
                self.toast.show_toast(
                    title=title,
                    message=message,
                    state=state
                )
