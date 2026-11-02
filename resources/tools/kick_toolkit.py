# resources\tools\kick_toolkit.py\

import os
import sys
import re
import time
import json
import argparse
import datetime
from typing import Optional, Dict, Any, List, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import requests
import websocket

try:
    from backend.providers.chat.kick_provider import ScraperFactory
except ImportError:
    ScraperFactory = None

try:
    from backend.config import KICK_PUSHER
    DEFAULT_PUSHER_CLUSTER = KICK_PUSHER.cluster
    DEFAULT_PUSHER_KEY = KICK_PUSHER.keys[0]
except ImportError:
    DEFAULT_PUSHER_CLUSTER = "us2"
    DEFAULT_PUSHER_KEY = ""

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:
    pass

class KickChannelResolver:
    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_http_client(cls):
        if ScraperFactory is not None:
            try:
                return ScraperFactory.create()
            except Exception:
                pass
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        return session

    @classmethod
    def resolve_channel(cls, slug: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        slug_norm = slug.strip().lower()
        if not slug_norm:
            return None

        if not force_refresh and slug_norm in cls._cache:
            return cls._cache[slug_norm]

        client = cls.get_http_client()
        url = f"https://kick.com/api/v1/channels/{slug_norm}"
        try:
            resp = client.get(url, timeout=10)
            if resp.status_code != 200:
                return None
            data = resp.json()
        except Exception as e:
            print(f"⚠️ Error al consultar API de canal para '{slug}': {e}")
            return None

        channel_id = data.get("id")
        chatroom = data.get("chatroom", {})
        chatroom_id = chatroom.get("id")
        user_id = data.get("user_id")
        followers = data.get("followersCount", 0)

        channel_ulid = None
        try:
            goals_resp = client.get(f"https://kick.com/api/v2/channels/{slug_norm}/goals", timeout=8)
            if goals_resp.status_code == 200:
                goals_data = goals_resp.json()
                if isinstance(goals_data, list) and len(goals_data) > 0:
                    channel_ulid = goals_data[0].get("channel_id")
        except Exception:
            pass

        resolved = {
            "slug": slug_norm,
            "channel_id": channel_id,
            "chatroom_id": chatroom_id,
            "user_id": user_id,
            "channel_ulid": channel_ulid,
            "followers_count": followers,
            "raw_data": data,
        }
        cls._cache[slug_norm] = resolved
        return resolved

class KickLiveMonitor:
    def __init__(
        self,
        channel_slug: str = "theandro2k",
        room_id: Optional[int] = None,
        cluster: str = DEFAULT_PUSHER_CLUSTER,
        key: str = DEFAULT_PUSHER_KEY,
        raw_mode: bool = False,
        save_log: bool = True,
        log_path: Optional[str] = None,
    ):
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
        self.event_counts: Dict[str, int] = {}
        self.start_time: Optional[float] = None

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
            logs_dir = os.path.join(PROJECT_ROOT, "resources", "logs")
            os.makedirs(logs_dir, exist_ok=True)
            if not self.log_filepath:
                slug_tag = self.channel_slug or f"room_{self.room_id or 'kick'}"
                dt_tag = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.log_filepath = os.path.join(logs_dir, f"ws_{slug_tag}_{dt_tag}.log")
            self.log_file_handle = open(self.log_filepath, "a", encoding="utf-8")
            self._log(f"📝 Registrando sesión en: {os.path.abspath(self.log_filepath)}")
        except Exception as e:
            print(f"⚠️ No se pudo inicializar archivo de log: {e}")

    def start(self):
        self._init_logging_file()

        if self.channel_slug and not self.room_id:
            info = KickChannelResolver.resolve_channel(self.channel_slug)
            if info:
                self.channel_id = info["channel_id"]
                self.room_id = info["chatroom_id"]
                self._log(f"✅ Canal resuelto: ID={self.channel_id} | Chatroom ID={self.room_id} | Seguidores={info['followers_count']}")
            else:
                self._log(f"❌ No se pudo resolver la información del canal '{self.channel_slug}'.")

        if not self.room_id:
            self._log("❌ Error: No se cuenta con un room_id válido para conectar.")
            return

        ws_url = f"wss://ws-{self.cluster}.pusher.com/app/{self.key}?protocol=7&client=js&version=7.6.0"
        mode_str = "📦 MODO RAW (JSON COMPLETO)" if self.raw_mode else "💬 MODO FORMATEADO"
        self._log(f"\n🚀 Conectando a Kick Pusher ({ws_url})...")
        self._log(f"📺 Room ID: {self.room_id} (Canal: {self.channel_slug})")
        self._log(f"💡 {mode_str} activo. Presione Ctrl+C para detener.\n" + "=" * 70)

        self.start_time = time.time()
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        try:
            self.ws.run_forever(ping_interval=30, ping_timeout=10)
        except KeyboardInterrupt:
            self._log("\n👋 Sesión detenida por el usuario.")
            self._print_stats()

    def _on_open(self, ws):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self._log(f"🟢 Conexión WebSocket establecida ({now_str})")
        
        ws.send(json.dumps({
            "event": "pusher:subscribe",
            "data": {"auth": "", "channel": f"chatrooms.{self.room_id}.v2"}
        }))

        if self.channel_id:
            ws.send(json.dumps({
                "event": "pusher:subscribe",
                "data": {"auth": "", "channel": f"channel.{self.channel_id}"}
            }))

    def _on_message(self, ws, message_str: str):
        try:
            data = json.loads(message_str)
        except Exception:
            self._log(f"[RAW MSG ERROR PARSING]: {message_str}")
            return

        event = data.get("event", "UNKNOWN_EVENT")
        channel = data.get("channel", "")
        raw_event_data = data.get("data", "")
        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        self.event_counts[event] = self.event_counts.get(event, 0) + 1

        if self.raw_mode:
            self._log(f"\n📦 [{now_str}] EVENTO: '{event}' | CANAL: '{channel}'")
            self._log(json.dumps(data, indent=2, ensure_ascii=False))
            return

        if event == "pusher:connection_established":
            self._log(f"⚡ [{now_str}] Pusher Handshake completado.")
        elif event == "pusher_internal:subscription_succeeded":
            self._log(f"✅ [{now_str}] Suscripción confirmada: {channel}")
        elif event == "pusher:ping":
            ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
        elif event == "App\\Events\\ChatMessageEvent":
            self._handle_chat_message(raw_event_data, now_str)
        elif event in ("App\\Events\\ChatMessageDeletedEvent", "App\\Events\\MessageDeletedEvent", "MessageDeletedEvent"):
            self._log(f"🗑️ [{now_str}] Mensaje eliminado por moderador.")
        elif event == "App\\Events\\ChatroomClearEvent":
            self._log(f"🧹 [{now_str}] ¡CHAT LIMPIADO! (/clear ejecutado por un moderador)")
        elif event in ("App\\Events\\UserBannedEvent", "UserBannedEvent"):
            self._log(f"🔨 [{now_str}] Usuario baneado o silenciado temporalmente.")
        elif event == "App\\Events\\UserUnbannedEvent":
            self._log(f"🕊️ [{now_str}] Usuario desbaneado.")
        elif event == "App\\Events\\PollUpdateEvent":
            self._log(f"📊 [{now_str}] Encuesta actualizada.")
        elif event == "App\\Events\\PollDeleteEvent":
            self._log(f"🗑️ [{now_str}] Encuesta finalizada/eliminada.")
        elif event == "App\\Events\\PinnedMessageCreatedEvent":
            self._log(f"📌 [{now_str}] Mensaje fijado en el canal.")
        elif event == "App\\Events\\PinnedMessageDeletedEvent":
            self._log(f"📌 [{now_str}] Mensaje fijado retirado.")
        elif event == "App\\Events\\SubscriptionEvent":
            self._log(f"⭐ [{now_str}] ¡NUEVA SUSCRIPCIÓN / RENOVACIÓN!")
        elif event in ("App\\Events\\GiftedSubscriptionsEvent", "GiftedSubscriptionsEvent"):
            self._log(f"🎁 [{now_str}] ¡SUSCRIPCIONES DE REGALO ENTREGADAS!")
        elif event in ("ChatKicksGiftEvent", "App\\Events\\ChatKicksGiftEvent"):
            self._log(f"🪙 [{now_str}] ¡REGALO DE KICKS EN EL CHAT!")
        elif event in ("RewardRedeemedEvent", "App\\Events\\RewardRedeemedEvent"):
            self._log(f"💎 [{now_str}] ¡RECOMPENSA DE PUNTOS CANJEADA!")
        elif event in ("GoalProgressUpdateEvent", "GoalAchievedEvent", "GoalUpdatedEvent"):
            self._log(f"🎯 [{now_str}] META DEL CANAL ACTUALIZADA: {event}")
        elif event in ("App\\Events\\StreamHostedEvent", "App\\Events\\StreamHostEvent"):
            self._log(f"🚀 [{now_str}] ¡HOSTING / RAID RECIBIDO!")
        elif event == "App\\Events\\StreamerIsLive":
            self._log(f"🔴 [{now_str}] ¡EL STREAMER HA INICIADO DIRECTO!")
        elif event == "App\\Events\\StopStreamBroadcast":
            self._log(f"⚫ [{now_str}] El streamer ha finalizado la transmisión.")
        elif event == "App\\Events\\LivestreamUpdated":
            self._log(f"📝 [{now_str}] Metadatos de transmisión actualizados (Categoría/Título).")
        else:
            self._log(f"⚡ [{now_str}] EVENTO: '{event}' en '{channel}'")

    def _handle_chat_message(self, raw_event_data: Any, now_str: str):
        try:
            inner = json.loads(raw_event_data) if isinstance(raw_event_data, str) else raw_event_data
            sender = inner.get("sender", {})
            username = sender.get("username", "Desconocido")
            slug = sender.get("slug", "")
            content = inner.get("content", "")
            msg_id = inner.get("id", "")
            identity = sender.get("identity", {})
            raw_badges = identity.get("badges", [])
            badges = [b.get("type", "") for b in raw_badges]
            badge_str = f"[{', '.join(badges)}]" if badges else "[]"

            self._log("--------------------------------------------------")
            self._log(f"📩 [{now_str}] #{msg_id} {username} (@{slug}) {badge_str}:")
            self._log(f"   💬 {content}")
        except Exception as e:
            self._log(f"⚠️ [{now_str}] Error formateando ChatMessageEvent: {e}")

    def _on_error(self, ws, error):
        self._log(f"❌ Error WebSocket: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        self._log(f"\n🔴 Conexión cerrada. ({close_status_code}: {close_msg})")
        self._print_stats()

    def _print_stats(self):
        if not self.start_time:
            return
        elapsed = max(1.0, time.time() - self.start_time)
        self._log("\n" + "=" * 70)
        self._log("📊 RESUMEN DE MONITOREO DE KICK")
        self._log("=" * 70)
        self._log(f"⏱️ Tiempo transcurrido: {int(elapsed)} segundos")
        self._log(f"📺 Canal: {self.channel_slug or self.room_id}")
        self._log("📈 Total de eventos recibidos por tipo:")
        for ev, count in sorted(self.event_counts.items(), key=lambda x: x[1], reverse=True):
            self._log(f"   • {ev}: {count}")
        chat_count = self.event_counts.get("App\\Events\\ChatMessageEvent", 0)
        msg_per_min = round((chat_count / elapsed) * 60, 2)
        self._log(f"💬 Promedio de chat: {msg_per_min} mensajes/minuto")
        if self.log_filepath:
            self._log(f"📁 Log guardado en: {os.path.abspath(self.log_filepath)}")
        self._log("=" * 70)

        if self.log_file_handle:
            try:
                self.log_file_handle.close()
                self.log_file_handle = None
            except Exception:
                pass

class KickEventSniffer:
    def __init__(self, channel_slug: str = "theandro2k", cluster: str = DEFAULT_PUSHER_CLUSTER, key: str = DEFAULT_PUSHER_KEY):
        self.channel_slug = channel_slug
        self.cluster = cluster
        self.key = key
        self.ws = None

    def start(self):
        print(f"\n=======================================================")
        print(f"📡 MINI-KICK: SNIFFER PROFUNDO DE EVENTOS MULTI-CANAL")
        print(f"=======================================================")
        print(f"Resolviendo canal '{self.channel_slug}'...")

        info = KickChannelResolver.resolve_channel(self.channel_slug)
        if not info:
            print(f"[X] No se pudo resolver el canal '{self.channel_slug}'.")
            return

        chatroom_id = info.get("chatroom_id")
        channel_id = info.get("channel_id")
        user_id = info.get("user_id")
        channel_ulid = info.get("channel_ulid")
        followers = info.get("followers_count", 0)

        print(f"-> Chatroom ID:  {chatroom_id}")
        print(f"-> Channel ID:   {channel_id}")
        print(f"-> User ID:      {user_id}")
        if channel_ulid:
            print(f"-> Channel ULID: {channel_ulid}")
        print(f"-> Seguidores:   {followers}")
        print(f"-------------------------------------------------------")

        channels_to_listen = [
            f"chatrooms.{chatroom_id}.v2",
            f"chatrooms.{chatroom_id}",
            f"chatroom_{chatroom_id}",
            f"channel_{channel_id}",
            f"channel.{channel_id}",
            f"user_{user_id}",
            f"user.{user_id}",
            f"users.{user_id}",
        ]
        if channel_ulid:
            channels_to_listen.extend([
                f"{channel_ulid}",
                f"channel_{channel_ulid}",
                f"channel.{channel_ulid}",
            ])

        ws_url = f"wss://ws-{self.cluster}.pusher.com/app/{self.key}?protocol=7&client=js&version=7.6.0"

        def on_open(ws):
            print(f"✅ Conectado a Pusher WebSocket ({self.cluster}).")
            print(f"📡 Enviando suscripciones a {len(channels_to_listen)} canales:")
            for ch in channels_to_listen:
                ws.send(json.dumps({"event": "pusher:subscribe", "data": {"channel": ch}}))
            print(f"-------------------------------------------------------")
            print(f"👀 Escuchando eventos en vivo...")
            print(f"👉 Realiza un seguimiento, canje de puntos, regalo de Kicks o acción en Kick para observar qué canal reacciona.")
            print(f"Presiona Ctrl+C para salir.\n")

        def on_message(ws, msg):
            try:
                d = json.loads(msg)
                evt = d.get("event")
                ch = d.get("channel", "N/A")

                if evt in ("pusher:connection_established", "pusher:pong"):
                    return
                if evt == "pusher:ping":
                    ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
                    return
                if evt == "pusher_internal:subscription_succeeded":
                    print(f"   [✓] Suscripción aceptada: {ch}")
                    return
                if evt in ("pusher:error", "pusher_internal:subscription_error"):
                    print(f"   [✗] Error en canal {ch}: {d.get('data')}")
                    return

                raw_data = d.get("data", "")
                try:
                    parsed_data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                except Exception:
                    parsed_data = raw_data

                ts = datetime.datetime.now().strftime("%H:%M:%S")

                if "Kicks" in evt or "kicks" in evt.lower():
                    print(f"\n🪙 [{ts}] ¡REGALO DE KICKS DETECTADO!")
                    print(f"   Canal:  {ch} | Evento: {evt}")
                    print(f"   Payload: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
                elif "Reward" in evt or "reward" in evt.lower():
                    print(f"\n🎁 [{ts}] ¡CANJE DE PUNTOS DETECTADO!")
                    print(f"   Canal:  {ch} | Evento: {evt}")
                    print(f"   Payload: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
                elif "Goal" in evt or "goal" in evt.lower():
                    print(f"\n🎯 [{ts}] ¡EVENTO DE META DEL CANAL (GOAL) DETECTADO!")
                    print(f"   Canal:  {ch} | Evento: {evt}")
                    print(f"   Payload: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
                elif "Clear" in evt or "clear" in evt.lower():
                    print(f"\n🧹 [{ts}] ¡COMANDO /CLEAR DETECTADO EN EL CHAT!")
                    print(f"   Canal:  {ch} | Evento: {evt}")
                elif "Follow" in evt or "follow" in evt.lower():
                    print(f"\n👥 [{ts}] ¡EVENTO DE FOLLOWER DETECTADO!")
                    print(f"   Canal:  {ch} | Evento: {evt}")
                    print(f"   Payload: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
                elif "Subscription" in evt or "subscription" in evt.lower():
                    print(f"\n⭐ [{ts}] ¡EVENTO DE SUSCRIPCIÓN DETECTADO!")
                    print(f"   Canal:  {ch} | Evento: {evt}")
                    print(f"   Payload: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
                elif "Host" in evt or "host" in evt.lower() or "raid" in evt.lower():
                    print(f"\n🚀 [{ts}] ¡RAID / HOSTING DETECTADO!")
                    print(f"   Canal:  {ch} | Evento: {evt}")
                    print(f"   Payload: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
                else:
                    print(f"\n⚡ [{ts}] EVENTO RECIBIDO: '{evt}' en '{ch}'")
                    print(f"   Payload: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
            except Exception as e:
                print(f"[!] Error parseando mensaje de WebSocket: {e}")

        def on_error(ws, err):
            print(f"[X] Error WebSocket: {err}")

        def on_close(ws, code, reason):
            print(f"[-] Conexión cerrada ({code}): {reason}")

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        try:
            self.ws.run_forever(ping_interval=25, ping_timeout=15)
        except KeyboardInterrupt:
            print("\nSniffer finalizado por el usuario.")

class KickFrontendScraper:
    @classmethod
    def run_scan(cls, target_channel: str = "theandro2k", max_scripts: int = 80) -> Dict[str, Any]:
        print("=" * 65)
        print("🔬 INSPECTOR PROFUNDO DE CHUNKS TURBOPACK & EVENTOS DE KICK")
        print("=" * 65)
        print(f"Target: https://kick.com/{target_channel}")

        client = KickChannelResolver.get_http_client()
        urls: Set[str] = set()

        pages = [f"https://kick.com/{target_channel}"]
        for page in pages:
            try:
                r = client.get(page, timeout=12)
                if r.status_code == 200:
                    for m in re.findall(r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']', r.text):
                        urls.add(m if m.startswith("http") else f"https://kick.com{m}")

                    for m in re.findall(r'static/chunks/([a-zA-Z0-9_\-\.]+)\.js', r.text):
                        urls.add(f"https://assets.kick.com/main/_next/static/chunks/{m}.js")
            except Exception as e:
                print(f"⚠️ Error al leer {page}: {e}")

        print(f"[*] Total scripts y chunks identificados: {len(urls)}")
        urls_to_scan = sorted(urls)[:max_scripts]
        print(f"[*] Escaneando los primeros {len(urls_to_scan)} scripts principales...")

        events_found: Set[str] = set()
        channels_found: Set[str] = set()
        pusher_keys_found: Set[str] = set()

        scanned_count = 0
        for u in urls_to_scan:
            if "cloudflare" in u or "challenge" in u:
                continue
            try:
                resp = client.get(u, timeout=8)
                if resp.status_code != 200:
                    continue
                code = resp.text
                scanned_count += 1

                for k in re.findall(r'["\']([0-9a-f]{20})["\']', code):
                    pusher_keys_found.add(k)

                for ev in re.findall(r'App\\\\Events\\\\[a-zA-Z0-9_]+', code):
                    events_found.add(ev.replace("\\\\", "\\"))
                for ev in re.findall(r'App\\Events\\[a-zA-Z0-9_]+', code):
                    events_found.add(ev)

                for ev in re.findall(r'["\']([a-zA-Z0-9_]+Event)["\']', code):
                    if not any(ign in ev for ign in ("Animation", "Transition", "Pointer", "Touch", "Mouse", "Keyboard", "Composition", "Input", "Text")):
                        events_found.add(ev)

                for ev in re.findall(r'["\']((?:StreamerIsLive|StopStreamBroadcast|LivestreamUpdated|GoalAchievedEvent|GoalProgressUpdateEvent))["\']', code):
                    events_found.add(ev)

                for ch in re.findall(r'[`"\']([a-zA-Z0-9_\-\.]+[\.\_]\$\{[^\}]+\}[^`"\']*)[`"\']', code):
                    if any(k in ch for k in ("channel", "chatroom", "user", "stream", "feed")):
                        channels_found.add(ch)

                for ch in re.findall(r'["\']((?:chatrooms?\.[^"\']+|channels?\.[^"\']+|users?\.[^"\']+|private-[^"\']+))["\']', code):
                    channels_found.add(ch)

            except Exception:
                pass

        print(f"\n[✓] {scanned_count} scripts analizados con éxito.")

        categories: Dict[str, List[str]] = {
            "💬 Chat & Interacción": [],
            "🛡️ Moderación": [],
            "🪙 Monetización & Kicks": [],
            "🎯 Metas & Goals": [],
            "📺 Estado de Stream & Raids": [],
            "⚙️ Otros Eventos": [],
        }

        for ev in sorted(events_found):
            ev_lower = ev.lower()
            if any(k in ev_lower for k in ("clear", "ban", "delete")):
                categories["🛡️ Moderación"].append(ev)
            elif any(k in ev_lower for k in ("kicks", "sub", "gift", "reward")):
                categories["🪙 Monetización & Kicks"].append(ev)
            elif "goal" in ev_lower:
                categories["🎯 Metas & Goals"].append(ev)
            elif any(k in ev_lower for k in ("stream", "live", "host", "broadcast")):
                categories["📺 Estado de Stream & Raids"].append(ev)
            elif any(k in ev_lower for k in ("chat", "poll", "pin")):
                categories["💬 Chat & Interacción"].append(ev)
            else:
                categories["⚙️ Otros Eventos"].append(ev)

        for cat_name, ev_list in categories.items():
            if ev_list:
                print(f"\n{cat_name}:")
                for ev in ev_list:
                    print(f"   • {ev}")

        print("\n📡 PLANTILLAS DE CANALES ENCONTRADAS:")
        for ch in sorted(channels_found):
            print(f"   • {ch}")

        if pusher_keys_found:
            print("\n🔑 PUSHER KEYS DETECTADAS:")
            for k in sorted(pusher_keys_found):
                print(f"   • {k}")

        return {
            "target_channel": target_channel,
            "events_by_category": categories,
            "channels": sorted(channels_found),
            "pusher_keys": sorted(pusher_keys_found),
        }

class KickEventAuditor:
    KNOWN_KICK_EVENTS: Dict[str, Dict[str, str]] = {
        "App\\Events\\ChatMessageEvent": {
            "desc": "Mensajes estándar de chat de usuarios",
            "category": "Chat",
            "importance": "CRÍTICA",
        },
        "App\\Events\\ChatMessageDeletedEvent": {
            "desc": "Eliminación de mensaje individual",
            "category": "Moderación",
            "importance": "ALTA",
        },
        "App\\Events\\MessageDeletedEvent": {
            "desc": "Alias de eliminación de mensaje",
            "category": "Moderación",
            "importance": "ALTA",
        },
        "App\\Events\\ChatroomClearEvent": {
            "desc": "Limpieza total de chat (/clear)",
            "category": "Moderación",
            "importance": "MEDIA",
        },
        "App\\Events\\UserBannedEvent": {
            "desc": "Baneo o timeout de usuario",
            "category": "Moderación",
            "importance": "ALTA",
        },
        "App\\Events\\UserUnbannedEvent": {
            "desc": "Desbaneo de usuario",
            "category": "Moderación",
            "importance": "BAJA",
        },
        "App\\Events\\PollUpdateEvent": {
            "desc": "Creación o voto en encuesta",
            "category": "Interacción",
            "importance": "MEDIA",
        },
        "App\\Events\\PollDeleteEvent": {
            "desc": "Finalización o eliminación de encuesta",
            "category": "Interacción",
            "importance": "MEDIA",
        },
        "App\\Events\\PinnedMessageCreatedEvent": {
            "desc": "Mensaje fijado en el canal",
            "category": "Interacción",
            "importance": "MEDIA",
        },
        "App\\Events\\PinnedMessageDeletedEvent": {
            "desc": "Retiro de mensaje fijado",
            "category": "Interacción",
            "importance": "MEDIA",
        },
        "RewardRedeemedEvent": {
            "desc": "Canje de recompensas de puntos",
            "category": "Monetización",
            "importance": "ALTA",
        },
        "App\\Events\\SubscriptionEvent": {
            "desc": "Nueva suscripción o renovación",
            "category": "Monetización",
            "importance": "ALTA",
        },
        "GiftedSubscriptionsEvent": {
            "desc": "Suscripciones de regalo individuales/masivas",
            "category": "Monetización",
            "importance": "ALTA",
        },
        "ChatKicksGiftEvent": {
            "desc": "Regalos de Kicks (moneda virtual / cheers)",
            "category": "Monetización",
            "importance": "OPORTUNIDAD",
        },
        "GoalProgressUpdateEvent": {
            "desc": "Avance en tiempo real de metas del canal",
            "category": "Metas (Goals)",
            "importance": "OPORTUNIDAD",
        },
        "GoalAchievedEvent": {
            "desc": "Meta completada al 100%",
            "category": "Metas (Goals)",
            "importance": "OPORTUNIDAD",
        },
        "App\\Events\\StreamHostedEvent": {
            "desc": "Raid o hosting entrante",
            "category": "Stream",
            "importance": "OPORTUNIDAD",
        },
        "App\\Events\\LivestreamUpdated": {
            "desc": "Cambio de categoría o título del stream",
            "category": "Stream",
            "importance": "OPORTUNIDAD",
        },
        "App\\Events\\StreamerIsLive": {
            "desc": "Inicio de transmisión en vivo",
            "category": "Stream",
            "importance": "BAJA",
        },
        "App\\Events\\StopStreamBroadcast": {
            "desc": "Fin de transmisión en vivo",
            "category": "Stream",
            "importance": "BAJA",
        },
    }

    @classmethod
    def get_minikick_supported_events(cls) -> Set[str]:
        try:
            from backend.providers.chat.kick_ws_provider import KickWebSocketManager
            mgr = KickWebSocketManager(cluster="us2", keys=("dummy",))
            return set(mgr._dispatch_table.keys())
        except Exception:
            return {
                "App\\Events\\ChatMessageEvent",
                "App\\Events\\PollUpdateEvent",
                "App\\Events\\PollDeleteEvent",
                "App\\Events\\PinnedMessageCreatedEvent",
                "App\\Events\\PinnedMessageDeletedEvent",
                "RewardRedeemedEvent",
                "App\\Events\\RewardRedeemedEvent",
                "App\\Events\\ChatMessageDeletedEvent",
                "App\\Events\\MessageDeletedEvent",
                "MessageDeletedEvent",
                "App\\Events\\UserBannedEvent",
                "UserBannedEvent",
                "pusher:connection_established",
                "pusher:ping",
            }

    @classmethod
    def run_comparison(cls, as_json: bool = False) -> Dict[str, Any]:
        minikick_events = cls.get_minikick_supported_events()

        implemented: List[Dict[str, str]] = []
        opportunities: List[Dict[str, str]] = []

        for ev_name, info in cls.KNOWN_KICK_EVENTS.items():
            is_supported = ev_name in minikick_events or (
                ev_name.startswith("App\\Events\\") and ev_name.replace("App\\Events\\", "") in minikick_events
            )
            item = {
                "event": ev_name,
                "description": info["desc"],
                "category": info["category"],
                "importance": info["importance"],
                "supported_in_minikick": is_supported,
            }
            if is_supported:
                implemented.append(item)
            else:
                opportunities.append(item)

        total_catalog = len(cls.KNOWN_KICK_EVENTS)
        implemented_count = len(implemented)
        coverage_pct = round((implemented_count / total_catalog) * 100, 1)

        result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "coverage_percentage": coverage_pct,
            "total_catalog_events": total_catalog,
            "implemented_in_minikick": implemented_count,
            "opportunities_count": len(opportunities),
            "implemented": implemented,
            "opportunities": opportunities,
        }

        if as_json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result

        print("=" * 80)
        print("  📊 MATRIZ COMPARATIVA: KICK WEBSOCKETS VS MINIKICK")
        print("=" * 80)
        print(f"Cobertura Actual de Eventos : {coverage_pct}% ({implemented_count}/{total_catalog} eventos)")
        print(f"Oportunidades de Expansión  : {len(opportunities)} eventos nuevos")
        print("-" * 80)

        print("\n✅ EVENTOS ACTUALMENTE SOPORTADOS POR MINIKICK:")
        for item in implemented:
            print(f"  [✓] {item['event']:<38} | {item['category']:<14} | {item['description']}")

        print("\n💡 OPORTUNIDADES PARA INTEGRAR EN MINIKICK:")
        for item in opportunities:
            print(f"  [+] {item['event']:<38} | {item['category']:<14} | {item['description']}")

        print("\n" + "=" * 80)
        return result

class KickOfficialApiTester:
    CONFIG_PATH = os.path.join(PROJECT_ROOT, "resources", "tools", "kick_api_config.json")
    CACHE_PATH = os.path.join(PROJECT_ROOT, "resources", "tools", ".kick_token_cache.json")

    @classmethod
    def load_credentials(cls) -> Tuple[Optional[str], Optional[str], int, str]:
        client_id = None
        client_secret = None
        broadcaster_uid = 32253592
        source = ".env"

        if os.path.exists(cls.CONFIG_PATH):
            try:
                with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    client_id = cfg.get("client_id")
                    client_secret = cfg.get("client_secret")
                    broadcaster_uid = cfg.get("broadcaster_user_id", broadcaster_uid)
                    source = "resources/tools/kick_api_config.json"
            except Exception:
                pass

        if not client_id or not client_secret:
            client_id = os.getenv("KICK_CLIENT_ID")
            client_secret = os.getenv("KICK_CLIENT_SECRET")
            source = ".env"

        return client_id, client_secret, broadcaster_uid, source

    @classmethod
    def get_access_token(cls, client_id: str, client_secret: str) -> Optional[Tuple[str, str, int, bool]]:
        now = time.time()

        if os.path.exists(cls.CACHE_PATH):
            try:
                with open(cls.CACHE_PATH, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    exp_at = cached.get("expires_at", 0)
                    token = cached.get("access_token")
                    ttype = cached.get("token_type", "Bearer")
                    if token and exp_at > now + 120:
                        rem_sec = int(exp_at - now)
                        return token, ttype, rem_sec, True
            except Exception:
                pass

        token_url = "https://id.kick.com/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        try:
            resp = requests.post(token_url, data=payload, headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"[X] Falló la obtención de token HTTP {resp.status_code}: {resp.text}")
                return None

            data = resp.json()
            token = data.get("access_token")
            ttype = data.get("token_type", "Bearer")
            exp_in = data.get("expires_in", 3600)

            try:
                with open(cls.CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump({
                        "access_token": token,
                        "token_type": ttype,
                        "expires_at": now + exp_in,
                        "saved_at": datetime.datetime.now().isoformat(),
                    }, f, indent=2)
            except Exception:
                pass

            return token, ttype, exp_in, False
        except Exception as e:
            print(f"[X] Error solicitando token a id.kick.com: {e}")
            return None

    @classmethod
    def run_diagnostics(cls, broadcaster_user_id: Optional[int] = None) -> bool:
        print("=" * 65)
        print("🧪 TEST DE API OFICIAL DE KICK (CLIENT CREDENTIALS)")
        print("=" * 65)

        client_id, client_secret, default_uid, source = cls.load_credentials()
        target_uid = broadcaster_user_id or default_uid

        if not client_id or not client_secret:
            print(f"[X] ERROR: Credenciales de Kick no encontradas en {cls.CONFIG_PATH} ni en .env")
            return False

        masked_id = client_id[:6] + "..." + client_id[-4:] if len(client_id) > 10 else "***"
        print(f"[*] Origen de credenciales: \033[1;36m{source}\033[0m")
        print(f"[*] Client ID detectado   : {masked_id}")
        print(f"[*] Broadcaster User ID   : {target_uid}")

        res = cls.get_access_token(client_id, client_secret)
        if not res:
            return False

        token, token_type, expires_in, was_cached = res
        cache_str = "⚡ Desde Caché O(1)" if was_cached else "🌐 Solicitado a id.kick.com"
        print(f"✅ TOKEN DISPONIBLE ({cache_str}):")
        print(f"   • Tipo:       {token_type}")
        print(f"   • Válido por: {expires_in} segundos (~{round(expires_in / 86400, 1)} días)")
        print("-" * 65)

        auth_headers = {
            "Authorization": f"{token_type} {token}",
            "Accept": "application/json",
        }

        ch_url = f"https://api.kick.com/public/v1/channels?broadcaster_user_id={target_uid}"
        print(f"\n-> [GET] {ch_url}")
        try:
            r = requests.get(ch_url, headers=auth_headers, timeout=10)
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                payload = r.json()
                channels_data = payload.get("data", [])
                if channels_data:
                    ch_info = channels_data[0]
                    stream_info = ch_info.get("stream", {})
                    is_live = stream_info.get("is_live", False)
                    live_str = "\033[1;32mEN VIVO\033[0m" if is_live else "\033[1;31mOFFLINE\033[0m"
                    print(f"   📺 Canal: \033[1;33m@{ch_info.get('slug')}\033[0m (ID={ch_info.get('broadcaster_user_id')})")
                    print(f"   🔴 Estado Stream: {live_str}")
                    if is_live:
                        print(f"   🎮 Categoría / Juego: {stream_info.get('language')}")
                        print(f"   ⏱️ Inicio: {stream_info.get('start_time')}")
                else:
                    print(f"   Payload: {json.dumps(payload, indent=2, ensure_ascii=False)[:300]}")
            else:
                print(f"   Respuesta: {r.text[:200]}")
        except Exception as e:
            print(f"   ⚠️ Error en consulta: {e}")

        ev_url = "https://api.kick.com/public/v1/events/subscriptions"
        print(f"\n-> [GET] {ev_url}")
        try:
            r = requests.get(ev_url, headers=auth_headers, timeout=10)
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                subs = r.json().get("data", [])
                print(f"   📋 Total suscripciones a eventos registradas: {len(subs)}")
                for s in subs:
                    print(f"      • {s}")
            else:
                print(f"   Respuesta: {r.text[:200]}")
        except Exception as e:
            print(f"   ⚠️ Error en consulta: {e}")

        print("\n" + "=" * 65)
        return True

def interactive_menu():
    active_slug = "theandro2k"

    while True:
        info = KickChannelResolver.resolve_channel(active_slug)
        room_str = str(info["chatroom_id"]) if info else "N/A"
        cid_str = str(info["channel_id"]) if info else "N/A"
        folls = info.get("followers_count", 0) if info else 0

        print("\n" + "=" * 68)
        print("             MINIKICK - KICK UNIFIED TOOLKIT (v1.6.0)")
        print("=" * 68)
        print(f" 📺 Canal Activo : \033[1;32m{active_slug}\033[0m | Room: {room_str} | ID: {cid_str} | Seguidores: {folls}")
        print("-" * 68)
        print("  1. 💬 Monitor de Chat & Eventos en Vivo (WebSocket Pusher)")
        print("  2. 📡 Sniffer Multi-Canal Profundo (Kicks, Metas, Rewards, Raids)")
        print("  3. 🔬 Scraper de Chunks Web (Descubrimiento Turbopack/Next.js)")
        print("  4. 📊 Matriz Comparativa: Kick WebSockets vs MiniKick (Gaps)")
        print("  5. 🧪 Diagnóstico de API Oficial de Kick (OAuth & Webhooks)")
        print("  6. 🔄 Cambiar Canal Activo")
        print("  0. 🚪 Salir")
        print("=" * 68)

        try:
            choice = input("Selecciona una opción (0-6) [1]: ").strip() or "1"
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Operación cancelada.")
            break

        if choice == "1":
            raw_in = input("¿Activar modo RAW JSON completo? (s/n) [n]: ").strip().lower()
            raw_mode = raw_in in ("s", "si", "y", "yes", "1")
            monitor = KickLiveMonitor(channel_slug=active_slug, raw_mode=raw_mode)
            monitor.start()

        elif choice == "2":
            sniffer = KickEventSniffer(channel_slug=active_slug)
            sniffer.start()

        elif choice == "3":
            KickFrontendScraper.run_scan(target_channel=active_slug)

        elif choice == "4":
            KickEventAuditor.run_comparison(as_json=False)

        elif choice == "5":
            default_uid = info.get("user_id", 32253592) if info else 32253592
            uid_str = input(f"Broadcaster User ID a consultar [{default_uid}]: ").strip() or str(default_uid)
            try:
                uid = int(uid_str)
            except ValueError:
                uid = default_uid
            KickOfficialApiTester.run_diagnostics(broadcaster_user_id=uid)

        elif choice == "6":
            new_slug = input(f"Nuevo slug de canal [{active_slug}]: ").strip()
            if new_slug:
                new_info = KickChannelResolver.resolve_channel(new_slug, force_refresh=True)
                if new_info:
                    active_slug = new_slug.lower()
                    print(f"✅ Canal cambiado exitosamente a '{active_slug}'.")
                else:
                    print(f"⚠️ No se encontró el canal '{new_slug}'. Se mantiene '{active_slug}'.")

        elif choice in ("0", "q", "exit", "salir"):
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("[X] Opción inválida. Intenta nuevamente.")


def main():
    parser = argparse.ArgumentParser(
        description="Kick Unified Toolkit - Herramienta Unificada de Diagnóstico y Monitoreo de Kick",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--monitor", "--chat", action="store_true", help="Iniciar monitor de chat y eventos en vivo")
    parser.add_argument("--sniff", action="store_true", help="Iniciar sniffer multi-canal profundo (rewards/follows/kicks/metas)")
    parser.add_argument("--scrape", action="store_true", help="Escanear scripts de Turbopack/Next.js para descubrir canales y eventos")
    parser.add_argument("--compare", "--audit", action="store_true", help="Generar matriz comparativa entre WebSockets de Kick y MiniKick")
    parser.add_argument("--api", action="store_true", help="Ejecutar diagnóstico de API oficial de Kick (OAuth)")
    parser.add_argument("--slug", "-s", type=str, default="theandro2k", help="Slug del canal de Kick (default: theandro2k)")
    parser.add_argument("--room-id", "-r", type=int, default=None, help="Room ID numérico explícito si se conoce")
    parser.add_argument("--raw", action="store_true", help="Modo RAW JSON completo para eventos")
    parser.add_argument("--no-log", action="store_true", help="Desactivar creación de archivo de log")
    parser.add_argument("--log-path", type=str, default=None, help="Ruta personalizada para archivo de log")
    parser.add_argument("--broadcaster-id", type=int, default=32253592, help="User ID para diagnóstico de API oficial")
    parser.add_argument("--json", action="store_true", help="Exportar reporte en formato JSON")

    args, unknown = parser.parse_known_args()

    if args.compare:
        res = KickEventAuditor.run_comparison(as_json=args.json)
        sys.exit(0)
    elif args.scrape:
        res = KickFrontendScraper.run_scan(target_channel=args.slug)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        sys.exit(0)
    elif args.monitor:
        monitor = KickLiveMonitor(
            channel_slug=args.slug,
            room_id=args.room_id,
            raw_mode=args.raw,
            save_log=not args.no_log,
            log_path=args.log_path,
        )
        monitor.start()
    elif args.sniff:
        sniffer = KickEventSniffer(channel_slug=args.slug)
        sniffer.start()
    elif args.api:
        success = KickOfficialApiTester.run_diagnostics(broadcaster_user_id=args.broadcaster_id)
        sys.exit(0 if success else 1)
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
