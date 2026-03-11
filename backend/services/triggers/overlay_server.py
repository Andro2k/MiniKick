# backend/services/triggers/overlay_server.py

import asyncio
import os
from aiohttp import web
from PyQt6.QtCore import QThread, pyqtSignal

class OverlayMinimalServer(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, port=8081):
        super().__init__()
        self.port = port
        self.loop = None
        self.runner = None
        self.ws_clients = set()
        self.is_running = True
        
        # Aseguramos que exista la carpeta media
        os.makedirs("media", exist_ok=True)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._start_server())
        
        try:
            self.loop.run_forever()
        except asyncio.CancelledError:
            pass
        finally:
            self.loop.run_until_complete(self._stop_server())
            self.loop.close()

    async def _start_server(self):
        app = web.Application()
        
        # Rutas del servidor
        app.router.add_get('/', self.index_handler)
        app.router.add_get('/ws', self.websocket_handler)
        app.router.add_static('/media', os.path.abspath('media')) # Para que OBS pueda leer los videos
        
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '127.0.0.1', self.port)
        await site.start()
        self.log_signal.emit(f"📺 Overlay activo en: http://127.0.0.1:{self.port}")

    async def index_handler(self, request):
        """Sirve la página web que pondrás en OBS."""
        with open("overlay.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")

    async def websocket_handler(self, request):
        """Mantiene la conexión en tiempo real con OBS."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.add(ws)
        self.log_signal.emit("🟢 OBS se ha conectado al Overlay.")
        
        try:
            async for msg in ws: pass
        finally:
            self.ws_clients.remove(ws)
            self.log_signal.emit("🔴 OBS se ha desconectado.")
        return ws

    def play_media(self, filename, media_type, volume):
        """Dispara el archivo multimedia a todos los OBS conectados."""
        if not self.loop: return
        payload = {"action": "play", "file": filename, "type": media_type, "volume": volume}
        asyncio.run_coroutine_threadsafe(self._broadcast(payload), self.loop)

    async def _broadcast(self, message):
        for ws in list(self.ws_clients):
            try:
                await ws.send_json(message)
            except: pass

    def stop(self):
        if self.loop: self.loop.call_soon_threadsafe(self.loop.stop)
        self.quit()
        self.wait()

    async def _stop_server(self):
        if self.runner: await self.runner.cleanup()