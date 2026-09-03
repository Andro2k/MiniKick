# backend\services\overlay\overlay_manager.py

from .overlay_routes import OverlayRequestHandler
from .websocket_client import WebSocketClient
import logging
import secrets
import threading
import time
import urllib.parse
from http.server import ThreadingHTTPServer

logger = logging.getLogger("minikick.services.overlay.manager")

class OverlayServerManager:
    def __init__(self, port=8090, settings_storage=None):
        self.port = port
        self.server = None
        self.thread = None

        self.clients = []
        self.chat_clients = []
        self.music_clients = []
        self.widget_clients = []
        self.alert_clients = []
        self.on_alert_finished = None

        self.ws_clients = {
            "rewards": set(),
            "chat": set(),
            "music": set(),
            "widgets": set(),
            "alerts": set()
        }
        self.ws_lock = threading.Lock()

        self._last_song: dict | None = None
        self._last_death_count: int = 0
        self._last_score: dict = {"wins": 0, "losses": 0}
        self._last_death_data: dict = {"count": 0, "is_active": True}
        self._last_score_data: dict = {"wins": 0, "losses": 0, "is_active": True}
        self._last_poll_data: dict | None = None
        self._last_poll_timestamp: float = 0.0
        self._last_pinned_data: dict | None = None
        self.settings_storage = settings_storage
        self.lock = threading.Lock()

        self.session_token = ""
        if self.settings_storage:
            self.session_token = self.settings_storage.load_string("overlay_session_token", "")

        if not self.session_token:
            self.session_token = secrets.token_hex(16)
            if self.settings_storage:
                self.settings_storage.save_string("overlay_session_token", self.session_token)

    def register_ws_client(self, ws_client: WebSocketClient):
        with self.ws_lock:
            topic_set = self.ws_clients.get(ws_client.topic)
            if topic_set is not None:
                topic_set.add(ws_client)

    def unregister_ws_client(self, ws_client: WebSocketClient):
        with self.ws_lock:
            topic_set = self.ws_clients.get(ws_client.topic)
            if topic_set is not None:
                topic_set.discard(ws_client)

    def get_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/overlay?token={self.session_token}"

    def get_chat_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/chat?token={self.session_token}"

    def get_music_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/music?token={self.session_token}"

    def get_shoutout_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/widgets/shoutout?token={self.session_token}"

    def get_death_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/widgets/deaths?token={self.session_token}"

    def get_score_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/widgets/score?token={self.session_token}"

    def get_explosion_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/widgets/emote_explosion?token={self.session_token}"

    def get_combo_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/widgets/emote_combo?token={self.session_token}"

    def get_poll_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/widgets/poll?token={self.session_token}"

    def get_pinned_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/widgets/pinned?token={self.session_token}"

    def get_widgets_overlay_url(self) -> str:
        return self.get_shoutout_overlay_url()

    def get_alerts_overlay_url(self) -> str:
        return f"http://localhost:{self.port}/alerts?token={self.session_token}"

    def start(self):
        try:
            self.server = ThreadingHTTPServer(("127.0.0.1", self.port), OverlayRequestHandler)
            self.server.manager = self

            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logger.info("Overlay server active: %s", self.get_overlay_url())
        except OSError as e:
            logger.error("[OverlayServer] Could not start Overlay server on port %s: %s", self.port, e)

    def _broadcast(self, sse_clients_attr: str, ws_topic: str, payload: dict):
        clients_list = getattr(self, sse_clients_attr)
        with self.lock:
            clients_copy = list(clients_list)
        for client_queue in clients_copy:
            client_queue.put(payload)

        with self.ws_lock:
            ws_copy = list(self.ws_clients.get(ws_topic, []))
        for ws_client in ws_copy:
            ws_client.send_json(payload)

    def trigger_rewards(self, reward_name: str, config: dict):
        if isinstance(config, str):
            config = {"filepath": config, "volume": 1.0, "scale": 1.0, "pos_x": 0, "pos_y": 0}

        filepath = config.get("filepath", "")
        safe_path = urllib.parse.quote(filepath)
        import os
        _, ext = os.path.splitext(filepath.lower())

        payload = {
            "reward": reward_name,
            "file_url": f"http://localhost:{self.port}/media?path={safe_path}&token={self.session_token}",
            "file_ext": ext,
            "volume": config.get("volume", 1.0),
            "scale": config.get("scale", 1.0),
            "pos_x": config.get("pos_x", 0),
            "pos_y": config.get("pos_y", 0),
            "is_random_pos": config.get("is_random_pos", False),
            "duration": config.get("duration", 5.0)
        }

        logger.info("[Overlay] Emitiendo alerta multimedia de recompensa: '%s' (%s)", reward_name, os.path.basename(filepath))
        self._broadcast("clients", "rewards", payload)

    def trigger_alert(self, payload: dict):
        import os
        sound_path = payload.get("sound_path", "")
        media_path = payload.get("media_path", "")

        sound_url = ""
        if sound_path and os.path.exists(sound_path):
            safe_sound = urllib.parse.quote(sound_path)
            sound_url = f"http://localhost:{self.port}/media?path={safe_sound}&token={self.session_token}"

        media_url = ""
        media_ext = ""
        if media_path and os.path.exists(media_path):
            _, ext = os.path.splitext(media_path.lower())
            media_ext = ext
            safe_media = urllib.parse.quote(media_path)
            media_url = f"http://localhost:{self.port}/media?path={safe_media}&token={self.session_token}"

        broadcast_payload = dict(payload)
        broadcast_payload["sound_url"] = sound_url
        broadcast_payload["media_url"] = media_url
        broadcast_payload["media_ext"] = media_ext

        logger.info("[Overlay] Emitiendo alerta en vivo: '%s' (%s)", payload.get("formatted_text"), payload.get("id"))
        self._broadcast("alert_clients", "alerts", broadcast_payload)

    def trigger_chat_message(self, user: str, message: str, color: str, badges: list = None, platform: str = "kick", emotes_tag: str = ""):
        payload = {
            "user": user,
            "message": message,
            "color": color,
            "badges": badges or [],
            "platform": platform,
            "emotes_tag": emotes_tag
        }
        self._broadcast("chat_clients", "chat", payload)

    def trigger_music_change(self, song: dict):
        if not song:
            payload = {"type": "stopped"}
        else:
            payload = {
                "type": "playing",
                "title": song.get("title", ""),
                "artist": song.get("artist", ""),
                "url": song.get("url", ""),
                "is_playing": song.get("is_playing", False),
                "duration": song.get("duration", 0),
                "progress": song.get("progress", 0),
                "thumbnail": song.get("thumbnail", ""),
                "timestamp": time.time() * 1000
            }
        self._last_song = payload
        self._broadcast("music_clients", "music", payload)

    def trigger_widget_event(self, event_type: str, data: dict):
        if event_type == "death_update":
            self._last_death_count = data.get("count", 0)
            self._last_death_data.update(data)
        elif event_type == "score":
            self._last_score = {"wins": data.get("wins", 0), "losses": data.get("losses", 0)}
            self._last_score_data.update(data)
        elif event_type == "poll_update":
            self._last_poll_data = data.get("poll") or data
            self._last_poll_timestamp = time.time()
        elif event_type == "poll_delete":
            self._last_poll_data = None
            self._last_poll_timestamp = 0.0
        elif event_type == "pinned_created":
            self._last_pinned_data = data.get("pinned") or data
        elif event_type == "pinned_deleted":
            self._last_pinned_data = None
        elif event_type == "widget_toggle":
            w_id = data.get("widget_id")
            if w_id == "death":
                self._last_death_data["is_active"] = data.get("is_active", True)
            elif w_id == "score":
                self._last_score_data["is_active"] = data.get("is_active", True)

        payload = {"event": event_type, **data}
        self._broadcast("widget_clients", "widgets", payload)

    def stop(self):
        if self.server:
            with self.ws_lock:
                for topic_set in self.ws_clients.values():
                    for ws_client in list(topic_set):
                        ws_client.close()

            with self.lock:
                clients_copy = list(self.clients)
                chat_copy = list(self.chat_clients)
                music_copy = list(self.music_clients)
                widget_copy = list(self.widget_clients)

            for q in clients_copy + chat_copy + music_copy + widget_copy:
                q.put(None)

            self.server.shutdown()
            self.server.server_close()
