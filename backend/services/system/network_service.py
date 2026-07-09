# backend/services/system/network_service.py

import random
from PySide6.QtCore import QObject, Signal, QTimer, Slot
from frontend.workers.network_worker import NetworkWorker

class NetworkService(QObject):
    results_updated = Signal(dict)
    history_updated = Signal(list, float, float, float)
    checking_started = Signal()

    def __init__(self, overlay_port=8090, check_interval_ms=60000):
        super().__init__()
        self.overlay_port = overlay_port
        self.check_interval_ms = check_interval_ms
        self.worker = None

        self.latency_history = [35.0] * 50
        self.current_latency = 35.0
        self.avg_latency = 35.0
        self.max_latency = 35.0
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

        latencies = []
        for key, info in results.items():
            if key != "overlay" and info["status"] == "online" and info["latency"] > 0:
                latencies.append(info["latency"])

        if latencies:
            avg_lat = sum(latencies) / len(latencies)
            self.add_real_measurement(avg_lat)

    def add_real_measurement(self, latency: float):
        self.current_latency = latency
        self.latency_history.pop(0)
        self.latency_history.append(float(latency))
        self._calculate_stats()
        self.history_updated.emit(
            self.latency_history.copy(),
            self.current_latency,
            self.avg_latency,
            self.max_latency
        )

    def _update_simulation(self):
        last_val = self.latency_history[-1]
        noise = random.uniform(-4.0, 4.0)
        drift_correction = (self.current_latency - last_val) * 0.1
        new_val = max(5.0, min(999.0, last_val + noise + drift_correction))

        self.latency_history.pop(0)
        self.latency_history.append(new_val)
        self._calculate_stats()
        self.history_updated.emit(
            self.latency_history.copy(),
            self.current_latency,
            self.avg_latency,
            self.max_latency
        )

    def _calculate_stats(self):
        active_points = [p for p in self.latency_history if p > 0]
        if active_points:
            self.avg_latency = sum(active_points) / len(active_points)
            self.max_latency = max(active_points)
