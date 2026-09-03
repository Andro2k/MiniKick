# backend\controllers\timer_controller.py

import threading
import logging
from PySide6.QtCore import QObject, Slot, Signal

logger = logging.getLogger("minikick.timer_controller")

class TimerController(QObject):
    metrics_update_requested = Signal()
    categories_found = Signal(str, object)

    def __init__(self, view, service, toast_manager=None, schedule_service=None, connected_platforms_provider=None, i18n=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.schedule_service = schedule_service
        self.connected_platforms_provider = connected_platforms_provider
        self.i18n = i18n
        self._view_connected = False
        if self.view is not None:
            self._connect_signals()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def _get_i18n(self):
        if self.i18n:
            return self.i18n
        if self.view and hasattr(self.view, "i18n") and self.view.i18n:
            return self.view.i18n
        from backend.services.system.translation_service import TranslationService
        return TranslationService()

    def _connect_signals(self):
        if not self.view or self._view_connected:
            return
        self._view_connected = True
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
        logger.info("[User Action] Searching categories in timer wizard: query='%s', platform='%s'", query, platform)

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
            if hasattr(self.view, "set_connected_platforms") and callable(self.connected_platforms_provider):
                self.view.set_connected_platforms(self.connected_platforms_provider())
            timers = self.service.get_all_timers()
            self.view.populate_table(timers)

    @Slot()
    def _handle_add(self):
        logger.info("[User Action] Opened Add Timer dialog")
        connected_plats = self.connected_platforms_provider() if callable(self.connected_platforms_provider) else None
        data = self.view.show_add_dialog(connected_platforms=connected_plats)
        if data:
            data.pop("timer_id", None)
            if data.get("name") and data.get("messages"):
                logger.info("[User Action] Created new timer: name='%s', messages=%d, online=%s min, offline=%s min",
                            data.get("name"), len(data.get("messages", [])), data.get("interval_online"), data.get("interval_offline"))
                self.service.save_timer(**data)
                self.load_initial_data()
                self.metrics_update_requested.emit()
                self._show_toast("timer.status.created", "timer.status.created_msg", data['name'], "success")

    @Slot(int)
    def _handle_edit(self, timer_id: int):
        existing = self.service.get_timer_by_id(timer_id)
        if not existing:
            return
        logger.info("[User Action] Opened Edit Timer dialog: id=%d, name='%s'", timer_id, existing.get("name"))
        connected_plats = self.connected_platforms_provider() if callable(self.connected_platforms_provider) else None
        data = self.view.show_edit_dialog(existing, connected_platforms=connected_plats)
        if data:
            if data.get("name") and data.get("messages"):
                logger.info("[User Action] Updated timer: id=%d, name='%s'", timer_id, data.get("name"))
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
        logger.info("[User Action] Deleted timer: id=%d, name='%s'", timer_id, name)
        self.service.delete_timer(timer_id)
        self.load_initial_data()
        self.metrics_update_requested.emit()
        self._show_toast("timer.status.deleted", "timer.status.deleted_msg", name, "warning")

    @Slot(int, bool)
    def _handle_status_change(self, timer_id: int, is_active: bool):
        existing = self.service.get_timer_by_id(timer_id)
        if not existing:
            return
        if existing.get("is_active") == is_active:
            return

        logger.info("[User Action] Toggled timer status: id=%d, name='%s', is_active=%s", timer_id, existing.get("name"), is_active)
        self.service.save_timer(
            timer_id=timer_id,
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
            apply_youtube=existing.get("apply_youtube", True)
        )
        self.load_initial_data()
        self.metrics_update_requested.emit()

        i18n = self._get_i18n()
        status_text = i18n.get("timer.status.enabled") if is_active else i18n.get("timer.status.disabled")
        msg = i18n.get("timer.status.toggled_msg").replace("{name}", existing['name']).replace("{status}", status_text.lower())
        if self.toast:
            self.toast.show_toast(
                title=i18n.get("timer.status.updated"),
                message=msg,
                state="success",
                tag=f"timer_{timer_id}"
            )

    @Slot(str)
    def _handle_search(self, search_term: str):
        logger.debug("[User Action] Filtered timers table by search term: '%s'", search_term)
        if not search_term.strip():
            self.load_initial_data()
        else:
            timers = self.service.get_all_timers()
            term_lower = search_term.lower()
            filtered = [
                t for t in timers 
                if term_lower in t["name"].lower() or any(term_lower in m.lower() for m in t["messages"])
            ]
            self.view.populate_table(filtered)

    def _show_toast(self, title_key: str, msg_key: str, val: str, state: str):
        if self.toast:
            i18n = self._get_i18n()
            self.toast.show_toast(
                title=i18n.get(title_key),
                message=(i18n.get(msg_key)).replace("{name}", val),
                state=state
            )
