import asyncio
import json
import os
import base64
import hashlib
import urllib.parse
import webbrowser
import aiohttp
from aiohttp import web
from PyQt6.QtCore import QThread, pyqtSignal
import cloudscraper

class KickAPI:
    def __init__(self, client_id, client_secret, redirect_uri, session_file="backend/session.json"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.session_file = session_file
        self.access_token = None
        self.refresh_token = None
        self.session = None
        self._load_tokens()

    def _load_tokens(self):
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")

    def _save_tokens(self, data):
        with open(self.session_file, 'w') as f:
            json.dump(data, f, indent=4)
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session: 
            await self.session.close()

    async def do_refresh(self) -> bool:
        if not self.refresh_token: return False
        url = "https://id.kick.com/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        async with self.session.post(url, data=payload) as resp:
            if resp.status == 200:
                new_data = await resp.json()
                if "refresh_token" not in new_data:
                    new_data["refresh_token"] = self.refresh_token
                self._save_tokens(new_data)
                return True
            return False

    async def request(self, method, url, **kwargs):
        if not self.session: await self.init_session()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Accept"] = "application/json"

        async with self.session.request(method, url, headers=headers, **kwargs) as resp:
            if resp.status == 401:  
                if await self.do_refresh():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    async with self.session.request(method, url, headers=headers, **kwargs) as retry_resp:
                        return retry_resp.status, await retry_resp.json()
                else:
                    return 401, {"error": "Fallo al renovar token"}
            try:
                return resp.status, await resp.json()
            except:
                return resp.status, {}

    # --- FLUJO OAUTH AUTOMÁTICO ---
    async def authenticate_if_needed(self, log_callback) -> bool:
        """Verifica si el token es válido. Si no, lanza el flujo en el navegador."""
        if self.access_token:
            status, _ = await self.request("GET", "https://api.kick.com/public/v1/users")
            if status == 200: 
                return True # El token actual funciona perfecto

        log_callback("⚠️ Token faltante o expirado. Abriendo navegador para Login OAuth...")
        
        # Generar códigos de seguridad PKCE
        verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('utf-8')).digest()).rstrip(b'=').decode('utf-8')
        
        params = {
            "client_id": self.client_id, "code_challenge": challenge, "code_challenge_method": "S256",
            "redirect_uri": self.redirect_uri, "response_type": "code", "state": "kick_auth",
            "scope": "user:read channel:read channel:write chat:write events:subscribe channel:rewards:read channel:rewards:write"
        }
        auth_url = f"https://id.kick.com/oauth/authorize?{urllib.parse.urlencode(params)}"
        
        # Levantar mini-servidor para atrapar la respuesta
        parsed_uri = urllib.parse.urlparse(self.redirect_uri)
        future_code = asyncio.Future()

        async def callback_handler(request):
            if code := request.query.get("code"):
                future_code.set_result(code)
                return web.Response(text="<h2>¡Exito!</h2><p>Ya puedes volver a KickMonitor.</p>", content_type="text/html")
            return web.Response(text="Error de Login.", content_type="text/html")
            
        app = web.Application()
        app.router.add_get(parsed_uri.path, callback_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, parsed_uri.hostname, parsed_uri.port)
        await site.start()
        
        webbrowser.open(auth_url) # Abre la web de Kick
        
        try:
            code = await asyncio.wait_for(future_code, timeout=120) # Espera max 2 min
            log_callback("✅ Autorización concedida. Obteniendo tokens...")
            
            payload = {
                "grant_type": "authorization_code", "client_id": self.client_id, "client_secret": self.client_secret,
                "code": code, "redirect_uri": self.redirect_uri, "code_verifier": verifier
            }
            async with self.session.post("https://id.kick.com/oauth/token", data=payload) as resp:
                if resp.status == 200:
                    self._save_tokens(await resp.json())
                    return True
        except asyncio.TimeoutError:
            log_callback("❌ El tiempo de inicio de sesión expiró.")
        finally:
            await site.stop()
            await runner.cleanup()
            
        return False

