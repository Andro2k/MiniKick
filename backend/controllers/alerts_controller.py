# backend\controllers\alerts_controller.py

import logging
from PySide6.QtCore import QObject, Slot, QUrl
from PySide6.QtGui import QGuiApplication, QDesktopServices
from backend.models import AlertConfig

logger = logging.getLogger("minikick.controllers.alerts")

class AlertsController(QObject):
    def __init__(self, view=None, service=None, toast_manager=None, i18n=None, browser_service=None):
        super().__init__()
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.i18n = i18n
        self.browser_service = browser_service
        self._view_connected = False
        self._previous_enabled: dict[tuple[str, str], bool] = {}
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def _connect_signals(self):
        if not self.view or self._view_connected:
            return
        self._view_connected = True
        self.view.config_changed.connect(self._handle_config_changed)
        self.view.test_alert_requested.connect(self._handle_test_alert)
        self.view.copy_url_requested.connect(self._handle_copy_url)
        self.view.open_browser_requested.connect(self._handle_open_browser)
        self.view.view_shown.connect(self.load_initial_data)

    def load_initial_data(self):
        if not self.service or not self.view:
            return
        configs = None
        if hasattr(self.service, "load_all_configs"):
            try:
                res = self.service.load_all_configs()
                if isinstance(res, (dict, list)):
                    configs = res
            except Exception:
                pass
        if configs is None and hasattr(self.service, "storage") and hasattr(self.service.storage, "load_all"):
            configs = self.service.storage.load_all()
        if configs:
            self.view.populate_configs(configs)
            items = configs.items() if isinstance(configs, dict) else [((c.platform, c.alert_type), c) for c in configs]
            for key, cfg in items:
                plat = key[0] if isinstance(key, tuple) else getattr(cfg, "platform", None)
                atype = key[1] if isinstance(key, tuple) else getattr(cfg, "alert_type", None)
                if plat and atype:
                    self._previous_enabled[(plat, atype)] = bool(getattr(cfg, "enabled", True))

    @Slot(object)
    def _handle_config_changed(self, config: AlertConfig):
        if not self.service:
            return
        logger.info(
            "[User Action] Updated alert config: platform='%s', type='%s', enabled=%s, duration=%sms",
            config.platform, config.alert_type, config.enabled, config.duration_ms
        )
        self.service.save_config(config)

        key = (config.platform, config.alert_type)
        prev_enabled = self._previous_enabled.get(key, True)
        self._previous_enabled[key] = bool(config.enabled)

        if self.toast and self.i18n:
            if prev_enabled != config.enabled:
                event_name = self.i18n.get(f"alerts.events.{config.alert_type}")
                if config.enabled:
                    title = self.i18n.get("alerts.status.enabled_title")
                    msg = self.i18n.get("alerts.status.enabled_msg").replace("{event}", event_name)
                    state = "success"
                else:
                    title = self.i18n.get("alerts.status.disabled_title")
                    msg = self.i18n.get("alerts.status.disabled_msg").replace("{event}", event_name)
                    state = "warning"
                self.toast.show_toast(
                    title=title,
                    message=msg,
                    state=state,
                    tag=f"alert_{config.platform}_{config.alert_type}"
                )
            else:
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
            logger.info("[User Action] Opening alerts overlay in browser: %s", url)
            if self.browser_service and hasattr(self.browser_service, "open_url"):
                self.browser_service.open_url(url)
            else:
                QDesktopServices.openUrl(QUrl(url))
