# frontend\workers\network_worker.py

import socket
import urllib.request
import urllib.error
import time
from PySide6.QtCore import QThread, Signal

class NetworkWorker(QThread):
    result_ready = Signal(dict)

    def __init__(self, overlay_port=8090, parent=None):
        super().__init__(parent)
        self.overlay_port = overlay_port

    def check_service(self, name: str, host_or_url: str, is_url: bool = True, expected_port: int = 80) -> tuple[str, int]:
        start_time = time.time()
        try:
            if is_url:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                req = urllib.request.Request(host_or_url, method='HEAD', headers=headers)
                try:
                    with urllib.request.urlopen(req, timeout=3.0) as response:
                        pass
                except urllib.error.HTTPError:
                    pass
                except urllib.error.URLError:
                    return "offline", -1
            else:
                with socket.create_connection((host_or_url, expected_port), timeout=3.0):
                    pass
            
            latency = int((time.time() - start_time) * 1000)
            status = "online"
            if latency > 800:
                status = "warning"
            return status, latency
        except Exception:
            return "offline", -1

    def run(self):
        from concurrent.futures import ThreadPoolExecutor
        results = {}
        
        services = [
            ("internet", "https://www.google.com", True, 80),
            ("kick", "https://kick.com", True, 80),
            ("spotify", "https://api.spotify.com", True, 80),
            ("overlay", "127.0.0.1", False, self.overlay_port),
            ("youtube", "https://www.youtube.com", True, 80),
            ("chat_websocket", "ws-us2.pusher.com", False, 443)
        ]
        
        with ThreadPoolExecutor(max_workers=len(services)) as executor:
            futures = {
                executor.submit(self.check_service, name, host, is_url, port): name
                for name, host, is_url, port in services
            }
            for future in futures:
                name = futures[future]
                try:
                    status, latency = future.result()
                    results[name] = {"status": status, "latency": latency}
                except Exception:
                    results[name] = {"status": "offline", "latency": -1}
                    
        self.result_ready.emit(results)
