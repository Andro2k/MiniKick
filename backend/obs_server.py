import os
import json
from pathlib import Path
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

# Permitir conexiones desde cualquier origen (vital para el navegador de OBS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RUTAS SEGURAS CON PATHLIB ---
# Subimos DOS niveles desde este script (backend -> raíz)
BASE_DIR = Path(__file__).resolve().parent.parent
HTML_PATH = BASE_DIR / "assets" / "html" / "overlay.html"

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
        # pathlib nos permite leer el contenido súper fácil
        return HTMLResponse(content=HTML_PATH.read_text(encoding="utf-8"))
    except Exception:
        return HTMLResponse(
            content=f"<h1>Error: No se encontró overlay.html en {HTML_PATH}</h1>", 
            status_code=404
        )

@app.get("/serve_media")
async def serve_media(path: str):
    """Transmite el archivo multimedia local hacia OBS."""
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
    """El bot de Kick o el botón de 'Test' llaman a esta ruta para disparar la alerta."""
    print(f"[*] Disparando alerta en OBS: {data.get('type')}")
    await manager.broadcast(data)
    return {"status": "ok", "message": "Alerta enviada a OBS"}

# --- EL MOTOR DE ARRANQUE ---
if __name__ == "__main__":
    print("[*] Levantando servidor local de OBS en el puerto 8081...")
    # Pasamos la app directamente para evitar problemas de rutas en Windows
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="warning")