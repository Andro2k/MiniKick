import queue
import threading
import pyttsx3


class TTSManager:
    """
    Manages Text-To-Speech in a dedicated background thread.

    pyttsx3 has a known bug where runAndWait() corrupts the engine's internal
    state after the first call on many systems. The safest fix is to
    reinitialize the engine for every message inside a dedicated thread so
    the main thread is never blocked.
    """

    def __init__(self, rate: int = 150):
        self.rate = rate
        self.queue: queue.Queue[str | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def say(self, text: str) -> None:
        """Enqueue a message to be spoken."""
        if text and text.strip():
            self.queue.put(text.strip())

    def stop(self) -> None:
        """Signal the worker thread to exit cleanly."""
        self.queue.put(None)
        self._thread.join(timeout=5)

    # ------------------------------------------------------------------
    # Internal worker
    # ------------------------------------------------------------------

    def _worker(self) -> None:
        """Dedicated thread: pulls messages and speaks them one by one."""
        while True:
            text = self.queue.get()

            # Sentinel value → clean shutdown
            if text is None:
                self.queue.task_done()
                break

            self._speak(text)
            self.queue.task_done()

    def _speak(self, text: str) -> None:
        """
        Reinitialize the engine per message.
        This avoids the runAndWait() state corruption bug in pyttsx3.
        """
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"[TTS] Error al hablar: {e}")