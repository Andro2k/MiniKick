# backend\controllers\webhooks_controller.py

import threading
import logging
from PySide6.QtCore import Slot, Signal
from .base_controller import BaseController

logger = logging.getLogger("minikick.webhooks_controller")


class WebhooksController(BaseController):
    ping_finished = Signal(object)

    def __init__(self, view, service, toast_manager=None, i18n=None):
        super().__init__(view=view, service=service, toast_manager=toast_manager, i18n=i18n)
        if self.view is not None:
            self._connect_signals()

    def _get_i18n(self):
        if self.i18n:
            return self.i18n
        if self.view and getattr(self.view, "i18n", None):
            return self.view.i18n
        from backend.services.system import TranslationService
        return TranslationService()

    def _connect_signals(self):
        if not self._connect_crud_signals(
            on_add=self._handle_add,
            on_edit=self._handle_edit,
            on_delete=self._handle_delete,
            on_status_toggle=self._handle_status_change,
        ):
            return
        self.view.search_text_changed.connect(self._handle_search)
        self.view.test_requested.connect(self._handle_test)
        self.ping_finished.connect(self.view.set_ping_result)

    def load_initial_data(self):
        if self.view is not None:
            self.view.populate_table(self.service.list_endpoints())

    def _dialog_options(self) -> dict:
        return {
            "event_types": self.service.event_types(),
            "platforms": self.service.platforms(),
            "url_validator": self.service.validate_url,
        }

    @Slot()
    def _handle_add(self):
        logger.info("[User Action] Opened Add Webhook dialog")
        data = self.view.show_add_dialog(**self._dialog_options())
        if data:
            data.pop("endpoint_id", None)
            self._save(data, "webhooks.status.created", "webhooks.status.created_msg")

    @Slot(str)
    def _handle_edit(self, endpoint_id: str):
        existing = self.service.get_endpoint(endpoint_id)
        if not existing:
            return
        logger.info("[User Action] Opened Edit Webhook dialog: name='%s'", existing.name)
        data = self.view.show_edit_dialog(existing, **self._dialog_options())
        if data:
            data["endpoint_id"] = endpoint_id
            data["enabled"] = existing.enabled
            self._save(data, "webhooks.status.updated", "webhooks.status.updated_msg")

    @Slot(str)
    def _handle_delete(self, endpoint_id: str):
        existing = self.service.get_endpoint(endpoint_id)
        if not existing or not self.service.delete_endpoint(endpoint_id):
            return
        logger.info("[User Action] Deleted webhook endpoint: name='%s'", existing.name)
        self.load_initial_data()
        self._show_toast("webhooks.status.deleted", "webhooks.status.deleted_msg", existing.name, "warning")

    @Slot(str, bool)
    def _handle_status_change(self, endpoint_id: str, is_active: bool):
        try:
            changed = self.service.set_enabled(endpoint_id, is_active)
        except Exception as err:
            logger.error("[WebhooksController] Could not change endpoint status: %s", type(err).__name__)
            self._show_toast("webhooks.status.error", "webhooks.status.save_failed", "", "danger")
            self.load_initial_data()
            return
        if not changed:
            return
        logger.info("[User Action] Toggled webhook endpoint: is_active=%s", is_active)
        self.load_initial_data()

    @Slot(str)
    def _handle_search(self, search_term: str):
        term = search_term.strip().lower()
        endpoints = self.service.list_endpoints()
        if term:
            endpoints = [ep for ep in endpoints if term in ep.name.lower()]
        self.view.populate_table(endpoints)

    @Slot(object)
    def _handle_test(self, data: dict):
        logger.info("[User Action] Sent webhook test ping")

        def _worker():
            try:
                result = self.service.send_test_ping(data)
            except Exception as err:
                logger.error("[WebhooksController] Test ping failed unexpectedly: %s", type(err).__name__)
                from backend.services.webhooks import PingResult
                result = PingResult(ok=False, error=type(err).__name__)
            self.ping_finished.emit(result)

        threading.Thread(target=_worker, name="WebhookTestPing", daemon=True).start()

    def _save(self, data: dict, title_key: str, msg_key: str) -> None:
        try:
            endpoint = self.service.save_endpoint(data)
        except Exception as err:
            logger.error("[WebhooksController] Could not save endpoint: %s", type(err).__name__)
            self._show_toast("webhooks.status.error", "webhooks.status.save_failed", "", "danger")
            return
        logger.info("[User Action] Saved webhook endpoint: name='%s', events=%d", endpoint.name, len(endpoint.events))
        self.load_initial_data()
        self._show_toast(title_key, msg_key, endpoint.name, "success")

    def _show_toast(self, title_key: str, msg_key: str, name: str, state: str) -> None:
        if self.toast:
            i18n = self._get_i18n()
            self.toast.show_toast(
                title=i18n.get(title_key),
                message=i18n.get(msg_key).replace("{name}", name),
                state=state,
            )
