# backend\controllers\network_controller.py

from PySide6.QtCore import QObject, Slot

class NetworkController(QObject):
    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        
        self.view.check_requested.connect(self.service.run_network_check)
        self.view.view_shown.connect(self.update_view_from_service)
        
        self.service.checking_started.connect(self.view.set_checking_state)
        self.service.results_updated.connect(self.view.update_status)
        self.service.history_updated.connect(self.view.graph.update_graph_data)
        
        self.update_view_from_service()
        
    @Slot()
    def update_view_from_service(self):
        if self.service.last_results:
            self.view.update_status(self.service.last_results)
        self.view.graph.update_graph_data(
            self.service.latency_history,
            self.service.current_latency,
            self.service.avg_latency,
            self.service.max_latency
        )
