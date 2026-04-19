import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn

app = FastAPI()

# Permitir conexiones desde cualquier origen (vital para el navegador de OBS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RUTAS ---
# Subimos un nivel desde 'backend' para llegar a la raíz de MiniKick
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(BASE_DIR, "assets", "html", "overlay.html")

# --- GESTOR DE WEBSOCKETS ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("[+] OBS Conectado al Overlay de Alertas")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print("[-] OBS Desconectado del Overlay")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"[!] Error enviando a OBS: {e}")

manager = ConnectionManager()

# --- ENDPOINTS ---

@app.get("/")
async def get_overlay():
    """Entrega el archivo HTML a la Fuente de Navegador de OBS."""
    try:
        with open(HTML_PATH, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception:
        return HTMLResponse(
            content=f"<h1>Error: No se encontró overlay.html en {HTML_PATH}</h1>", 
            status_code=404
        )

@app.get("/serve_media")
async def serve_media(path: str):
    """
    Recibe la ruta absoluta del PC del streamer (ej: C:/Users/video.mp4) 
    y la transmite como un video/audio web a OBS.
    """
    if os.path.exists(path):
        return FileResponse(path)
    print(f"[-] Archivo no encontrado: {path}")
    return HTMLResponse(content="Archivo no encontrado", status_code=404)

@app.websocket("/ws/triggers")
async def websocket_endpoint(websocket: WebSocket):
    """Mantiene la conexión en tiempo real con el HTML en OBS."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/trigger")
async def trigger_media(data: dict):
    """El bot de Kick llamará a esta ruta cuando detecte un canje válido."""
    print(f"[*] Disparando alerta en OBS: {data.get('type')}")
    await manager.broadcast(data)
    return {"status": "ok", "message": "Alerta enviada a OBS"}
