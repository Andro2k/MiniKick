# frontend\window\shutdown.py

from typing import Callable, Sequence

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
