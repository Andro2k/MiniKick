# backend/services/trigger_worker.py

import asyncio
import os
import sys
import urllib.parse
from aiohttp import web
from PyQt6.QtCore import QThread, pyqtSignal

class OverlayServer(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, port=8081):
        super().__init__()
        self.port = port
        self.loop = None
        self.runner = None
        self.ws_clients = set()
        self.is_running = True
        self.base_dir = self._get_base_dir()

    def _get_base_dir(self):
        """Obtiene la ruta base correcta, ya sea en desarrollo o compilado con PyInstaller."""
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        else:
            return os.getcwd()

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

        app.router.add_get('/', self._index_handler)
        app.router.add_get('/ws/triggers', self._websocket_handler)

        app.router.add_get('/media', self._media_handler)
        
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        
        try:
            site = web.TCPSite(self.runner, '127.0.0.1', self.port)
            await site.start()
            self.log_signal.emit(f"📺 Overlay activo en: http://127.0.0.1:{self.port}")
        except OSError as e:
            self.log_signal.emit(f"❌ Error al iniciar el servidor del Overlay: {e}")

    async def _index_handler(self, request):
        # NUEVO: Buscar en assets/overlays/
        html_path = os.path.join(self.base_dir, "assets", "overlays", "triggers_overlay.html")
        
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                return web.Response(text=f.read(), content_type="text/html")
        except FileNotFoundError:
            error_html = f"<h2 style='color:red;'>❌ Archivo no encontrado en: {html_path}</h2>"
            return web.Response(text=error_html, content_type="text/html", status=404)

    async def _media_handler(self, request):
        """Lee el archivo desde la ruta absoluta de la PC y se lo envía a OBS."""
        file_path = request.query.get("path", "")
        if not file_path or not os.path.isfile(file_path):
            return web.Response(status=404, text="Archivo multimedia no encontrado")
        
        return web.FileResponse(file_path)

    async def _websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.add(ws)
        self.log_signal.emit("🟢 OBS conectado al Overlay.")
        try:
            async for _ in ws: pass
        finally:
            self.ws_clients.remove(ws)
            self.log_signal.emit("🔴 OBS desconectado del Overlay.")
        return ws

    def play_media(self, filepath: str, media_type: str, volume: int = 100, 
                   scale: float = 1.0, pos_x: int = 0, pos_y: int = 0, random_pos: bool = False):
        if not self.loop or self.loop.is_closed(): return
            
        payload = {
            "action": "play_media",
            "url": f"/media?path={urllib.parse.quote(filepath)}",
            "type": media_type,
            "volume": volume,
            "scale": scale,
            "pos_x": pos_x,
            "pos_y": pos_y,
            "random": random_pos
        }
        self.loop.call_soon_threadsafe(asyncio.create_task, self._broadcast(payload))

    async def _broadcast(self, message: dict):
        if not self.ws_clients: return
        for ws in list(self.ws_clients):
            try:
                if not ws.closed: await ws.send_json(message)
            except: pass

    def stop(self):
        self.is_running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.quit()
        self.wait()

    async def _stop_server(self):
        for ws in list(self.ws_clients):
            if not ws.closed: await ws.close()
        self.ws_clients.clear()
        if self.runner: await self.runner.cleanup()