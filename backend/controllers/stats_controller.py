# backend\controllers\stats_controller.py
"""Controlador del módulo de estadísticas."""

import datetime
import logging
from PySide6.QtCore import QObject, QTimer, Slot

logger = logging.getLogger("minikick.controllers.stats")

_LIVE_REFRESH_MS = 3000


class StatsController(QObject):
    """Une la vista de estadísticas con el servicio y los top chatters del widget en vivo."""

    def __init__(self, view, service, widget_service=None, widgets_controller=None,
                 flush_pending=None, toast_manager=None, i18n=None):
        super().__init__()
        self.view = None
        self.service = service
        self.widget_service = widget_service
        self.toast = toast_manager
        self.i18n = i18n
        self._flush_pending = flush_pending
        self._widgets_controller = None
        self._period = "today"
        self._chatters_date = datetime.date.today().strftime("%Y-%m-%d")
        self._live_timer = QTimer(self)
        self._live_timer.setSingleShot(True)
        self._live_timer.setInterval(_LIVE_REFRESH_MS)
        self._live_timer.timeout.connect(self.refresh)
        self.widgets_controller = widgets_controller
        if view is not None:
            self.attach_view(view)

    @property
    def widgets_controller(self):
        return self._widgets_controller

    @widgets_controller.setter
    def widgets_controller(self, controller):
        if self._widgets_controller is controller:
            return
        if self._widgets_controller is not None:
            for signal, slot in (("chatters_updated", self._on_chatters_updated),
                                 ("widget_status_changed", self._on_widget_status_changed)):
                try:
                    getattr(self._widgets_controller, signal).disconnect(slot)
                except (AttributeError, RuntimeError, TypeError):
                    pass
        self._widgets_controller = controller
        if controller is not None:
            if hasattr(controller, "chatters_updated"):
                controller.chatters_updated.connect(self._on_chatters_updated)
            if hasattr(controller, "widget_status_changed"):
                controller.widget_status_changed.connect(self._on_widget_status_changed)

    def attach_view(self, view) -> None:
        self.view = view
        view.period_changed.connect(self._on_period_changed)
        view.chatters_date_changed.connect(self._on_chatters_date_changed)
        view.activate_chatters_requested.connect(self._on_activate_chatters_requested)
        self.refresh()
        self._init_chatters()

    def request_live_refresh(self) -> None:
        """Pide repintar con un retardo: agrupa ráfagas de mensajes y solo actúa si la vista está visible."""
        if self.view is not None and self.view.isVisible() and not self._live_timer.isActive():
            self._live_timer.start()

    @Slot()
    def refresh(self) -> None:
        if self.view is None:
            return
        try:
            if self._flush_pending is not None:
                self._flush_pending()
            self.view.render_snapshot(self.service.build_snapshot(self._period))
        except Exception:
            logger.exception("[Stats] Error building snapshot for period '%s'.", self._period)

    @Slot(str)
    def _on_period_changed(self, period: str) -> None:
        self._period = period
        self.refresh()

    def _today(self) -> str:
        return datetime.date.today().strftime("%Y-%m-%d")

    def _chatters_active(self) -> bool:
        if self.widget_service is not None and hasattr(self.widget_service, "get_widget"):
            widget = self.widget_service.get_widget("chatters")
            return bool(widget.get("is_active", True)) if widget else True
        return True

    def _init_chatters(self) -> None:
        if self.view is None:
            return
        dates = self.widget_service.get_available_chatter_dates() if self.widget_service else []
        self.view.populate_chatter_dates(dates)
        self._chatters_date = self._today()
        self.view.set_chatters_widget_active(self._chatters_active())
        self.load_top_chatters(self._chatters_date)

    def load_top_chatters(self, date_str: str | None = None) -> list[dict]:
        date_str = date_str or self._today()
        live = getattr(self._widgets_controller, "_chatters_counts", None)
        if date_str == self._today() and live:
            chatters = sorted(live.values(), key=lambda c: int(c.get("count", 0)), reverse=True)
        elif self.widget_service is not None:
            chatters = list(self.widget_service.load_daily_chatters(date_str).values())
        else:
            chatters = []
        if self.view is not None:
            total = sum(int(c.get("count", 0)) for c in chatters)
            self.view.render_top_chatters(chatters, total_messages=total)
        return chatters

    @Slot(str)
    def _on_chatters_date_changed(self, date_str: str) -> None:
        self._chatters_date = date_str
        self.load_top_chatters(date_str)

    @Slot()
    def _on_chatters_updated(self) -> None:
        if self._chatters_date == self._today():
            self.load_top_chatters(self._chatters_date)

    @Slot(str, bool)
    def _on_widget_status_changed(self, widget_id: str, is_active: bool) -> None:
        if widget_id == "chatters" and self.view is not None:
            self.view.set_chatters_widget_active(is_active)

    @Slot()
    def _on_activate_chatters_requested(self) -> None:
        controller = self._widgets_controller
        if controller is None or not hasattr(controller, "set_widget_active"):
            return
        if controller.set_widget_active("chatters", True):
            self.view.set_chatters_widget_active(self._chatters_active())
            self.load_top_chatters(self._today())
            if self.toast and self.i18n:
                self.toast.show_toast(
                    title=self.i18n.get("dashboard.chatters.toast_activated_title"),
                    message=self.i18n.get("dashboard.chatters.toast_activated_desc"),
                    state="success",
                    tag="widget_chatters_activated",
                )
