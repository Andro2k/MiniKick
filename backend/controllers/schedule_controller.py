# backend\controllers\schedule_controller.py

import threading
import logging
from PySide6.QtCore import QObject, Signal, Slot
from backend.services.schedule.schedule_service import ScheduleService

logger = logging.getLogger("minikick.schedule_controller")

class ScheduleController(QObject):
    info_refreshed = Signal(object)
    categories_found = Signal(str, object)
    update_completed = Signal(object)
    schedules_updated = Signal(object)
    loading_changed = Signal(bool)
    toast_requested = Signal(str, str)

    def __init__(self, view=None, service: ScheduleService = None, toast_manager=None, i18n=None, connected_platforms_provider=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.i18n = i18n
        self.connected_platforms_provider = connected_platforms_provider
        self.is_loading = False
        self._view_connected = False

        self.toast_requested.connect(self._handle_toast_request)

        if self.view:
            self.attach_view(self.view)

    def attach_view(self, view) -> None:
        self.view = view
        if not self.view or self._view_connected:
            return
        self._view_connected = True
        if hasattr(self.view, "refresh_info_requested"):
            self.view.refresh_info_requested.connect(self.fetch_current_info)
        if hasattr(self.view, "update_stream_requested"):
            self.view.update_stream_requested.connect(self.update_stream_info)
        if hasattr(self.view, "search_category_requested"):
            self.view.search_category_requested.connect(self.search_categories)
        if hasattr(self.view, "save_schedule_requested"):
            self.view.save_schedule_requested.connect(self.save_schedule)
        if hasattr(self.view, "delete_schedule_requested"):
            self.view.delete_schedule_requested.connect(self.delete_schedule)
        if hasattr(self.view, "toggle_schedule_requested"):
            self.view.toggle_schedule_requested.connect(self.toggle_schedule)

        self.info_refreshed.connect(self.view.set_current_info if hasattr(self.view, "set_current_info") else self.view.set_current_stream_info)
        self.categories_found.connect(self.view.set_category_search_results)
        self.update_completed.connect(self.view.on_update_completed)
        self.schedules_updated.connect(self.view.set_schedules)
        self.loading_changed.connect(self.view.set_loading)

        self.load_initial_data()

    def _get_i18n(self):
        if self.i18n:
            return self.i18n
        if self.view and hasattr(self.view, "i18n") and self.view.i18n:
            return self.view.i18n
        from backend.services.system.translation_service import TranslationService
        return TranslationService()

    def reload_schedules(self) -> None:
        if not self.service:
            return
        schedules = self.service.get_all_schedules()
        self.schedules_updated.emit(schedules)

    def load_initial_data(self) -> None:
        if self.view and hasattr(self.view, "set_connected_platforms") and callable(self.connected_platforms_provider):
            self.view.set_connected_platforms(self.connected_platforms_provider())
        self.reload_schedules()
        self.fetch_current_info()

    def fetch_current_info(self) -> None:
        if not self.service:
            return
        logger.info("[User Action] Requested refresh of current stream info")

        def _worker():
            self.loading_changed.emit(True)
            try:
                info = self.service.get_current_info()
                self.info_refreshed.emit(info)
            except Exception as e:
                logger.error("[ScheduleController] Error fetching current stream info: %s", e)
            finally:
                self.loading_changed.emit(False)

        threading.Thread(target=_worker, daemon=True).start()

    def search_categories(self, query: str, platform: str = "both") -> None:
        if not self.service or not query.strip():
            return
        logger.debug("[User Action] Searching stream categories: query='%s', platform='%s'", query, platform)

        def _worker():
            try:
                res = self.service.search_categories(query, platform)
                if "kick" in res and res["kick"]:
                    self.categories_found.emit("kick", res["kick"])
                if "twitch" in res and res["twitch"]:
                    self.categories_found.emit("twitch", res["twitch"])
            except Exception as e:
                logger.error("[ScheduleController] Error searching categories: %s", e)

        threading.Thread(target=_worker, daemon=True).start()

    def update_stream_info(self, title: str, kick_cat_id: int | None, twitch_cat_id: str | None, platform: str = "both", category_query: str = "") -> None:
        if not self.service:
            return
        logger.info("[User Action] Executing quick stream update: title='%s', kick_cat_id=%s, twitch_cat_id=%s, platform='%s'",
                    title, kick_cat_id, twitch_cat_id, platform)

        def _worker():
            self.loading_changed.emit(True)
            try:
                res = self.service.update_stream_info(
                    title=title,
                    kick_category_id=kick_cat_id,
                    twitch_category_id=twitch_cat_id,
                    platform=platform,
                    category_query=category_query
                )
                self.update_completed.emit(res)

                kick_ok = res.get("kick", {}).get("success", False)
                twitch_ok = res.get("twitch", {}).get("success", False)

                if platform == "kick":
                    if kick_ok:
                        self.toast_requested.emit("stream_info.toasts.kick_updated_success", "success")
                    else:
                        self.toast_requested.emit("stream_info.toasts.kick_updated_error", "danger")
                elif platform == "twitch":
                    if twitch_ok:
                        self.toast_requested.emit("stream_info.toasts.twitch_updated_success", "success")
                    else:
                        self.toast_requested.emit("stream_info.toasts.twitch_updated_error", "danger")
                else:
                    if kick_ok and twitch_ok:
                        self.toast_requested.emit("stream_info.toasts.all_updated_success", "success")
                    elif kick_ok or twitch_ok:
                        self.toast_requested.emit("stream_info.toasts.partial_updated", "warning")
                    else:
                        self.toast_requested.emit("stream_info.toasts.update_error", "danger")

                self.fetch_current_info()
            except Exception as e:
                logger.error("[ScheduleController] Error updating stream info: %s", e)
                self.toast_requested.emit("stream_info.toasts.update_error", "danger")
            finally:
                self.loading_changed.emit(False)

        threading.Thread(target=_worker, daemon=True).start()

    def save_schedule(self, data: dict) -> None:
        if not self.service:
            return
        logger.info("[User Action] Saved schedule slot: id=%s, name='%s', date='%s', time='%s', target='%s'",
                    data.get("id"), data.get("name"), data.get("date_str"), data.get("time_str"), data.get("target_platform"))
        sched_id = self.service.save_schedule(
            name=data.get("name", ""),
            date_str=data.get("date_str", ""),
            time_str=data.get("time_str", "18:00"),
            target_platform=data.get("target_platform", "all"),
            title=data.get("title", ""),
            kick_category_id=data.get("kick_category_id"),
            kick_category_name=data.get("kick_category_name", ""),
            twitch_category_id=data.get("twitch_category_id"),
            twitch_category_name=data.get("twitch_category_name", ""),
            is_active=data.get("is_active", True),
            schedule_id=data.get("id")
        )
        self._show_toast("stream_info.toasts.schedule_saved", state="success")
        self.schedules_updated.emit(self.service.get_all_schedules())

    def delete_schedule(self, schedule_id: int) -> None:
        if not self.service:
            return
        logger.info("[User Action] Deleted schedule slot: id=%d", schedule_id)
        self.service.delete_schedule(schedule_id)
        self._show_toast("stream_info.toasts.schedule_deleted", state="info")
        self.schedules_updated.emit(self.service.get_all_schedules())

    def toggle_schedule(self, schedule_id: int, is_active: bool) -> None:
        if not self.service:
            return
        logger.info("[User Action] Toggled schedule slot status: id=%d, is_active=%s", schedule_id, is_active)
        self.service.toggle_schedule(schedule_id, is_active)
        self.schedules_updated.emit(self.service.get_all_schedules())

    @Slot(str, str)
    def _handle_toast_request(self, msg_key: str, state: str) -> None:
        self._show_toast(msg_key, state)

    def _show_toast(self, msg_key: str, state: str = "success") -> None:
        if not self.toast:
            return
        i18n = self._get_i18n()
        title = i18n.get("stream_info.header.title")
        msg = i18n.get(msg_key)
        self.toast.show_toast(title=title, message=msg, state=state, tag="schedule_action")
