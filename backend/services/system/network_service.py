# backend\services\system\network_service.py

import random
from PySide6.QtCore import QObject, Signal, QTimer, Slot
from backend.workers.network_worker import NetworkWorker

class NetworkService(QObject):
    results_updated = Signal(object)
    history_updated = Signal(object, object, object, object, object, object, object)
    checking_started = Signal()

    _DEFAULT_SERVICES = {
        "internet": 35.0,
        "kick": 45.0,
        "chat_websocket": 40.0,
        "overlay": 2.0,
        "youtube": 30.0
    }

    def __init__(self, overlay_port=8090, check_interval_ms=60000):
        super().__init__()
        self.overlay_port = overlay_port
        self.check_interval_ms = check_interval_ms
        self.worker = None

        self.history_by_service = {
            key: [default_val] * 50 for key, default_val in self._DEFAULT_SERVICES.items()
        }
        self.current_latencies = {
            key: default_val for key, default_val in self._DEFAULT_SERVICES.items()
        }
        self.avg_latencies = {
            key: default_val for key, default_val in self._DEFAULT_SERVICES.items()
        }
        self.max_latencies = {
            key: default_val for key, default_val in self._DEFAULT_SERVICES.items()
        }
        self.min_latencies = {
            key: default_val for key, default_val in self._DEFAULT_SERVICES.items()
        }
        self.jitter_by_service = {
            key: 0.0 for key in self._DEFAULT_SERVICES.keys()
        }
        self.stability_by_service = {
            key: "optimal" for key in self._DEFAULT_SERVICES.keys()
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

    def _recalculate_stats(self, key: str):
        active_points = [p for p in self.history_by_service[key] if p > 0]
        if active_points:
            self.avg_latencies[key] = sum(active_points) / len(active_points)
            self.max_latencies[key] = max(active_points)
            self.min_latencies[key] = min(active_points)
            
            recent = active_points[-15:]
            if len(recent) > 1:
                avg_recent = sum(recent) / len(recent)
                variance = sum((x - avg_recent) ** 2 for x in recent) / len(recent)
                self.jitter_by_service[key] = variance ** 0.5
            else:
                self.jitter_by_service[key] = 0.0

            curr = self.current_latencies.get(key, self.avg_latencies[key])
            jit = self.jitter_by_service[key]
            if curr <= 0 or curr > 800:
                self.stability_by_service[key] = "poor"
            elif curr < 120 and jit < 25:
                self.stability_by_service[key] = "optimal"
            elif curr < 300 and jit < 60:
                self.stability_by_service[key] = "good"
            else:
                self.stability_by_service[key] = "fair"

    def _emit_history(self):
        self.history_updated.emit(
            self.history_by_service.copy(),
            self.current_latencies.copy(),
            self.avg_latencies.copy(),
            self.max_latencies.copy(),
            self.min_latencies.copy(),
            self.jitter_by_service.copy(),
            self.stability_by_service.copy()
        )

    @Slot(object)
    def handle_results(self, results):
        self.last_results = results
        self.results_updated.emit(results)

        for key, res in results.items():
            if key not in self.history_by_service:
                self.history_by_service[key] = [35.0] * 50

            if res["status"] in ["online", "warning"]:
                latency = res["latency"]
                if latency > 0:
                    self.current_latencies[key] = float(latency)
                    self.history_by_service[key].pop(0)
                    self.history_by_service[key].append(float(latency))
                    self._recalculate_stats(key)
            elif res["status"] == "offline":
                self.current_latencies[key] = -1.0
                self.stability_by_service[key] = "poor"

        self._emit_history()

    def _update_simulation(self):
        for key in list(self.history_by_service.keys()):
            last_val = self.history_by_service[key][-1]
            max_noise = 0.8 if key == "overlay" else 3.5
            noise = random.uniform(-max_noise, max_noise)
            target = self.current_latencies.get(key, last_val)
            if target <= 0:
                target = last_val
            drift_correction = (target - last_val) * 0.1
            min_bound = 1.0 if key == "overlay" else 5.0
            new_val = max(min_bound, min(999.0, last_val + noise + drift_correction))

            self.history_by_service[key].pop(0)
            self.history_by_service[key].append(new_val)
            self._recalculate_stats(key)

        self._emit_history()
