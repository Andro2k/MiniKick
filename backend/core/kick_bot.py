# backend/core/kick_bot.py
import asyncio
import json
import aiohttp
from PyQt6.QtCore import QThread, pyqtSignal
from backend.core.db_manager import DBManager
from backend.core.api_client import KickAPIClient

class KickBot(QThread):
    """Orquestador principal que maneja la conexión con Kick y los eventos en tiempo real."""
    
    log_signal = pyqtSignal(str)
    chat_signal = pyqtSignal(str, str)
    redemption_signal = pyqtSignal(str, str, str)
    rewards_list_signal = pyqtSignal(list)

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, db_manager: DBManager):
        super().__init__()
        self.api = KickAPIClient(client_id, client_secret, redirect_uri, db_manager)
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
        # 1. Autenticar
        if not await self.api.authenticate_if_needed(self.log_signal.emit):
            self.log_signal.emit("❌ Error: No se pudo autenticar el bot.")
            return

        # 2. Obtener Usuario
        self.log_signal.emit("🔍 Consultando perfil en la API de Kick...")
        status, user_data = await self.api.request("GET", "https://api.kick.com/public/v1/users")
        
        if status != 200:
            self.log_signal.emit(f"❌ Error consultando el usuario de la API. Status: {status}")
            return

        user_obj = self._extract_user_object(user_data)
        slug = user_obj.get("slug") or user_obj.get("name") or user_obj.get("username")
        
        if not slug:
            self.log_signal.emit(f"❌ Estructura desconocida. JSON recibido: {user_data}")
            return

        self.log_signal.emit(f"👤 Canal detectado: {slug}")
        
        # 3. Obtener Chatroom ID (Evadiendo Cloudflare)
        self.log_signal.emit("🛡️ Evadiendo Cloudflare para obtener el ID de la sala...")
        try:
            channel_data = await self.loop.run_in_executor(None, self.api.fetch_channel_data_sync, slug)
            self.chatroom_id = str(channel_data.get('chatroom', {}).get('id', ''))
            
            if not self.chatroom_id:
                self.log_signal.emit("❌ Error: Se evadió Cloudflare pero no se halló el chatroom_id.")
                return
                
            self.log_signal.emit(f"🔌 Sala de Chat (ID): {self.chatroom_id}")
            
        except Exception as e:
            self.log_signal.emit(f"❌ Error al conectar con Kick (Cloudflare bloqueó): {e}")
            return

        # 4. Obtener Recompensas Existentes
        await self._fetch_initial_rewards()

        # 5. Iniciar sistemas paralelos
        self.log_signal.emit("🚀 Iniciando motores de Chat y Recompensas...")
        await asyncio.gather(
            self._listen_chat(),
            self._poll_redemptions()
        )

    def _extract_user_object(self, user_data: dict) -> dict:
        """Maneja las diferentes estructuras de respuesta de la API."""
        if isinstance(user_data, dict):
            lista = user_data.get("data", [])
            return lista[0] if lista else user_data
        elif isinstance(user_data, list) and len(user_data) > 0:
            return user_data[0]
        return {}

    async def _fetch_initial_rewards(self):
        self.log_signal.emit("📦 Obteniendo recompensas disponibles en Kick...")
        status, rewards_data = await self.api.request("GET", "https://api.kick.com/public/v1/channels/rewards")
        
        if status == 200:
            lista_recompensas = rewards_data.get("data", [])
            self.rewards_list_signal.emit(lista_recompensas) 
            self.log_signal.emit(f"✅ Se encontraron {len(lista_recompensas)} recompensas en tu canal.")
        else:
            self.log_signal.emit(f"⚠️ No se pudieron cargar las recompensas de Kick. Status: {status}")

    # --- MÓDULOS DE TIEMPO REAL ---

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
                            self._handle_chat_message(msg.data, ws)
            except Exception as e:
                self.log_signal.emit(f"⚠️ Error WS Chat: {e}. Reconectando...")
                await asyncio.sleep(3)

    def _handle_chat_message(self, raw_data: str, ws: aiohttp.ClientWebSocketResponse):
        """Procesa un mensaje entrante del websocket de Pusher."""
        data = json.loads(raw_data)
        if data.get("event") == "pusher:ping":
            asyncio.create_task(ws.send_json({"event": "pusher:pong", "data": {}}))
            return
            
        if data.get("event") == "App\\Events\\ChatMessageEvent":
            chat_data = json.loads(data.get("data", "{}"))
            sender = chat_data.get('sender', {}).get('username', 'Desconocido')
            if content := chat_data.get('content', ''):
                self.chat_signal.emit(sender, content)

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
                                
                if ids_to_accept: 
                    await self.api.request("POST", "https://api.kick.com/public/v1/channels/rewards/redemptions/accept", json={"ids": ids_to_accept})
                    
                first_scan = False
            await asyncio.sleep(2)

    def update_kick_reward_sync(self, reward_id: str, cost: int, description: str, enabled: bool, color: str):
        """Función accesible desde el Frontend para mandar a actualizar un punto en Kick."""
        if not self.loop or self.loop.is_closed(): 
            return
            
        payload = {
            "cost": cost,
            "description": description,
            "is_enabled": enabled,
            "color": color
        }
        
        async def _do_update():
            status, response = await self.api.update_reward(reward_id, payload)
            if status == 200:
                self.log_signal.emit(f"✅ Recompensa actualizada en Kick con éxito.")
            else:
                self.log_signal.emit(f"⚠️ Error actualizando en Kick (Status: {status}).")

        # Enviamos la tarea al event loop del bot
        asyncio.run_coroutine_threadsafe(_do_update(), self.loop)

    def stop(self):
        self.is_running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self._cancel_tasks)
        self.quit()
        self.wait()

    def _cancel_tasks(self):
        for task in asyncio.all_tasks(self.loop): task.cancel()