# frontend\window\schedule.py

from __future__ import annotations

from backend.workers import ScheduleWorker


class SchedulePresenter:
    def __init__(self, window) -> None:
        self._window = window

    def start_worker(self) -> None:
        w = self._window
        w._schedule_slot.start(self._build_worker)

    def _build_worker(self) -> ScheduleWorker:
        w = self._window
        worker = ScheduleWorker(w.schedule_service)
        worker.schedule_triggered.connect(self.on_schedule_triggered)
        return worker

    def on_schedule_triggered(self, schedule: dict, _result: dict) -> None:
        w = self._window
        name = schedule.get("name", "")
        title = w.i18n.get("stream_info.toasts.schedule_auto_applied")
        w.toast.show_toast(title=title, message=name, state="success")
        w.schedule_controller.reload_schedules()
        w.schedule_controller.fetch_current_info()

    def send_timer_message(
        self,
        message: str,
        apply_kick: bool = True,
        apply_twitch: bool = True,
    ) -> None:
        if message:
            self._window.command_service.post_chat_message(
                message,
                apply_kick=apply_kick,
                apply_twitch=apply_twitch,
            )