# =========================================================================
# 2. HILO PRINCIPAL (El motor del Backend)
# =========================================================================
class KickMinimalBackend(QThread):
    log_signal = pyqtSignal(str)
    chat_signal = pyqtSignal(str, str)
    redemption_signal = pyqtSignal(str, str, str)

    def __init__(self, client_id, client_secret, redirect_uri):
        super().__init__()
        self.api = KickAPI(client_id, client_secret, redirect_uri)
        self.chatroom_id = None
        self.is_running = True
        self.loop = None
        self.processed_redemptions = set()

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._main_tasks())
        except asyncio.CancelledError:
            pass
        finally:
            self.loop.run_until_complete(self.api.close())
            self.loop.close()

    async def _main_tasks(self):
        await self.api.init_session()
        
        # 1. Autenticar (Flujo OAuth automático si es necesario)
        if not await self.api.authenticate_if_needed(self.log_signal.emit):
            self.log_signal.emit("❌ Error: No se pudo autenticar el bot.")
            return

        # 2. Autodescubrimiento del Usuario y Canal
        self.log_signal.emit("🔍 Consultando perfil en la API de Kick...")
        status, user_data = await self.api.request("GET", "https://api.kick.com/public/v1/users")
        
        if status == 200:
            if isinstance(user_data, dict):
                lista = user_data.get("data", [])
                user_obj = lista[0] if lista else user_data
            elif isinstance(user_data, list) and len(user_data) > 0:
                user_obj = user_data[0]
            else:
                user_obj = {}

            slug = user_obj.get("slug") or user_obj.get("name") or user_obj.get("username")
            
            if not slug:
                self.log_signal.emit(f"❌ Estructura desconocida. JSON recibido: {user_data}")
                return

            self.log_signal.emit(f"👤 Canal detectado: {slug}")
            
            # 3. Obtener el Chatroom ID oculto (EVADIENDO CLOUDFLARE)
            self.log_signal.emit("🛡️ Evadiendo Cloudflare para obtener el ID de la sala...")
            
            def fetch_channel_data():
                # Creamos el scraper y hacemos la petición sincrónica
                scraper = cloudscraper.create_scraper()
                headers = {"Authorization": f"Bearer {self.api.access_token}", "Accept": "application/json"}
                resp = scraper.get(f"https://kick.com/api/v1/channels/{slug}", headers=headers, timeout=10)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    raise Exception(f"HTTP {resp.status_code}")

            try:
                # Corremos el scraper en un hilo secundario para no bloquear el Event Loop
                channel_data = await self.loop.run_in_executor(None, fetch_channel_data)
                self.chatroom_id = str(channel_data.get('chatroom', {}).get('id', ''))
                
                if not self.chatroom_id:
                    self.log_signal.emit("❌ Error: Se evadió Cloudflare pero no se halló el chatroom_id.")
                    return
                    
                self.log_signal.emit(f"🔌 Sala de Chat (ID): {self.chatroom_id}")
                
            except Exception as e:
                self.log_signal.emit(f"❌ Error al conectar con Kick (Cloudflare bloqueó): {e}")
                return
        else:
            self.log_signal.emit(f"❌ Error consultando el usuario de la API. Status: {status}")
            return

        # 4. Iniciar sistemas paralelos
        self.log_signal.emit("🚀 Iniciando motores de Chat y Recompensas...")
        await asyncio.gather(
            self._listen_chat(),
            self._poll_redemptions()
        )

    # --- MÓDULO CHAT (PUSHER) ---
    async def _listen_chat(self):
        pusher_url = "wss://ws-us2.pusher.com/app/32cbd69e4b950bf97679?protocol=7&client=js&version=7.6.0&flash=false"
        while self.is_running:
            try:
                async with self.api.session.ws_connect(pusher_url) as ws:
                    subscribe_msg = {"event": "pusher:subscribe", "data": {"auth": "", "channel": f"chatrooms.{self.chatroom_id}.v2"}}
                    await ws.send_json(subscribe_msg)
                    self.log_signal.emit("🟢 Escuchando Chat en vivo.")

                    async for msg in ws:
                        if not self.is_running: break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("event") == "pusher:ping":
                                await ws.send_json({"event": "pusher:pong", "data": {}})
                                continue
                            if data.get("event") == "App\\Events\\ChatMessageEvent":
                                chat_data = json.loads(data.get("data", "{}"))
                                sender = chat_data.get('sender', {}).get('username', 'Desconocido')
                                if content := chat_data.get('content', ''):
                                    self.chat_signal.emit(sender, content)
            except Exception as e:
                self.log_signal.emit(f"⚠️ Error WS Chat: {e}. Reconectando...")
                await asyncio.sleep(3)

    # --- MÓDULO CANJES (POLLING) ---
    async def _poll_redemptions(self):
        url = "https://api.kick.com/public/v1/channels/rewards/redemptions?status=pending"
        first_scan = True
        while self.is_running:
            status, response = await self.api.request("GET", url)
            if status == 200:
                groups = response.get("data", [])
                ids_to_accept = []
                for group in groups:
                    reward_title = group.get("reward", {}).get("title", "")
                    for red in group.get("redemptions", []):
                        if (red_id := red.get("id")) and red_id not in self.processed_redemptions:
                            self.processed_redemptions.add(red_id)
                            ids_to_accept.append(red_id)
                            if not first_scan:
                                user = red.get("user", {}).get("username", "Desconocido")
                                self.redemption_signal.emit(user, reward_title, red.get("user_input", ""))
                                
                if ids_to_accept: # Aprueba los canjes en Kick
                    await self.api.request("POST", "https://api.kick.com/public/v1/channels/rewards/redemptions/accept", json={"ids": ids_to_accept})
                first_scan = False
            await asyncio.sleep(2)

    def stop(self):
        self.is_running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self._cancel_tasks)
        self.quit()
        self.wait()

    def _cancel_tasks(self):
        for task in asyncio.all_tasks(self.loop): task.cancel()