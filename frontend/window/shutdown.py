# frontend\window\shutdown.py

from typing import Callable, Sequence

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QApplication

from backend.connections import WorkerShutdownCoordinator

ShutdownStep = tuple[str, Callable[[], None]]


class ShutdownSequence:
    def __init__(
        self,
        logger,
        stop_workers: Callable[[Callable[[], None]], None],
        release_steps: Sequence[ShutdownStep],
        close_steps: Sequence[ShutdownStep],
        on_complete: Callable[[], None],
    ) -> None:
        self._logger = logger
        self._stop_workers = stop_workers
        self._release_steps = release_steps
        self._close_steps = close_steps
        self._on_complete = on_complete

    def run(self) -> None:
        self._logger.info("[Shutdown] Initiating application shutdown sequence...")
        self._stop_workers(self._finish)

    def _finish(self) -> None:
        self._run_steps(self._release_steps)
        self._logger.info("[Shutdown] Stopping TTS worker and overlay HTTP server...")
        self._run_steps(self._close_steps)
        self._logger.info("[Shutdown] Shutdown sequence completed.")
        self._on_complete()

    def _run_steps(self, steps: Sequence[ShutdownStep]) -> None:
        for label, action in steps:
            try:
                action()
            except Exception:
                self._logger.exception("[Shutdown] Failed to %s.", label)


class MainWindowShutdown:
    def __init__(self, window) -> None:
        self._window = window
        self._retiring_workers: set = set()
        self.worker_shutdown_coordinator = WorkerShutdownCoordinator(
            window,
            window.logger,
            self._retiring_workers,
        )
        self._sequence = ShutdownSequence(
            window.logger,
            stop_workers=self.stop_all_workers,
            release_steps=(
                ("clean up music_controller", lambda: window.music_controller.shutdown()),
                ("clean up widgets_controller", lambda: window.widgets_controller.cleanup()),
                ("stop the chat service", lambda: window.chat_service.shutdown()),
                ("clean up the chat controller", lambda: window.chat_controller.cleanup()),
            ),
            close_steps=(
                ("stop application services", lambda: window.container.shutdown()),
                ("flush pending log records", lambda: window.log_service.close()),
                ("close database resources", lambda: window.container.db_manager.cleanup()),
            ),
            on_complete=self._on_complete,
        )

    def force_quit(self) -> None:
        w = self._window
        w.window_state.save()
        w.hide()
        w._quit_requested = True
        self.cleanup()

    def cleanup(self) -> None:
        w = self._window
        if w._is_shutting_down:
            return
        w._is_shutting_down = True
        w.session_metrics.stop()
        if w.view_chat is not None:
            w.view_chat.close_floating_chat()
        self._sequence.run()

    def stop_workers_parallel(
        self,
        worker_map: list[tuple[str, QThread | None]],
        on_finished: Callable[[], None] | None = None,
        *,
        warning_after_ms: int = 10_000,
    ) -> None:
        self.worker_shutdown_coordinator.stop_workers(
            worker_map,
            on_finished=on_finished,
            warning_after_seconds=max(warning_after_ms, 0) / 1000,
        )

    def stop_all_workers(
        self,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        w = self._window
        slots = (
            w.media_keys.slot,
            w.whats_new.slot,
            *(chat.slot for chat in w.live_chats),
            *w.twitch.slots,
            *w.kick.slots,
            w._schedule_slot,
        )
        self.stop_workers_parallel(
            [slot.detach() for slot in slots],
            on_finished=on_finished,
        )

    def _on_complete(self) -> None:
        w = self._window
        w._cleanup_complete = True
        w.shutdown_finished.emit()
        if w._quit_requested:
            QTimer.singleShot(0, QApplication.quit)
