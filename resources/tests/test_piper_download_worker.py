# resources\tests\test_piper_download_worker.py

import threading

from backend.services.chat.piper_manager import PiperVoiceDownloadWorker


class _FakeManager:
    def __init__(self, ok=True, steps=3, error=None):
        self.ok, self.steps, self.error = ok, steps, error

    def download_voice_sync(self, voice_id, progress_callback=None):
        if self.error:
            raise self.error
        for i in range(1, self.steps + 1):
            progress_callback(i * 100 // self.steps, float(i), float(self.steps))
        return self.ok


def _run(manager):
    progress, done = [], threading.Event()
    result = {}

    def on_finished(voice_id, ok, msg):
        result.update(voice_id=voice_id, ok=ok, msg=msg)
        done.set()

    worker = PiperVoiceDownloadWorker(
        "voz", manager, on_progress=lambda *a: progress.append(a), on_finished=on_finished
    )
    worker.start()
    assert done.wait(5)
    return progress, result


def test_success_reports_progress_and_finish():
    progress, result = _run(_FakeManager())
    assert [p[1] for p in progress] == [33, 66, 100]
    assert result == {"voice_id": "voz", "ok": True, "msg": ""}


def test_failure_and_exception():
    _, result = _run(_FakeManager(ok=False))
    assert result["ok"] is False and result["msg"] == "Download failed"
    _, result = _run(_FakeManager(error=OSError("sin red")))
    assert result["ok"] is False and result["msg"] == "sin red"


def test_cancel_stops_download():
    gate = threading.Event()

    class _Slow(_FakeManager):
        def download_voice_sync(self, voice_id, progress_callback=None):
            gate.wait(5)
            progress_callback(10, 1.0, 10.0)
            return True

    done, result = threading.Event(), {}
    worker = PiperVoiceDownloadWorker(
        "voz", _Slow(), on_finished=lambda v, ok, m: (result.update(ok=ok, msg=m), done.set())
    )
    worker.start()
    worker.cancel()
    gate.set()
    assert done.wait(5)
    assert result["ok"] is False and "cancelled" in result["msg"]


def test_cancel_reports_cancelled_when_manager_swallows_the_interruption():
    gate = threading.Event()

    class _Swallowing(_FakeManager):
        def download_voice_sync(self, voice_id, progress_callback=None):
            gate.wait(5)
            try:
                progress_callback(10, 1.0, 10.0)
            except InterruptedError:
                return False
            return True

    done, result = threading.Event(), {}
    worker = PiperVoiceDownloadWorker(
        "voz", _Swallowing(), on_finished=lambda v, ok, m: (result.update(ok=ok, msg=m), done.set())
    )
    worker.start()
    worker.cancel()
    gate.set()
    assert done.wait(5)
    assert result == {"ok": False, "msg": "Download cancelled by user"}
