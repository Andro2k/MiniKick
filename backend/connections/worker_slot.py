# backend\connections\worker_slot.py

from typing import Callable

from PySide6.QtCore import QThread

from .worker_shutdown import WorkerShutdownCoordinator, is_worker_running


class WorkerSlot:
    def __init__(self, name: str, coordinator: WorkerShutdownCoordinator) -> None:
        self.name = name
        self._coordinator = coordinator
        self._worker: QThread | None = None

    @property
    def is_running(self) -> bool:
        return is_worker_running(self._worker)

    def start(self, factory: Callable[[], QThread]) -> bool:
        if self.is_running:
            return False
        self._worker = factory()
        self._worker.start()
        return True

    def detach(self) -> tuple[str, QThread | None]:
        worker, self._worker = self._worker, None
        return self.name, worker

    def stop(
        self,
        on_finished: Callable[[], None] | None = None,
        timeout_ms: int = 1500,
    ) -> None:
        self._coordinator.stop_workers(
            [self.detach()],
            on_finished=on_finished,
            warning_after_seconds=max(timeout_ms, 0) / 1000,
        )
