# backend/services/system/network_service.py

import random
from PySide6.QtCore import QObject, Signal, QTimer, Slot
from backend.workers.network_worker import NetworkWorker

class NetworkService(QObject):
    results_updated = Signal(dict)
    history_updated = Signal(dict, dict, dict, dict)
    checking_started = Signal()

    def __init__(self, overlay_port=8090, check_interval_ms=60000):
        super().__init__()
        self.overlay_port = overlay_port
        self.check_interval_ms = check_interval_ms
        self.worker = None

        self.history_by_service = {
            "internet": [35.0] * 50,
            "kick": [45.0] * 50
        }
        self.current_latencies = {
            "internet": 35.0,
            "kick": 45.0
        }
        self.avg_latencies = {
            "internet": 35.0,
            "kick": 45.0
        }
        self.max_latencies = {
            "internet": 35.0,
            "kick": 45.0
        }
        self.last_results = {}

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._update_simulation)
        self.sim_timer.start(1000)
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.run_network_check)
        self.check_timer.start(self.check_interval_ms)
        QTimer.singleShot(1000, self.run_network_check)

    @Slot()
    def run_network_check(self):
        try:
            if self.worker and self.worker.isRunning():
                return
        except RuntimeError:
            self.worker = None

        self.checking_started.emit()

        self.worker = NetworkWorker(overlay_port=self.overlay_port)
        self.worker.result_ready.connect(self.handle_results)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self._clear_worker)
        self.worker.start()

    def _clear_worker(self):
        self.worker = None

    @Slot(dict)
    def handle_results(self, results):
        self.last_results = results
        self.results_updated.emit(results)

        for key in ["internet", "kick"]:
            if key in results and results[key]["status"] in ["online", "warning"]:
                latency = results[key]["latency"]
                if latency > 0:
                    self.current_latencies[key] = float(latency)
                    self.history_by_service[key].pop(0)
                    self.history_by_service[key].append(float(latency))
                    
                    active_points = [p for p in self.history_by_service[key] if p > 0]
                    if active_points:
                        self.avg_latencies[key] = sum(active_points) / len(active_points)
                        self.max_latencies[key] = max(active_points)

        self.history_updated.emit(
            self.history_by_service.copy(),
            self.current_latencies.copy(),
            self.avg_latencies.copy(),
            self.max_latencies.copy()
        )

    def _update_simulation(self):
        for key in ["internet", "kick"]:
            last_val = self.history_by_service[key][-1]
            noise = random.uniform(-4.0, 4.0)
            drift_correction = (self.current_latencies[key] - last_val) * 0.1
            new_val = max(5.0, min(999.0, last_val + noise + drift_correction))

            self.history_by_service[key].pop(0)
            self.history_by_service[key].append(new_val)
            
            active_points = [p for p in self.history_by_service[key] if p > 0]
            if active_points:
                self.avg_latencies[key] = sum(active_points) / len(active_points)
                self.max_latencies[key] = max(active_points)

        self.history_updated.emit(
            self.history_by_service.copy(),
            self.current_latencies.copy(),
            self.avg_latencies.copy(),
            self.max_latencies.copy()
        )
