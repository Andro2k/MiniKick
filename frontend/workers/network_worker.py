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
        results = {}
        
        status_net, lat_net = self.check_service("internet", "https://www.google.com")
        results["internet"] = {"status": status_net, "latency": lat_net}
        
        status_kick, lat_kick = self.check_service("kick", "https://kick.com")
        results["kick"] = {"status": status_kick, "latency": lat_kick}
        
        status_spot, lat_spot = self.check_service("spotify", "https://api.spotify.com")
        results["spotify"] = {"status": status_spot, "latency": lat_spot}
        
        status_over, lat_over = self.check_service("overlay", "127.0.0.1", is_url=False, expected_port=self.overlay_port)
        results["overlay"] = {"status": status_over, "latency": lat_over}
        
        status_yt, lat_yt = self.check_service("youtube", "https://www.youtube.com")
        results["youtube"] = {"status": status_yt, "latency": lat_yt}
        
        status_ws, lat_ws = self.check_service("chat_websocket", "ws-us2.pusher.com", is_url=False, expected_port=443)
        results["chat_websocket"] = {"status": status_ws, "latency": lat_ws}
        
        self.result_ready.emit(results)
