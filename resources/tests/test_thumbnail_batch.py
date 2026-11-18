# resources\tests\test_thumbnail_batch.py
"""Pruebas de la recarga de miniaturas en lote: no bloquea la UI y aplica los resultados."""

from PySide6.QtCore import QCoreApplication, QElapsedTimer
from PySide6.QtGui import QColor, QImage

from backend.services.rewards.rewards_service import RewardsService
from backend.services.rewards.thumbnail_service import ThumbnailBatchGenerator


class _FakeStorage:
    def __init__(self, data):
        self.data = data
        self.saved = 0

    def load_all(self):
        return self.data

    def save_all(self, data):
        self.data = data
        self.saved += 1


def _wait(cond, timeout_ms=15000):
    t = QElapsedTimer()
    t.start()
    while not cond() and t.elapsed() < timeout_ms:
        QCoreApplication.processEvents()
    return cond()


def _make_files(tmp_path):
    img = QImage(300, 200, QImage.Format.Format_RGB32)
    img.fill(QColor("red"))
    png = tmp_path / "a.png"
    img.save(str(png))
    bad_video = tmp_path / "broken.mp4"
    bad_video.write_bytes(b"not a video")
    audio = tmp_path / "s.mp3"
    audio.write_bytes(b"x")
    return str(png), str(bad_video), str(audio)


def test_batch_finishes_without_blocking_and_reports_every_file(qapp, tmp_path):
    png, bad_video, audio = _make_files(tmp_path)
    done = []
    gen = ThumbnailBatchGenerator([png, bad_video, audio, png])
    gen.finished.connect(done.append)
    gen.start()
    assert not done  # start() no ejecuta nada de forma síncrona
    assert _wait(lambda: bool(done))
    results = done[0]
    assert set(results) == {png, bad_video, audio}
    assert results[png] and results[bad_video] is None and results[audio] is None


def test_service_reload_applies_results_and_rejects_reentry(qapp, tmp_path):
    png, bad_video, _ = _make_files(tmp_path)
    storage = _FakeStorage({
        "kick:a": {"filepath": png, "thumbnail_bytes": b"old"},
        "kick:b": {"filepath": bad_video},
    })
    service = RewardsService(storage, overlay_server=None)
    done = []
    assert service.reload_thumbnails(done.append) is True
    assert service.reload_thumbnails(done.append) is False
    assert _wait(lambda: bool(done))
    assert done == [1]
    assert storage.data["kick:a"]["thumbnail_bytes"] not in (None, b"old")
    assert storage.data["kick:b"]["thumbnail_bytes"] is None
    assert storage.saved == 1
    assert service.reload_thumbnails(lambda _n: None) is True  # se puede volver a ejecutar
