# backend\services\overlay\overlay_server.py

import os
import sys
import json
import queue
import secrets
import logging
import threading
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger("minikick.services.overlay")

def get_resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SSEChannelManager:
    def __init__(self, lock: threading.Lock | None = None):
        self.lock = lock or threading.Lock()
        self._channels: dict[str, list[queue.Queue]] = {}
        self._last_state: dict[str, dict] = {}

    def register_channel(self, channel_name: str) -> None:
        with self.lock:
            if channel_name not in self._channels:
                self._channels[channel_name] = []

    def subscribe(self, channel_name: str) -> queue.Queue:
        client_queue: queue.Queue = queue.Queue()
        with self.lock:
            if channel_name not in self._channels:
                self._channels[channel_name] = []
            self._channels[channel_name].append(client_queue)
        return client_queue

    def unsubscribe(self, channel_name: str, client_queue: queue.Queue) -> None:
        with self.lock:
            clients = self._channels.get(channel_name)
            if clients and client_queue in clients:
                clients.remove(client_queue)

    def set_last_state(self, channel_name: str, state: dict) -> None:
        with self.lock:
            self._last_state[channel_name] = state

    def get_last_state(self, channel_name: str) -> dict | None:
        with self.lock:
            return self._last_state.get(channel_name)

    def broadcast(self, channel_name: str, payload: dict) -> None:
        with self.lock:
            clients = list(self._channels.get(channel_name, []))

        for client_queue in clients:
            client_queue.put(payload)

    def serve_stream(self, handler, channel_name: str, initial_payloads: list[dict] | None = None) -> None:
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-cache")
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.end_headers()

        client_queue = self.subscribe(channel_name)

        if initial_payloads:
            for init_payload in initial_payloads:
                client_queue.put(init_payload)

        try:
            while True:
                try:
                    data = client_queue.get(timeout=2.0)
                    if data is None:
                        break
                    handler.wfile.write(f"data: {json.dumps(data)}\n\n".encode("utf-8"))
                    handler.wfile.flush()
                except queue.Empty:
                    handler.wfile.write(b": keep-alive\n\n")
                    handler.wfile.flush()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            logger.debug("[SSEManager] Stream ended for channel %s: %s", channel_name, e)
        finally:
            self.unsubscribe(channel_name, client_queue)

    def shutdown(self) -> None:
        with self.lock:
            all_queues = [q for clients in self._channels.values() for q in clients]

        for client_queue in all_queues:
            client_queue.put(None)

def serve_html_file(handler, relative_html_path: str, not_found_msg: str = "HTML not found") -> None:
    html_path = get_resource_path(relative_html_path)
    try:
        with open(html_path, "rb") as f:
            handler.send_response(200)
            handler.send_header("Content-Type", "text/html; charset=utf-8")
            handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            handler.send_header("Pragma", "no-cache")
            handler.send_header("Expires", "0")
            handler.end_headers()
            handler.wfile.write(f.read())
    except FileNotFoundError:
        handler.send_error(404, f"{not_found_msg} at: {html_path}")

def serve_media_file(handler, parsed_url) -> None:
    query = parse_qs(parsed_url.query)
    if "path" not in query:
        handler.send_error(400, "Path not specified")
        return
        
    filepath = query["path"][0]
    if not os.path.exists(filepath):
        handler.send_error(404, "Media file not found")
        return
        
    mime_type, _ = mimetypes.guess_type(filepath)
    
    try:
        handler.send_response(200)
        handler.send_header("Content-Type", mime_type or "application/octet-stream")
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.end_headers()
        
        with open(filepath, "rb") as f:
            chunk_size = 1024 * 64
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                handler.wfile.write(chunk)
    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
        pass
    except Exception as e:
        try:
            handler.send_error(500, f"Internal error: {e}")
        except Exception:
            pass

class OverlayRouteRegistry:
    def __init__(self):
        self._exact_routes: dict[str, callable] = {}
        self._setup_default_routes()

    def register_route(self, path: str, handler_func: callable) -> None:
        self._exact_routes[path] = handler_func

    def register_routes(self, paths: list[str], handler_func: callable) -> None:
        for p in paths:
            self._exact_routes[p] = handler_func

    def _setup_default_routes(self) -> None:
        self.register_route(
            "/overlay",
            lambda h, p: serve_html_file(h, os.path.join("assets", "overlays", "rewards", "rewards.html"), "Rewards Overlay HTML not found")
        )
        self.register_route(
            "/chat",
            lambda h, p: serve_html_file(h, os.path.join("assets", "overlays", "chat", "chat.html"), "Chat Overlay HTML not found")
        )
        self.register_route(
            "/music",
            lambda h, p: serve_html_file(h, os.path.join("assets", "overlays", "music", "music.html"), "Music Overlay HTML not found")
        )
        self.register_routes(
            ["/widgets/shoutout", "/widgets/shoutouts", "/shoutout"],
            lambda h, p: serve_html_file(h, os.path.join("assets", "overlays", "widgets", "shoutout.html"), "Shoutout Overlay HTML not found")
        )
        self.register_routes(
            ["/widgets/deaths", "/widgets/death", "/deaths"],
            lambda h, p: serve_html_file(h, os.path.join("assets", "overlays", "widgets", "deaths.html"), "Death Counter Overlay HTML not found")
        )
        self.register_routes(
            ["/widgets/score", "/widgets/scores", "/score"],
            lambda h, p: serve_html_file(h, os.path.join("assets", "overlays", "widgets", "score.html"), "Score Overlay HTML not found")
        )
        self.register_route("/media", lambda h, p: serve_media_file(h, p))

    def dispatch(self, handler, parsed_url) -> bool:
        path = parsed_url.path
        
        route_func = self._exact_routes.get(path)
        if route_func:
            route_func(handler, parsed_url)
            return True

        if path.startswith("/css/"):
            css_filename = os.path.basename(path)
            css_path = get_resource_path(os.path.join("assets", "overlays", "chat", "css", css_filename))
            try:
                with open(css_path, "rb") as f:
                    handler.send_response(200)
                    handler.send_header("Content-Type", "text/css; charset=utf-8")
                    handler.end_headers()
                    handler.wfile.write(f.read())
            except FileNotFoundError:
                handler.send_error(404, f"CSS file not found at: {css_path}")
            return True

        relative_path = path.lstrip("/")
        file_path = get_resource_path(os.path.join("assets", "overlays", relative_path))
        
        if os.path.isfile(file_path):
            abs_base = os.path.abspath(get_resource_path(os.path.join("assets", "overlays")))
            abs_target = os.path.abspath(file_path)
            if abs_target.startswith(abs_base):
                mime_type, _ = mimetypes.guess_type(file_path)
                try:
                    handler.send_response(200)
                    handler.send_header("Content-Type", mime_type or "application/octet-stream")
                    handler.end_headers()
                    with open(file_path, "rb") as f:
                        handler.wfile.write(f.read())
                    return True
                except Exception as e:
                    handler.send_error(500, f"Error reading file: {e}")
                    return True

        return False

class OverlayRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        token = query.get("token", [None])[0]
        
        manager = self.server.manager
        expected_token = getattr(manager, "session_token", None)
        is_css_request = path.endswith(".css") or "/css/" in path

        if expected_token and not is_css_request and token != expected_token:
            self.send_error(403, "Forbidden: Invalid session token")
            return

        if path == "/events":
            manager.sse_manager.serve_stream(self, "rewards")
            return
        elif path == "/chat_events":
            manager.sse_manager.serve_stream(self, "chat")
            return
        elif path == "/music_events":
            last_song = manager.sse_manager.get_last_state("music")
            initial = [last_song] if last_song is not None else None
            manager.sse_manager.serve_stream(self, "music", initial_payloads=initial)
            return
        elif path == "/widget_events":
            last_death = getattr(manager, "_last_death_count", 0)
            last_score = getattr(manager, "_last_score", {"wins": 0, "losses": 0})
            initial = [
                {"event": "death_update", "count": last_death},
                {"event": "score", "wins": last_score.get("wins", 0), "losses": last_score.get("losses", 0)}
            ]
            manager.sse_manager.serve_stream(self, "widgets", initial_payloads=initial)
            return

        handled = manager.route_registry.dispatch(self, parsed)
        if not handled:
            self.send_error(404, "Invalid endpoint")

    def log_message(self, format, *args):
        pass

class OverlayServerManager:
    def __init__(self, port: int = 8090, settings_storage=None):
        self.port = port
        self.settings_storage = settings_storage
        self.server = None
        self.thread = None
        self.lock = threading.Lock()

        self.sse_manager = SSEChannelManager(lock=self.lock)
        self.route_registry = OverlayRouteRegistry()

        self._last_death_count: int = 0
        self._last_score: dict = {"wins": 0, "losses": 0}

        self.session_token = ""
        if self.settings_storage:
            self.session_token = self.settings_storage.load_string("overlay_session_token", "")
            
        if not self.session_token:
            self.session_token = secrets.token_hex(16)
            if self.settings_storage:
                self.settings_storage.save_string("overlay_session_token", self.session_token)

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

    def get_widgets_overlay_url(self) -> str:
        return self.get_shoutout_overlay_url()

    def start(self) -> None:
        try:
            self.server = ThreadingHTTPServer(("127.0.0.1", self.port), OverlayRequestHandler)
            self.server.manager = self
            
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logging.info("Overlay server active: %s", self.get_overlay_url())
        except OSError as e:
            logging.error("[OverlayServer] Could not start Overlay server on port %s: %s", self.port, e)

    def trigger_rewards(self, reward_name: str, config: dict) -> None:
        if isinstance(config, str):
            config = {"filepath": config, "volume": 1.0, "scale": 1.0, "pos_x": 0, "pos_y": 0}
            
        safe_path = urllib.parse.quote(config.get("filepath", ""))
        payload = {
            "reward": reward_name,
            "file_url": f"http://localhost:{self.port}/media?path={safe_path}&token={self.session_token}",
            "volume": config.get("volume", 1.0),
            "scale": config.get("scale", 1.0),
            "pos_x": config.get("pos_x", 0),
            "pos_y": config.get("pos_y", 0),
            "is_random_pos": config.get("is_random_pos", False)
        }
        self.sse_manager.broadcast("rewards", payload)

    def trigger_chat_message(self, user: str, message: str, color: str, badges: list = None) -> None:
        payload = {
            "user": user,
            "message": message,
            "color": color,
            "badges": badges or []
        }
        self.sse_manager.broadcast("chat", payload)

    def trigger_music_change(self, song: dict) -> None:
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
                "thumbnail": song.get("thumbnail", "")
            }
        self.sse_manager.set_last_state("music", payload)
        self.sse_manager.broadcast("music", payload)

    def trigger_widget_event(self, event_type: str, data: dict) -> None:
        if event_type == "death_update":
            self._last_death_count = data.get("count", 0)
        elif event_type == "score":
            self._last_score = {"wins": data.get("wins", 0), "losses": data.get("losses", 0)}

        payload = {"event": event_type, **data}
        self.sse_manager.broadcast("widgets", payload)

    def stop(self) -> None:
        if self.server:
            self.sse_manager.shutdown()
            self.server.shutdown()
            self.server.server_close()
