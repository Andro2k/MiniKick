# backend\workers\schedule_worker.py

import logging
from datetime import datetime
from PySide6.QtCore import QThread, Signal
from backend.services.schedule.schedule_service import ScheduleService

logger = logging.getLogger("minikick.schedule_worker")

class ScheduleWorker(QThread):
    schedule_triggered = Signal(object, object)

    def __init__(self, service: ScheduleService, parent=None):
        super().__init__(parent)
        self.service = service
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False

    def run(self) -> None:
        logger.info("[ScheduleWorker] Worker started.")
        while self._is_running:
            try:
                self._check_and_execute_schedules()
            except Exception as e:
                logger.error("[ScheduleWorker] Error checking schedules: %s", e)

            for _ in range(100):
                if not self._is_running:
                    break
                self.msleep(100)

        logger.info("[ScheduleWorker] Worker stopped.")

    def _check_and_execute_schedules(self) -> None:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        today_date_str = now.strftime("%Y-%m-%d")

        schedules = self.service.get_all_schedules()
        for sched in schedules:
            if not sched.get("is_active"):
                continue

            sched_date = sched.get("date_str", "")
            if sched_date and sched_date != today_date_str:
                continue

            time_str = sched.get("time_str", "")
            if time_str != current_time_str:
                continue

            last_date = sched.get("last_executed_date", "")
            if last_date == today_date_str:
                continue

            self.service.schedule_storage.update_last_executed(sched["id"], today_date_str)
            self.service.toggle_schedule(sched["id"], False)
            sched["last_executed_date"] = today_date_str
            sched["is_active"] = False

            logger.info("[ScheduleWorker] Triggering date schedule '%s' for %s at %s",
                        sched.get("name"), today_date_str, current_time_str)
            result = self.service.apply_schedule(sched)
            self.schedule_triggered.emit(sched, result)
