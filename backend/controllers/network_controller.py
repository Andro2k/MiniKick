# backend\controllers\network_controller.py

import logging
from PySide6.QtCore import QObject, Slot

logger = logging.getLogger("minikick.controllers.network")

class NetworkController(QObject):
    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        if self.view is not None:
            self._connect_signals()

    def _connect_signals(self):
        if self.view:
            self.view.check_requested.connect(self._handle_manual_check)
            self.view.view_shown.connect(self.update_view_from_service)
            self.service.checking_started.connect(self.view.set_checking_state)
            self.service.results_updated.connect(self.view.update_status)
            self.service.history_updated.connect(self.view.graph.update_graph_data)
            self.update_view_from_service()

    @Slot()
    def _handle_manual_check(self):
        logger.info("[User Action] Manual network connectivity check requested")
        self.service.run_network_check()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
        
    @Slot()
    def update_view_from_service(self):
        if self.service.last_results:
            self.view.update_status(self.service.last_results)
        self.view.graph.update_graph_data(
            self.service.history_by_service,
            self.service.current_latencies,
            self.service.avg_latencies,
            self.service.max_latencies,
            getattr(self.service, "min_latencies", {}),
            getattr(self.service, "jitter_by_service", {}),
            getattr(self.service, "stability_by_service", {})
        )
