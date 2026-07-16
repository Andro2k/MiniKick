# backend\controllers\spam_controller.py

from PySide6.QtCore import QObject, Slot

class SpamController(QObject):
    def __init__(self, view, service, toast_manager=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self._connect_signals()

    def _connect_signals(self):
        self.view.filter_updated.connect(self._handle_filter_update)

    def load_initial_data(self):
        self.service.reload_filters()
        filters = self.service.filters
        self.view.populate_filters(filters)

    @Slot(str, dict)
    def _handle_filter_update(self, filter_id: str, config: dict):
        previous_config = self.service.filters.get(filter_id, {})
        was_active = previous_config.get("is_active", False)
        is_active = config.get("is_active", False)
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
