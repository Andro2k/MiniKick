# backend\controllers\timer_controller.py

import threading
import logging
from PySide6.QtCore import QObject, Slot, Signal

logger = logging.getLogger("minikick.timer_controller")

class TimerController(QObject):
    metrics_update_requested = Signal()
    categories_found = Signal(str, object)

    def __init__(self, view, service, toast_manager=None, schedule_service=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.schedule_service = schedule_service
        if self.view is not None:
            self._connect_signals()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def _connect_signals(self):
        self.view.add_requested.connect(self._handle_add)
        self.view.edit_requested.connect(self._handle_edit)
        self.view.delete_requested.connect(self._handle_delete)
        self.view.status_toggled.connect(self._handle_status_change)
        self.view.search_text_changed.connect(self._handle_search)
        if hasattr(self.view, "search_category_requested"):
            self.view.search_category_requested.connect(self.search_categories)
        if hasattr(self.view, "set_category_search_results"):
            self.categories_found.connect(self.view.set_category_search_results)

    def search_categories(self, query: str, platform: str = "both") -> None:
        if not self.schedule_service or not query.strip():
            return

        def _worker():
            try:
                res = self.schedule_service.search_categories(query.strip(), platform)
                kick_items = res.get("kick", []) if isinstance(res, dict) else []
                twitch_items = res.get("twitch", []) if isinstance(res, dict) else []
                combined = kick_items + twitch_items

                q_lower = query.strip().lower()
                def _sort_key(item: dict) -> tuple[int, int, str]:
                    n = item.get("name", "").strip().lower()
                    score = 0 if n == q_lower else (1 if n.startswith(q_lower) else 2)
                    return (score, len(n), n)

                sorted_results = sorted(combined, key=_sort_key)
                self.categories_found.emit("both", sorted_results)
            except Exception as e:
                logger.error("[TimerController] Error searching categories: %s", e)

        threading.Thread(target=_worker, daemon=True).start()

    def load_initial_data(self):
        if self.view is not None:
            timers = self.service.get_all_timers()
            self.view.populate_table(timers)

    @Slot()
    def _handle_add(self):
        data = self.view.show_add_dialog()
        if data:
            data.pop("timer_id", None)
            if data.get("name") and data.get("messages"):
                self.service.save_timer(**data)
                self.load_initial_data()
                self.metrics_update_requested.emit()
                self._show_toast("timer.status.created", "timer.status.created_msg", data['name'], "success")

    @Slot(int)
    def _handle_edit(self, timer_id: int):
        existing = self.service.get_timer_by_id(timer_id)
        if not existing:
            return
        
        data = self.view.show_edit_dialog(existing)
        if data:
            if data.get("name") and data.get("messages"):
                self.service.save_timer(**data)
                self.load_initial_data()
                self.metrics_update_requested.emit()
                self._show_toast("timer.status.updated", "timer.status.updated_msg", data['name'], "success")

    @Slot(int)
    def _handle_delete(self, timer_id: int):
        existing = self.service.get_timer_by_id(timer_id)
        if not existing:
            return
        name = existing["name"]
        self.service.delete_timer(timer_id)
        self.load_initial_data()
        self.metrics_update_requested.emit()
        self._show_toast("timer.status.deleted", "timer.status.deleted_msg", name, "warning")

    @Slot(int, bool)
    def _handle_status_change(self, timer_id: int, is_active: bool):
        existing = self.service.get_timer_by_id(timer_id)
        if not existing:
            return
            
        self.service.save_timer(
            name=existing["name"],
            messages=existing["messages"],
            is_active=is_active,
            interval_online=existing["interval_online"],
            interval_offline=existing["interval_offline"],
            chat_lines=existing["chat_lines"],
            keywords=existing["keywords"],
            categories=existing["categories"],
            apply_kick=existing.get("apply_kick", True),
            apply_twitch=existing.get("apply_twitch", True),
            timer_id=timer_id
        )
        self.metrics_update_requested.emit()
        if self.toast:
            title_key = "timer.status.enabled" if is_active else "timer.status.disabled"
            state_color = "success" if is_active else "info"
            
            status_txt = self.view.i18n.get("common.status.active") if is_active else self.view.i18n.get("common.status.inactive")
            message = (self.view.i18n.get("timer.status.toggled_msg")).replace("{name}", existing['name']).replace("{status}", status_txt.lower())

            self.toast.show_toast(
                title=self.view.i18n.get(title_key),
                message=message,
                state=state_color
            )

    @Slot(str)
    def _handle_search(self, text: str):
        if not text.strip():
            self.load_initial_data()
            return
            
        filtered_timers = self.service.search_timers(text)
        self.view.populate_table(filtered_timers)

    def _show_toast(self, title_key: str, msg_key: str, val: str, state: str):
        if self.toast:
            self.toast.show_toast(
                title=self.view.i18n.get(title_key),
                message=(self.view.i18n.get(msg_key)).replace("{name}", val),
                state=state
            )
