# backend/services/overlay_server.py

import os
import json
import queue
import threading
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class OverlayRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # 1. Servir la plantilla HTML a OBS
        if path == "/overlay":
            html_path = os.path.abspath(os.path.join("assets", "overlays", "rewards.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, "Overlay HTML no encontrado. Verifica la carpeta assets/overlays.")
                
        # 2. Servir los archivos multimedia locales
        elif path == "/media":
            query = parse_qs(parsed.query)
            if "path" not in query:
                self.send_error(400, "Ruta no especificada")
                return
                
            filepath = query["path"][0]
            if not os.path.exists(filepath):
                self.send_error(404, "Archivo multimedia no encontrado en el disco")
                return
                
            mime_type, _ = mimetypes.guess_type(filepath)
            
            try:
                with open(filepath, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", mime_type or "application/octet-stream")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(f.read())
            except Exception as e:
                self.send_error(500, f"Error leyendo archivo: {e}")
                
        # 3. Mantener viva la conexión SSE para mandar las alertas
        elif path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            # Cada conexión (OBS, navegador) tiene su propia cola de mensajes
            client_queue = queue.Queue()
            self.server.manager.clients.append(client_queue)
            
            try:
                while True:
                    alert = client_queue.get() # Se queda esperando aquí sin consumir CPU
                    if alert is None:
                        break # Señal de apagado
                    
                    # Formato estricto de SSE: "data: {json}\n\n"
                    self.wfile.write(f"data: {json.dumps(alert)}\n\n".encode("utf-8"))
                    self.wfile.flush()
            except Exception:
                pass # El cliente (OBS) cerró la conexión o recargó la página
            finally:
                if client_queue in self.server.manager.clients:
                    self.server.manager.clients.remove(client_queue)
        else:
            self.send_error(404, "Endpoint no válido")

    def log_message(self, format, *args):
        pass # Anulamos los logs por defecto para no saturar la terminal

class OverlayServerManager:
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
        self.clients = [] # Lista de conexiones activas

    def start(self):
        """Inicia el servidor en un hilo secundario (Separación de Responsabilidades)."""
        self.server = HTTPServer(("127.0.0.1", self.port), OverlayRequestHandler)
        self.server.manager = self # Referencia cruzada segura
        
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"🌐 Servidor Overlay activo: http://localhost:{self.port}/overlay")

    def trigger_alert(self, reward_name: str, config: dict):
        """Envía la alerta y sus parámetros a todos los clientes (OBS) conectados."""
        
        # Retrocompatibilidad por si había strings guardados en la versión anterior
        if isinstance(config, str):
            config = {"filepath": config, "volume": 1.0, "scale": 1.0, "position": "center"}
            
        payload = {
            "reward": reward_name,
            "file_url": f"http://localhost:{self.port}/media?path={config['filepath']}",
            "volume": config.get("volume", 1.0),
            "scale": config.get("scale", 1.0),
            "position": config.get("position", "center")
        }
        for client_queue in self.clients:
            client_queue.put(payload)

    def stop(self):
        if self.server:
            # Enviar pastilla de cianuro a todos los hilos en espera
            for client_queue in self.clients:
                client_queue.put(None)
            self.server.shutdown()
            self.server.server_close()