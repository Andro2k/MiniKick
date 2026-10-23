"""Non-blocking shutdown coordination for Qt worker threads."""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass
from typing import Callable, Iterable

from PySide6.QtCore import QObject, QThread, QTimer


@dataclass
class _PendingWorker:
    name: str
    worker: QThread
    started_at: float
    warning_after_seconds: float
    warned: bool = False


@dataclass
class _WorkerBatch:
    workers: list[_PendingWorker]
    on_finished: Callable[[], None] | None


class WorkerShutdownCoordinator(QObject):
    """Request worker termination together and poll without blocking Qt's UI loop."""

    _SIGNAL_NAMES = (
        "auth_success",
        "auth_error",
        "connection_success",
        "connection_lost",
        "connection_restored",
        "error_occurred",
        "message_received",
        "reward_redeemed",
        "rewards_fetched",
        "alert_received",
        "highlights_fetched",
        "poll_updated",
        "poll_deleted",
        "pinned_created",
        "pinned_deleted",
        "schedule_triggered",
        "post_message_requested",
        "play_pause_pressed",
        "skip_pressed",
        "stop_pressed",
    )
    _WARNING_AFTER_SECONDS = 10.0

    def __init__(
        self,
        parent: QObject,
        logger,
        retiring_workers: set[QThread],
    ) -> None:
        super().__init__(parent)
        self._logger = logger
        self._retiring_workers = retiring_workers
        self._batches: list[_WorkerBatch] = []
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._poll_workers)

    def stop_workers(
        self,
        workers: Iterable[tuple[str, QThread | None]],
        on_finished: Callable[[], None] | None = None,
        warning_after_seconds: float = _WARNING_AFTER_SECONDS,
    ) -> None:
        """Request all workers to stop, then invoke the callback once they finish."""
        pending: list[_PendingWorker] = []
        seen_workers: set[int] = set()

        for name, worker in workers:
            if worker is None or id(worker) in seen_workers:
                continue
            seen_workers.add(id(worker))
            try:
                if not worker.isRunning():
                    self._delete_worker(worker)
                    continue
            except RuntimeError:
                self._logger.warning(
                    "[Worker] Could not inspect '%s'; treating it as stopped.",
                    name,
                    exc_info=True,
                )
                self._delete_worker(worker)
                continue

            self._retiring_workers.add(worker)
            self._disconnect_worker_signals(worker, name)
            self._request_stop(worker, name)
            pending.append(
                _PendingWorker(
                    name,
                    worker,
                    time.monotonic(),
                    warning_after_seconds,
                )
            )

        if not pending:
            if on_finished is not None:
                QTimer.singleShot(0, lambda: self._run_callback(on_finished))
            return

        self._batches.append(_WorkerBatch(pending, on_finished))
        if not self._timer.isActive():
            self._timer.start()

    def _disconnect_worker_signals(self, worker: QThread, name: str) -> None:
        for signal_name in self._SIGNAL_NAMES:
            signal = getattr(worker, signal_name, None)
            if signal is None:
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    signal.disconnect()
            except (RuntimeError, TypeError):
                self._logger.debug(
                    "[Worker] Signal '%s' on '%s' was already disconnected.",
                    signal_name,
                    name,
                    exc_info=True,
                )

    def _request_stop(self, worker: QThread, name: str) -> None:
        self._logger.info("[Worker] Requesting stop for '%s'.", name)
        for method_name in ("stop", "requestInterruption", "quit"):
            method = getattr(worker, method_name, None)
            if method is None:
                continue
            try:
                method()
            except RuntimeError:
                self._logger.warning(
                    "[Worker] Failed to call %s() for '%s'.",
                    method_name,
                    name,
                    exc_info=True,
                )

    def _poll_workers(self) -> None:
        remaining_batches: list[_WorkerBatch] = []
        completed_callbacks: list[Callable[[], None]] = []
        now = time.monotonic()

        for batch in self._batches:
            pending: list[_PendingWorker] = []
            for entry in batch.workers:
                try:
                    is_running = entry.worker.isRunning()
                except RuntimeError:
                    self._logger.warning(
                        "[Worker] Could not inspect '%s' while stopping.",
                        entry.name,
                        exc_info=True,
                    )
                    is_running = False

                if is_running:
                    elapsed = now - entry.started_at
                    if elapsed >= entry.warning_after_seconds and not entry.warned:
                        self._logger.warning(
                            "[Worker] '%s' is still running after %.1f seconds; "
                            "waiting for cooperative shutdown.",
                            entry.name,
                            elapsed,
                        )
                        entry.warned = True
                    pending.append(entry)
                    continue

                self._logger.info(
                    "[Worker] '%s' stopped in %.1f ms.",
                    entry.name,
                    (now - entry.started_at) * 1000,
                )
                self._retiring_workers.discard(entry.worker)
                self._delete_worker(entry.worker)

            if pending:
                batch.workers = pending
                remaining_batches.append(batch)
            elif batch.on_finished is not None:
                completed_callbacks.append(batch.on_finished)

        self._batches = remaining_batches
        if not self._batches:
            self._timer.stop()
        for callback in completed_callbacks:
            self._run_callback(callback)

    def _run_callback(self, callback: Callable[[], None]) -> None:
        try:
            callback()
        except Exception:
            self._logger.exception("[Worker] Shutdown completion callback failed.")

    def _delete_worker(self, worker: QThread) -> None:
        self._retiring_workers.discard(worker)
        try:
            worker.deleteLater()
        except RuntimeError:
            self._logger.debug(
                "[Worker] Worker object was already deleted.",
                exc_info=True,
            )
