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
        app.router.add_get('/', self.index_handler)
        # ACTUALIZADO: La nueva ruta que pide tu HTML
        app.router.add_get('/ws/triggers', self.websocket_handler) 
        app.router.add_static('/media', os.path.abspath('media'))
        
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '127.0.0.1', self.port)
        await site.start()
        self.log_signal.emit(f"📺 Overlay activo en: http://127.0.0.1:{self.port}")

    async def index_handler(self, request):
        import os
        # Obtenemos la ruta desde donde ejecutaste main.py (tu carpeta kickmonitor)
        ruta_html = os.path.join(os.getcwd(), "triggers_overlay.html")
        
        try:
            with open(ruta_html, "r", encoding="utf-8") as f:
                return web.Response(text=f.read(), content_type="text/html")
        except FileNotFoundError:
            # Si no lo encuentra, te mostrará la ruta exacta en la pantalla
            error_html = f"""
            <div style='color: white; background: red; padding: 20px; font-family: sans-serif;'>
                <h2>❌ Archivo no encontrado</h2>
                <p>El servidor está buscando tu archivo HTML exactamente en esta ruta:</p>
                <b>{ruta_html}</b>
                <p>Por favor, asegúrate de que el archivo exista ahí y se llame exactamente así (cuidado con las extensiones ocultas como .html.html).</p>
            </div>
            """
            return web.Response(text=error_html, content_type="text/html", status=404)
        except Exception as e:
            return web.Response(text=f"Error inesperado: {str(e)}", content_type="text/plain", status=500)

    async def websocket_handler(self, request):
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

    # ACTUALIZADO: Añadidos los nuevos parámetros que soporta tu HTML
    def play_media(self, filename, media_type, volume=100, duration=0, scale=1.0, pos_x=0, pos_y=0, random_pos=False):
        if not self.loop: return
        payload = {
            "action": "play_media",
            "url": f"/media/{filename}",
            "type": media_type,
            "volume": volume,
            "duration": duration,
            "scale": scale,
            "pos_x": pos_x,
            "pos_y": pos_y,
            "random": random_pos
        }
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