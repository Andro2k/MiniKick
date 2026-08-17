# tests\live\kick_websocket_live.py

import os
import sys
import json
import time
import argparse
import requests
import websocket
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from backend.config.api_keys import KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY
    PUSHER_CLUSTER = KICK_PUSHER_CLUSTER
    PUSHER_KEY = KICK_PUSHER_KEY
except ImportError:
    PUSHER_CLUSTER = "us2"
    PUSHER_KEY = "32cbd69e4b950bf97679"

class KickWebsocketInspector:
    def __init__(self, channel_slug: str = None, room_id: int = None, cluster: str = PUSHER_CLUSTER, key: str = PUSHER_KEY, raw_mode: bool = False, save_log: bool = True, log_path: str = None):
        self.channel_slug = channel_slug
        self.room_id = room_id
        self.channel_id = None
        self.cluster = cluster
        self.key = key
        self.raw_mode = raw_mode
        self.save_log = save_log
        self.log_filepath = log_path
        self.log_file_handle = None
        self.ws = None
        self.event_counts = {}
        self.start_time = None

    def _log(self, text: str):
        print(text)
        if self.log_file_handle:
            try:
                self.log_file_handle.write(text + "\n")
                self.log_file_handle.flush()
            except Exception:
                pass

    def _init_logging_file(self):
        if not self.save_log:
            return
        try:
            logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
            os.makedirs(logs_dir, exist_ok=True)
            if not self.log_filepath:
                slug_tag = self.channel_slug or f"room_{self.room_id or 'kick'}"
                dt_tag = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.log_filepath = os.path.join(logs_dir, f"ws_{slug_tag}_{dt_tag}.log")
            
            self.log_file_handle = open(self.log_filepath, "a", encoding="utf-8")
            self._log(f"📝 Registrando sesión en archivo: {os.path.abspath(self.log_filepath)}")
        except Exception as e:
            print(f"⚠️ No se pudo iniciar el archivo de log: {e}")

    def fetch_channel_info(self, slug: str) -> dict:
        url = f"https://kick.com/api/v1/channels/{slug}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self._log(f"🔍 Consultando API de Kick para el canal '{slug}'...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        chatroom = data.get("chatroom", {})
        self.room_id = chatroom.get("id")
        self.channel_id = data.get("id")
        return data

    def start(self):
        self._init_logging_file()
        
        if self.channel_slug and not self.room_id:
            try:
                info = self.fetch_channel_info(self.channel_slug)
                self._log(f"✅ Información obtenida: Channel ID={self.channel_id} | Chatroom/Room ID={self.room_id}")
            except Exception as e:
                self._log(f"❌ Error al consultar la API de Kick para '{self.channel_slug}': {e}")
                self._log("Intentando continuar usando el room_id por defecto si está presente...")

        if not self.room_id:
            self._log("❌ No se especificó ni se pudo obtener un room_id válido.")
            return

        ws_url = f"wss://ws-{self.cluster}.pusher.com/app/{self.key}?protocol=7&client=js&version=7.6.0"
        self._log(f"🚀 Conectando a Kick Pusher WebSocket ({ws_url})...")
        self._log(f"📺 Room ID objetivo: {self.room_id} (Canal: {self.channel_slug or 'N/A'})")
        mode_str = "📦 MODO RAW (JSON 100% EN CRUDO)" if self.raw_mode else "💬 MODO RESUMIDO Y FORMATEADO"
        self._log(f"💡 {mode_str} activo. Presione Ctrl+C para salir.\n" + "="*70)

        self.start_time = time.time()
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.run_forever(ping_interval=30, ping_timeout=10)

    def _on_open(self, ws):
        now_str = datetime.now().strftime('%H:%M:%S')
        self._log(f"🟢 Conexión WebSocket establecida con éxito ({now_str})")
        self._log(f"📡 Suscribiéndose a chatrooms.{self.room_id}.v2 y channels.{self.channel_id or self.room_id}.v2...")

        sub_chatroom = {
            "event": "pusher:subscribe",
            "data": {
                "auth": "",
                "channel": f"chatrooms.{self.room_id}.v2"
            }
        }
        ws.send(json.dumps(sub_chatroom))

        if self.channel_id:
            sub_channel = {
                "event": "pusher:subscribe",
                "data": {
                    "auth": "",
                    "channel": f"channel.{self.channel_id}"
                }
            }
            ws.send(json.dumps(sub_channel))

    def _on_message(self, ws, message_str: str):
        try:
            data = json.loads(message_str)
        except Exception:
            self._log(f"[RAW MSG ERROR PARSING]: {message_str}")
            return

        event = data.get("event", "UNKNOWN_EVENT")
        channel = data.get("channel", "")
        raw_event_data = data.get("data", "")
        now_str = datetime.now().strftime('%H:%M:%S')

        self.event_counts[event] = self.event_counts.get(event, 0) + 1

        if self.raw_mode:
            self._log(f"\n📦 [{now_str}] EVENTO: '{event}' | CANAL: '{channel}'")
            self._log(json.dumps(data, indent=2, ensure_ascii=False))
            return

        if event == "pusher:connection_established":
            self._log(f"⚡ [{now_str}] Pusher Handshake completado.")
        elif event == "pusher_internal:subscription_succeeded":
            self._log(f"✅ [{now_str}] Suscripción confirmada al canal: {channel}")
        elif event == "pusher:ping":
            ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
        elif event == "App\\Events\\ChatMessageEvent":
            try:
                inner = json.loads(raw_event_data) if isinstance(raw_event_data, str) else raw_event_data
                sender = inner.get("sender", {})
                username = sender.get("username", "Desconocido")
                user_id = sender.get("id", "")
                content = inner.get("content", "")
                identity = sender.get("identity", {})
                color = identity.get("color", "")
                badges = [b.get("type", "") for b in identity.get("badges", [])]
                badge_str = f"[{', '.join(badges)}]" if badges else ""
                
                self._log(f"💬 [{now_str}] {badge_str} {username} (ID:{user_id}): {content}")
            except Exception as ex:
                self._log(f"⚠️ [{now_str}] Error parseando ChatMessageEvent: {ex}")
        elif event == "App\\Events\\PollUpdateEvent":
            try:
                inner = json.loads(raw_event_data) if isinstance(raw_event_data, str) else raw_event_data
                poll = inner.get("poll", {})
                title = poll.get("title", "")
                options = poll.get("options", [])
                opts_str = " | ".join([f"{o.get('label')}: {o.get('votes', 0)} votos" for o in options])
                self._log(f"📊 [{now_str}] ENCUESTA ACTIVA: '{title}' -> {opts_str}")
            except Exception:
                self._log(f"📊 [{now_str}] Encuesta actualizada.")
        elif event == "App\\Events\\PollDeleteEvent":
            self._log(f"🗑️ [{now_str}] Encuesta finalizada/eliminada.")
        elif event == "App\\Events\\PinnedMessageCreatedEvent":
            try:
                inner = json.loads(raw_event_data) if isinstance(raw_event_data, str) else raw_event_data
                msg = inner.get("pinned_message", {})
                content = msg.get("content", "")
                sender = msg.get("sender", {}).get("username", "")
                self._log(f"📌 [{now_str}] MENSAJE FIJADO por {sender}: '{content}'")
            except Exception:
                self._log(f"📌 [{now_str}] Mensaje fijado creado.")
        elif event == "App\\Events\\PinnedMessageDeletedEvent":
            self._log(f"📌 [{now_str}] Mensaje fijado retirado.")
        elif event == "App\\Events\\SubscriptionEvent":
            self._log(f"⭐ [{now_str}] ¡NUEVA SUSCRIPCIÓN EN EL CANAL!")
        elif event == "App\\Events\\GiftedSubscriptionsEvent":
            self._log(f"🎁 [{now_str}] ¡SUBSCRIPTIONES DE REGALO!")
        elif event == "App\\Events\\StreamHostEvent":
            self._log(f"🚀 [{now_str}] ¡HOSTING/RAID RECIBIDO!")
        else:
            self._log(f"⚡ [{now_str}] EVENTO RECIBIDO: '{event}' en canal '{channel}'")

    def _on_error(self, ws, error):
        self._log(f"❌ Error de WebSocket Kick: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        self._log(f"\n🔴 Conexión cerrada. ({close_status_code}: {close_msg})")
        self._print_stats()

    def _print_stats(self):
        if not self.start_time:
            return
        elapsed = max(1.0, time.time() - self.start_time)
        self._log("\n" + "="*70)
        self._log("📊 RESUMEN DE LA PRUEBA WEBSOCKET DE KICK")
        self._log("="*70)
        self._log(f"⏱️ Tiempo transcurrido: {int(elapsed)} segundos")
        self._log(f"📺 Canal inspeccionado: {self.channel_slug or self.room_id}")
        self._log("📈 Eventos Recibidos por Tipo:")
        for ev, count in sorted(self.event_counts.items(), key=lambda x: x[1], reverse=True):
            self._log(f"  • {ev}: {count}")
        chat_count = self.event_counts.get("App\\Events\\ChatMessageEvent", 0)
        msg_per_min = round((chat_count / elapsed) * 60, 2)
        self._log(f"💬 Promedio de chat: {msg_per_min} msgs/minuto")
        if self.log_filepath:
            self._log(f"📁 Log guardado en: {os.path.abspath(self.log_filepath)}")
        self._log("="*70)

        if self.log_file_handle:
            try:
                self.log_file_handle.close()
                self.log_file_handle = None
            except Exception:
                pass

def main():
    parser = argparse.ArgumentParser(description="Kick WebSocket Real-Time Test & Event Inspector")
    parser.add_argument("--slug", "-s", type=str, default="xqc", help="Slug del canal de Kick (ej: xqc, westcol, rubius)")
    parser.add_argument("--room-id", "-r", type=int, default=None, help="Room ID explícito si se conoce")
    parser.add_argument("--raw", action="store_true", help="Mostrar payloads JSON 100%% en crudo")
    parser.add_argument("--no-log", action="store_true", help="Desactivar la creación del archivo de log")
    parser.add_argument("--log-path", type=str, default=None, help="Ruta personalizada para guardar el archivo de log")

    args = parser.parse_args()

    inspector = KickWebsocketInspector(
        channel_slug=args.slug,
        room_id=args.room_id,
        raw_mode=args.raw,
        save_log=not args.no_log,
        log_path=args.log_path
    )
    try:
        inspector.start()
    except KeyboardInterrupt:
        print("\n👋 Prueba interrumpida por el usuario.")
        inspector._print_stats()

if __name__ == "__main__":
    main()
