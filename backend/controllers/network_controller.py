# backend\controllers\network_controller.py

from PySide6.QtCore import QObject, Slot
from frontend.workers.network_worker import NetworkWorker

class NetworkController(QObject):
    def __init__(self, view, overlay_port=8090):
        super().__init__()
        self.view = view
        self.overlay_port = overlay_port
        self.worker = None
        
        self.view.check_requested.connect(self.run_network_check)
        self.view.view_shown.connect(self.run_network_check)
        
    @Slot()
    def run_network_check(self):
        try:
            if self.worker and self.worker.isRunning():
                return
        except RuntimeError:
            self.worker = None
            
        self.view.set_checking_state()
        
        self.worker = NetworkWorker(overlay_port=self.overlay_port)
        self.worker.result_ready.connect(self.handle_results)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self._clear_worker)
        self.worker.start()

    def _clear_worker(self):
        self.worker = None
        
    @Slot(dict)
    def handle_results(self, results):
        self.view.update_status(results)
