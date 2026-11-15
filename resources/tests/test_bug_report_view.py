# resources\tests\test_bug_report_view.py
"""Pruebas de la vista de reporte de errores y su controlador."""

from PySide6.QtCore import QObject, Signal

from backend.controllers.bug_report_controller import BugReportController
from frontend.views.bug_report_view import BugReportView


class KeyTranslations:
    @staticmethod
    def get(key, default=""):
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


def _setup(qapp):
    FakeWorker.instances.clear()
    view = BugReportView(KeyTranslations())
    toast = FakeToast()
    controller = BugReportController(None, worker_class=FakeWorker, toast_manager=toast, i18n=KeyTranslations())
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
