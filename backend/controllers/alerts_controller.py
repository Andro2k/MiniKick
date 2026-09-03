# backend\controllers\alerts_controller.py

import logging
from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QGuiApplication
from backend.models.alert_models import AlertConfig

logger = logging.getLogger("minikick.controllers.alerts")

class AlertsController(QObject):
    def __init__(self, view=None, service=None, toast_manager=None, i18n=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.i18n = i18n
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def _connect_signals(self):
        self.view.config_changed.connect(self._handle_config_changed)
        self.view.test_alert_requested.connect(self._handle_test_alert)
        self.view.copy_url_requested.connect(self._handle_copy_url)
        self.view.open_browser_requested.connect(self._handle_open_browser)
        self.view.view_shown.connect(self.load_initial_data)

    def load_initial_data(self):
        if not self.service or not self.view:
            return
        configs = self.service.storage.load_all()
        self.view.populate_configs(configs)

    @Slot(object)
    def _handle_config_changed(self, config: AlertConfig):
        if not self.service:
            return
        logger.info(
            "[User Action] Updated alert config: platform='%s', type='%s', enabled=%s, duration=%sms",
            config.platform, config.alert_type, config.enabled, config.duration_ms
        )
        self.service.storage.save_config(config)
        if self.toast and self.i18n:
            self.toast.show_toast(
                title=self.i18n.get("alerts.status.saved_title"),
                message=self.i18n.get("alerts.status.saved_msg"),
                state="success",
                tag=f"alert_{config.platform}_{config.alert_type}"
            )

    @Slot(str, str)
    def _handle_test_alert(self, platform: str, alert_type: str):
        if not self.service:
            return
        logger.info("[User Action] Test alert requested: platform='%s', alert_type='%s'", platform, alert_type)
        self.service.trigger_test_alert(platform=platform, alert_type=alert_type)
        if self.toast and self.i18n:
            self.toast.show_toast(
                title=self.i18n.get("alerts.buttons.test"),
                message=self.i18n.get("alerts.buttons.test_sent"),
                state="info",
                tag=f"test_alert_{platform}_{alert_type}"
            )

    @Slot()
    def _handle_copy_url(self):
        if not self.view:
            return
        url = self.view.alerts_overlay_url
        if url:
            clipboard = QGuiApplication.clipboard()
            if clipboard:
                clipboard.setText(url)
            if self.toast and self.i18n:
                self.toast.show_toast(
                    title=self.i18n.get("alerts.overlay_card.copied_title"),
                    message=self.i18n.get("alerts.overlay_card.copied_msg"),
                    state="success",
                    tag="alert_overlay_copy"
                )

    @Slot()
    def _handle_open_browser(self):
        if not self.view:
            return
        url = self.view.alerts_overlay_url
        if url:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            logger.info("[User Action] Opening alerts overlay in default browser: %s", url)
            QDesktopServices.openUrl(QUrl(url))
