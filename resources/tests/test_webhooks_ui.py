# resources\tests\test_webhooks_ui.py

from backend.config.toml_config_provider import TomlConfigProvider
from backend.config.webhook_endpoint_store import WebhookEndpointStore
from backend.controllers import WebhooksController
from backend.interfaces.i_webhooks import DeliveryResponse
from backend.services.system import TranslationService
from backend.services.webhooks import PingResult, WebhookManagementService
from frontend.dialogs import WebhookEndpointDialog
from frontend.views import WebhooksView
from resources.tests.test_webhook_endpoint_store import ReversibleCipher
from resources.tests.test_webhook_management_service import FakeSender, URL


def _service(tmp_path):
    store = WebhookEndpointStore(TomlConfigProvider(tmp_path / "config.toml"), ReversibleCipher())
    return WebhookManagementService(store, FakeSender(DeliveryResponse(status_code=204)))


def _dialog(qtbot=None, existing=None, validator=WebhookManagementService.validate_url):
    return WebhookEndpointDialog(
        TranslationService(), event_types=WebhookManagementService.event_types(),
        platforms=WebhookManagementService.platforms(), url_validator=validator, existing=existing,
    )


def test_dialog_save_requires_name_url_event_and_platform(qapp):
    dialog = _dialog()
    assert not dialog.btn_save.isEnabled()
    dialog.txt_name.setText("Alerts")
    dialog.txt_url.setText(URL)
    assert not dialog.btn_save.isEnabled()
    dialog.event_checks["follow"].setChecked(True)
    assert dialog.btn_save.isEnabled()
    data = dialog.get_data()
    assert data["events"] == ["follow"] and data["formatter"] == "discord" and data["hmac_secret"] == ""


def test_dialog_rejects_bad_url_and_warns_on_plain_http(qapp):
    dialog = _dialog()
    dialog.txt_url.setText("http://192.168.1.50/hook")
    assert not dialog.lbl_http_warning.isHidden()
    dialog.txt_url.setText("nope")
    assert dialog._url_error() == "invalid_url" and not dialog.lbl_url_error.isHidden()


def test_dialog_shows_ping_result(qapp):
    dialog = _dialog()
    dialog.set_ping_result(PingResult(ok=True, status_code=204, latency_ms=87))
    assert "204" in dialog.lbl_ping.text() and "87" in dialog.lbl_ping.text()
    dialog.set_ping_result(PingResult(ok=False, error="timeout"))
    assert "timeout" in dialog.lbl_ping.text()


def test_view_and_controller_list_edit_toggle_delete(qapp, tmp_path):
    service = _service(tmp_path)
    ep = service.save_endpoint({"name": "Alerts", "formatter": "discord", "target_url": URL, "events": ["follow"], "platforms": ["kick"]})
    view = WebhooksView(TranslationService())
    controller = WebhooksController(view, service)
    controller.load_initial_data()
    assert view.table.rowCount() == 1

    view.status_toggled.emit(ep.endpoint_id, False)
    assert service.get_endpoint(ep.endpoint_id).enabled is False

    view.search_text_changed.emit("zzz")
    assert view.table.rowCount() == 0
    view.search_text_changed.emit("")
    assert view.table.rowCount() == 1

    view.delete_requested.emit(ep.endpoint_id)
    assert service.list_endpoints() == [] and view.table.rowCount() == 0


def test_controller_save_failure_keeps_data_and_notifies(qapp, tmp_path):
    service = _service(tmp_path)
    toasts = []

    class Toast:
        def show_toast(self, **kwargs):
            toasts.append(kwargs["state"])

    controller = WebhooksController(WebhooksView(TranslationService()), service, toast_manager=Toast())
    controller._save({"name": "", "target_url": ""}, "webhooks.status.created", "webhooks.status.created_msg")
    assert toasts == ["danger"] and service.list_endpoints() == []
