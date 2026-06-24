# backend\services\stream\overlay_server.py

import os
import json
import queue
import sys
import threading
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

def get_resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class OverlayRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/overlay":
            html_path = get_resource_path(os.path.join("assets", "overlays", "rewards.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Overlay HTML not found at: {html_path}")

        elif path == "/media":
            query = parse_qs(parsed.query)
            if "path" not in query:
                self.send_error(400, "Path not specified")
                return
                
            filepath = query["path"][0]
            if not os.path.exists(filepath):
                self.send_error(404, "Media file not found")
                return
                
            mime_type, _ = mimetypes.guess_type(filepath)
            
            try:
                self.send_response(200)
                self.send_header("Content-Type", mime_type or "application/octet-stream")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                with open(filepath, "rb") as f:
                    chunk_size = 1024 * 64 
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
            except Exception as e:
                try:
                    self.send_error(500, f"Internal error: {e}")
                except:
                    pass
                
        elif path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            client_queue = queue.Queue()
            self.server.manager.clients.append(client_queue)
            
            try:
                while True:
                    alert = client_queue.get()
                    if alert is None:
                        break
                    self.wfile.write(f"data: {json.dumps(alert)}\n\n".encode("utf-8"))
                    self.wfile.flush()
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
            except Exception:
                pass
            finally:
                if client_queue in self.server.manager.clients:
                    self.server.manager.clients.remove(client_queue)
        else:
            self.send_error(404, "Invalid endpoint")

    def log_message(self, format, *args):
        pass

class OverlayServerManager:
    def __init__(self, port=8090):
        self.port = port
        self.server = None
        self.thread = None
        self.clients = [] 

    def start(self):
        try:
            self.server = ThreadingHTTPServer(("127.0.0.1", self.port), OverlayRequestHandler)
            self.server.manager = self 
            
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            print(f"Overlay server active: http://localhost:{self.port}/overlay")
        except OSError as e:
            print(f"CRITICAL ERROR: Could not start Overlay server on port {self.port}.")
            print(f"Details: {e}")

    def trigger_alert(self, reward_name: str, config: dict):
        if isinstance(config, str):
            config = {"filepath": config, "volume": 1.0, "scale": 1.0, "pos_x": 0, "pos_y": 0}
            
        safe_path = urllib.parse.quote(config['filepath'])
        
        payload = {
            "reward": reward_name,
            "file_url": f"http://localhost:{self.port}/media?path={safe_path}",
            "volume": config.get("volume", 1.0),
            "scale": config.get("scale", 1.0),
            "pos_x": config.get("pos_x", 0),
            "pos_y": config.get("pos_y", 0),
            "is_random_pos": config.get("is_random_pos", False)
        }
        for client_queue in self.clients:
            client_queue.put(payload)

    def stop(self):
        if self.server:
            for client_queue in self.clients:
                client_queue.put(None)
            self.server.shutdown()
            self.server.server_close()