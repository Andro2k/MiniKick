# resources\tests\test_bug_report_view.py
"""Pruebas de la vista de reporte de errores y su controlador."""

import pytest
from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtWidgets import QApplication, QBoxLayout

from backend.controllers.bug_report_controller import BugReportController
from backend.services.logs.logs_service import LogService
from frontend.views.bug_report_view import BugReportView


class KeyTranslations:
    @staticmethod
    def get(key, default="", **kwargs):
        return default or key


class FakeWorker(QObject):
    report_completed = Signal(bool, str)
    finished = Signal()
    instances = []

    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs
        FakeWorker.instances.append(self)

    def start(self):
        pass


class FakeToast:
    def __init__(self):
        self.shown = []

    def show_toast(self, title, msg, kind):
        self.shown.append(kind)


class FakeLogService:
    log_dir = "."

    def read_app_log_preview(self):
        return {"path": "x", "exists": True, "size": 2048, "total_lines": 2, "shown_lines": 2,
                "text": "[2026-11-15 12:00:00] [INFO] arranque\n[2026-11-15 12:00:01] [ERROR] fallo"}


_VIEWS = []


@pytest.fixture(autouse=True)
def _dispose_views(qapp):
    """Destruye las vistas al terminar cada prueba, con sus eventos pendientes ya procesados."""
    yield
    for view in _VIEWS:
        view.deleteLater()
    _VIEWS.clear()
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _setup(qapp):
    FakeWorker.instances.clear()
    view = BugReportView(KeyTranslations())
    _VIEWS.append(view)
    toast = FakeToast()
    controller = BugReportController(None, worker_class=FakeWorker, log_service=FakeLogService(),
                                     toast_manager=toast, i18n=KeyTranslations())
    controller.attach_view(view)
    view._controller = controller
    return view, controller, toast


def test_empty_description_is_not_sent(qapp):
    view, controller, _ = _setup(qapp)
    view.btn_send.click()
    assert not FakeWorker.instances
    assert not view.lbl_error.isHidden()


def test_submit_sends_form_values_and_locks_the_form(qapp):
    view, controller, _ = _setup(qapp)
    view.txt_username.setText("@streamer")
    view.txt_desc.setPlainText("Algo falla")
    view._on_severity_selected("Urgent")
    view.btn_send.click()

    assert len(FakeWorker.instances) == 1
    kwargs = FakeWorker.instances[0].kwargs
    assert (kwargs["username"], kwargs["description"], kwargs["severity"]) == ("@streamer", "Algo falla", "Urgent")
    assert not view.btn_send.isEnabled()
    view.btn_send.click()
    assert len(FakeWorker.instances) == 1


def test_success_resets_form_and_failure_keeps_it(qapp):
    view, controller, toast = _setup(qapp)
    view.txt_desc.setPlainText("Algo falla")
    view.btn_send.click()
    FakeWorker.instances[0].report_completed.emit(False, "boom")
    assert view.btn_send.isEnabled() and view.txt_desc.toPlainText() == "Algo falla"
    assert view.lbl_error.text() == "boom"

    view.btn_send.click()
    FakeWorker.instances[1].report_completed.emit(True, "ok")
    assert view.txt_desc.toPlainText() == "" and toast.shown == ["success"]


def test_rows_stack_when_the_window_is_narrow(qapp):
    view, _, _ = _setup(qapp)
    view.resize(1200, 800)
    view.show()
    qapp.processEvents()
    assert all(r.direction() == QBoxLayout.Direction.LeftToRight for r in view._flex_rows)
    view.resize(700, 800)
    qapp.processEvents()
    assert all(r.direction() == QBoxLayout.Direction.TopToBottom for r in view._flex_rows)
    view.resize(1200, 800)
    qapp.processEvents()
    assert all(r.direction() == QBoxLayout.Direction.LeftToRight for r in view._flex_rows)


def test_log_preview_is_shown_and_follows_the_include_logs_checkbox(qapp):
    view, _, _ = _setup(qapp)
    assert "[ERROR] fallo" in view.log_panel.viewer.toPlainText()
    assert view.log_panel.viewer.isEnabled()
    view.chk_logs.setChecked(False)
    assert not view.log_panel.viewer.isEnabled()
    view.chk_logs.setChecked(True)
    assert view.log_panel.viewer.isEnabled()


def test_log_service_preview_returns_only_the_tail(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    service = LogService()
    assert service.read_app_log_preview()["exists"] is False
    with open(service.get_app_log_path(), "w", encoding="utf-8") as f:
        f.write("".join(f"[2026-11-15 12:00:00] [INFO] linea {i}\n" for i in range(500)))
    preview = service.read_app_log_preview(max_lines=50)
    assert preview["exists"] and preview["total_lines"] == 500 and preview["shown_lines"] == 50
    assert preview["text"].splitlines()[-1].endswith("linea 499")
