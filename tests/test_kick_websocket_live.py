# tests\test_kick_websocket_live.py

import os
import json
import time
import argparse
import requests
import websocket
from datetime import datetime

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
            logs_dir = os.path.join(os.path.dirname(__file__), "logs")
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
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        chatroom = data.get("chatroom", {})
        return {
            "room_id": chatroom.get("id"),
            "channel_id": data.get("id"),
            "user_id": data.get("user_id"),
            "slug": data.get("slug"),
            "followers": data.get("followersCount", 0),
            "livestream": data.get("livestream")
        }

    def start(self):
        if not self.room_id and self.channel_slug:
            print(f"🔍 Buscando información del canal Kick '{self.channel_slug}'...")
            try:
                info = self.fetch_channel_info(self.channel_slug)
                self.room_id = info["room_id"]
                self.channel_id = info["channel_id"]
                print(f"✅ Canal encontrado! Room ID: {self.room_id} | Channel ID: {self.channel_id} | Seguidores: {info['followers']}")
            except Exception as err:
                print(f"⚠️ No se pudo obtener la info del canal de Kick: {err}")
                print("💡 Usando canal por defecto 'xqc' para la inspección...")
                info = self.fetch_channel_info("xqc")
                self.room_id = info["room_id"]
                self.channel_id = info["channel_id"]
        elif not self.room_id:
            print("❌ Debe proporcionar --channel <slug> o --room-id <ID>")
            return

        self._init_logging_file()

        ws_url = f"wss://ws-{self.cluster}.pusher.com/app/{self.key}?protocol=7&client=js&version=7.6.0"
        self._log(f"🚀 Conectando a Kick WebSocket (Pusher Cluster: {self.cluster})...")
        mode_str = "📦 MODO RAW (JSON 100% EN CRUDO)" if self.raw_mode else "💬 MODO RESUMIDO"
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
        self._log(f"🟢 Conexión establecida con éxito a Pusher ({datetime.now().strftime('%H:%M:%S')})")

    def _on_message(self, ws, raw: str):
        try:
            outer = json.loads(raw)
            event = outer.get("event")
            self.event_counts[event] = self.event_counts.get(event, 0) + 1

            now_str = datetime.now().strftime('%H:%M:%S')

            if event == "pusher:connection_established":
                self._log(f"📡 Suscribiendo a canales de chatroom #{self.room_id}...")
                ws.send(json.dumps({
                    "event": "pusher:subscribe",
                    "data": {"channel": f"chatrooms.{self.room_id}.v2"}
                }))
                if self.channel_id:
                    ws.send(json.dumps({
                        "event": "pusher:subscribe",
                        "data": {"channel": f"channel.{self.channel_id}"}
                    }))
                return

            elif event == "pusher:ping":
                ws.send('{"event":"pusher:pong"}')
                return

            if self.raw_mode:
                self._log(f"\n📦 [{now_str}] RAW FRAME - Event: '{event}'")
                try:
                    parsed_outer = dict(outer)
                    if isinstance(outer.get("data"), str):
                        parsed_outer["data"] = json.loads(outer["data"])
                    self._log(json.dumps(parsed_outer, indent=2, ensure_ascii=False))
                except Exception:
                    self._log(raw)
                return

            if event == "App\\Events\\ChatMessageEvent":
                inner = json.loads(outer.get("data", "{}"))
                sender = inner.get("sender", {})
                user = sender.get("username", "Desconocido")
                msg = inner.get("content", "")
                badges = [b.get("type") for b in sender.get("identity", {}).get("badges", []) if isinstance(b, dict)]
                badge_str = f"[{', '.join(badges)}]" if badges else ""
                self._log(f"💬 [{now_str}] {badge_str} {user}: {msg}")

            elif event == "App\\Events\\GiftedSubscriptionsEvent":
                inner = json.loads(outer.get("data", "{}"))
                gifter = inner.get("gifter_username") or inner.get("custom_gift_sender_username") or "Anónimo"
                count = inner.get("gifted_usernames_count", len(inner.get("gifted_usernames", [])))
                gifted_to = ", ".join(inner.get("gifted_usernames", [])[:3])
                self._log(f"🎁 [{now_str}] ¡REGALO DE SUBS! {gifter} regala {count} suscripciones! (a {gifted_to}...)")

            elif event == "App\\Events\\SubscriptionEvent":
                inner = json.loads(outer.get("data", "{}"))
                user = inner.get("username", "Desconocido")
                months = inner.get("months", 1)
                self._log(f"⭐ [{now_str}] ¡NUEVA SUSCRIPCIÓN! {user} se ha suscrito por {months} mes(es)!")

            elif event == "App\\Events\\StreamHostEvent":
                inner = json.loads(outer.get("data", "{}"))
                hoster = inner.get("hoster_username", "Alguien")
                viewers = inner.get("number_viewers", 0)
                self._log(f"🚀 [{now_str}] ¡RAID / HOST! {hoster} ha alojado el canal con {viewers} espectadores!")

            elif event == "App\\Events\\UserBannedEvent":
                inner = json.loads(outer.get("data", "{}"))
                banned_user = inner.get("user", {}).get("username", "Usuario")
                banned_by = inner.get("banned_by", {}).get("username", "Mod")
                self._log(f"🚫 [{now_str}] BUSTED: {banned_user} fue baneado por {banned_by}")

            elif event == "App\\Events\\MessageDeletedEvent":
                inner = json.loads(outer.get("data", "{}"))
                msg_id = inner.get("id", {}).get("id") or inner.get("message", {}).get("id")
                self._log(f"🗑️ [{now_str}] Mensaje eliminado ID: {msg_id}")

            elif event == "App\\Events\\FollowersUpdate":
                inner = json.loads(outer.get("data", "{}"))
                self._log(f"❤️ [{now_str}] Nuevo seguidor / actualización de seguidores: {inner}")

            elif event == "App\\Events\\ViewersUpdate":
                inner = json.loads(outer.get("data", "{}"))
                viewers = inner.get("viewers")
                self._log(f"👁️ [{now_str}] Espectadores en vivo: {viewers}")

            else:
                self._log(f"⚡ [{now_str}] EVENTO RECIBIDO: '{event}'")
                try:
                    pretty_data = json.loads(outer.get("data", "{}"))
                    self._log(json.dumps(pretty_data, indent=2, ensure_ascii=False))
                except Exception:
                    self._log(str(outer))

        except Exception as e:
            self._log(f"⚠️ Error procesando frame: {e}")

    def _on_error(self, ws, error):
        self._log(f"❌ Error de WebSocket: {error}")

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
    parser.add_argument("--channel", type=str, default="xqc", help="Slug del canal Kick (ej: xqc, trainwreckstv)")
    parser.add_argument("--room-id", type=int, default=None, help="ID numérico de la sala de chat de Kick")
    parser.add_argument("--raw", "-r", action="store_true", help="Mostrar JSON 100%% en crudo para TODOS los eventos")
    parser.add_argument("--no-log", action="store_true", help="Desactivar la creación del archivo de log")
    parser.add_argument("--log-path", type=str, default=None, help="Ruta personalizada para guardar el archivo de log")

    args = parser.parse_args()

    inspector = KickWebsocketInspector(
        channel_slug=args.channel,
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
