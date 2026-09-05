# backend\services\overlay\overlay_routes.py

import base64
import hashlib
import json
import logging
import mimetypes
import os
import queue
import sys
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from .websocket_client import WebSocketClient

logger = logging.getLogger("minikick.services.overlay.routes")

def get_resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

STATIC_ENDPOINTS_MAP: dict[str, tuple[str, str]] = {
    "/overlay": (os.path.join("assets", "overlays", "rewards", "rewards.html"), "Overlay HTML"),
    "/chat": (os.path.join("assets", "overlays", "chat", "chat.html"), "Chat Overlay HTML"),
    "/music": (os.path.join("assets", "overlays", "music", "music.html"), "Music Overlay HTML"),
    "/widgets/shoutout": (os.path.join("assets", "overlays", "widgets", "shoutout.html"), "Shoutout Overlay HTML"),
    "/widgets/shoutouts": (os.path.join("assets", "overlays", "widgets", "shoutout.html"), "Shoutout Overlay HTML"),
    "/shoutout": (os.path.join("assets", "overlays", "widgets", "shoutout.html"), "Shoutout Overlay HTML"),
    "/widgets/deaths": (os.path.join("assets", "overlays", "widgets", "deaths.html"), "Death Counter Overlay HTML"),
    "/widgets/death": (os.path.join("assets", "overlays", "widgets", "deaths.html"), "Death Counter Overlay HTML"),
    "/deaths": (os.path.join("assets", "overlays", "widgets", "deaths.html"), "Death Counter Overlay HTML"),
    "/widgets/score": (os.path.join("assets", "overlays", "widgets", "score.html"), "Score Overlay HTML"),
    "/widgets/scores": (os.path.join("assets", "overlays", "widgets", "score.html"), "Score Overlay HTML"),
    "/score": (os.path.join("assets", "overlays", "widgets", "score.html"), "Score Overlay HTML"),
    "/widgets/emote_explosion": (os.path.join("assets", "overlays", "widgets", "emote_explosion.html"), "Emote Explosion Overlay HTML"),
    "/widgets/explosion": (os.path.join("assets", "overlays", "widgets", "emote_explosion.html"), "Emote Explosion Overlay HTML"),
    "/widgets/emotes": (os.path.join("assets", "overlays", "widgets", "emote_explosion.html"), "Emote Explosion Overlay HTML"),
    "/explosion": (os.path.join("assets", "overlays", "widgets", "emote_explosion.html"), "Emote Explosion Overlay HTML"),
    "/widgets/emote_combo": (os.path.join("assets", "overlays", "widgets", "emote_combo.html"), "Emote Combo Overlay HTML"),
    "/widgets/combo": (os.path.join("assets", "overlays", "widgets", "emote_combo.html"), "Emote Combo Overlay HTML"),
    "/combo": (os.path.join("assets", "overlays", "widgets", "emote_combo.html"), "Emote Combo Overlay HTML"),
    "/widgets/poll": (os.path.join("assets", "overlays", "widgets", "poll.html"), "Poll Overlay HTML"),
    "/widgets/polls": (os.path.join("assets", "overlays", "widgets", "poll.html"), "Poll Overlay HTML"),
    "/poll": (os.path.join("assets", "overlays", "widgets", "poll.html"), "Poll Overlay HTML"),
    "/widgets/pinned": (os.path.join("assets", "overlays", "widgets", "pinned.html"), "Pinned Message Overlay HTML"),
    "/widgets/pinned_message": (os.path.join("assets", "overlays", "widgets", "pinned.html"), "Pinned Message Overlay HTML"),
    "/pinned": (os.path.join("assets", "overlays", "widgets", "pinned.html"), "Pinned Message Overlay HTML"),
    "/alerts": (os.path.join("assets", "overlays", "alerts", "alerts.html"), "Alerts Overlay HTML"),
    "/alerts/": (os.path.join("assets", "overlays", "alerts", "alerts.html"), "Alerts Overlay HTML"),
    "/alert": (os.path.join("assets", "overlays", "alerts", "alerts.html"), "Alerts Overlay HTML"),
}

_ASSET_CACHE: dict[str, bytes] = {}

def get_cached_asset(filepath: str) -> bytes | None:
    if filepath not in _ASSET_CACHE:
        try:
            with open(filepath, "rb") as f:
                _ASSET_CACHE[filepath] = f.read()
        except FileNotFoundError:
            return None
    return _ASSET_CACHE[filepath]


class OverlayRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        token = query.get("token", [None])[0]

        expected_token = getattr(self.server.manager, "session_token", None)
        is_css_request = path.endswith(".css") or "/css/" in path
        if expected_token and not is_css_request and token != expected_token:
            self.send_error(403, "Forbidden: Invalid session token")
            return

        if path == "/ws":
            self._handle_websocket_upgrade(query, token)
            return
        if path in STATIC_ENDPOINTS_MAP:
            rel_asset_path, error_label = STATIC_ENDPOINTS_MAP[path]
            html_path = get_resource_path(rel_asset_path)
            content = get_cached_asset(html_path)
            if content is not None:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, f"{error_label} not found at: {html_path}")
            return

        if path.startswith("/css/"):
            css_filename = os.path.basename(path)
            css_path = get_resource_path(os.path.join("assets", "overlays", "chat", "css", css_filename))
            content = get_cached_asset(css_path)
            if content is not None:
                self.send_response(200)
                self.send_header("Content-Type", "text/css; charset=utf-8")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, f"CSS file not found at: {css_path}")
            return

        if path == "/media":
            self._handle_media_request(query)
            return
        if path == "/events":
            self._handle_sse_stream("clients")
            return
        elif path == "/chat_events":
            self._handle_sse_stream("chat_clients")
            return
        elif path == "/music_events":
            initial_data = [self.server.manager._last_song] if self.server.manager._last_song is not None else None
            self._handle_sse_stream("music_clients", initial_payloads=initial_data)
            return
        elif path == "/widget_events":
            last_death = getattr(self.server.manager, "_last_death_count", 0)
            last_score = getattr(self.server.manager, "_last_score", {"wins": 0, "losses": 0})
            initial_data = [
                {"event": "death_update", "count": last_death},
                {"event": "score", "wins": last_score.get("wins", 0), "losses": last_score.get("losses", 0)}
            ]
            self._handle_sse_stream("widget_clients", initial_payloads=initial_data)
            return

        relative_path = path.lstrip("/")
        file_path = get_resource_path(os.path.join("assets", "overlays", relative_path))
        if os.path.isfile(file_path):
            abs_base = os.path.abspath(get_resource_path(os.path.join("assets", "overlays")))
            abs_target = os.path.abspath(file_path)
            if abs_target.startswith(abs_base):
                mime_type, _ = mimetypes.guess_type(file_path)
                content = get_cached_asset(file_path)
                if content is not None:
                    try:
                        self.send_response(200)
                        self.send_header("Content-Type", mime_type or "application/octet-stream")
                        self.end_headers()
                        self.wfile.write(content)
                        return
                    except Exception as e:
                        self.send_error(500, f"Error reading file: {e}")
                        return

        self.send_error(404, "Invalid endpoint")

    def _handle_websocket_upgrade(self, query: dict, token: str):
        sec_key = self.headers.get("Sec-WebSocket-Key")
        if not sec_key:
            self.send_error(400, "Bad Request: Missing Sec-WebSocket-Key")
            return

        topic = query.get("topic", [query.get("type", ["rewards"])[0]])[0]

        accept_src = (sec_key.strip() + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("utf-8")
        accept_key = base64.b64encode(hashlib.sha1(accept_src).digest()).decode("utf-8")

        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept_key)
        self.end_headers()

        ws_client = WebSocketClient(self, topic=topic, token=token)
        self.server.manager.register_ws_client(ws_client)

        try:
            if topic == "music" and self.server.manager._last_song is not None:
                song_data = dict(self.server.manager._last_song)
                if song_data.get("type") == "playing" and song_data.get("is_playing"):
                    ts = song_data.get("timestamp")
                    if ts:
                        elapsed = (time.time() * 1000) - ts
                        dur = song_data.get("duration", 0)
                        calc_prog = song_data.get("progress", 0) + elapsed
                        song_data["progress"] = min(dur, calc_prog) if dur > 0 else calc_prog
                ws_client.send_json(song_data)
            elif topic == "widgets":
                ws_client.send_json({"event": "death_update", **getattr(self.server.manager, "_last_death_data", {"count": 0, "is_active": True})})
                ws_client.send_json({"event": "score", **getattr(self.server.manager, "_last_score_data", {"wins": 0, "losses": 0, "is_active": True})})
                if getattr(self.server.manager, "_last_poll_data", None):
                    poll_copy = dict(self.server.manager._last_poll_data)
                    elapsed = time.time() - getattr(self.server.manager, "_last_poll_timestamp", time.time())
                    orig_rem = poll_copy.get("remaining", 0)
                    poll_copy["remaining"] = max(0, int(orig_rem - elapsed))
                    ws_client.send_json({"event": "poll_update", "poll": poll_copy})
                if getattr(self.server.manager, "_last_pinned_data", None):
                    ws_client.send_json({"event": "pinned_created", "pinned": self.server.manager._last_pinned_data})

            while not ws_client.closed:
                msg = ws_client.read_frame()
                if msg is None and ws_client.closed:
                    break
                if msg and isinstance(msg, str):
                    try:
                        data = json.loads(msg)
                        if data.get("type") == "alert_finished":
                            cb = getattr(self.server.manager, "on_alert_finished", None)
                            if cb:
                                cb(data.get("id"))
                    except Exception:
                        pass
        finally:
            self.server.manager.unregister_ws_client(ws_client)

    def _handle_media_request(self, query: dict):
        if "path" not in query:
            self.send_error(400, "Path not specified")
            return

        filepath = os.path.normpath(query["path"][0])
        if not os.path.isfile(filepath):
            self.send_error(404, "Media file not found")
            return

        file_size = os.path.getsize(filepath)
        mime_type, _ = mimetypes.guess_type(filepath)
        content_type = mime_type or "application/octet-stream"

        range_header = self.headers.get("Range")
        start = 0
        end = file_size - 1 if file_size > 0 else 0

        if range_header and range_header.startswith("bytes="):
            range_val = range_header.replace("bytes=", "").strip()
            parts = range_val.split("-")
            try:
                if parts[0]:
                    start = int(parts[0])
                if len(parts) > 1 and parts[1]:
                    end = int(parts[1])
            except ValueError:
                pass
            start = max(0, min(start, file_size - 1)) if file_size > 0 else 0
            end = max(start, min(end, file_size - 1)) if file_size > 0 else 0
            status_code = 206
        else:
            status_code = 200

        content_length = (end - start + 1) if file_size > 0 else 0

        try:
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(content_length))
            self.send_header("Access-Control-Allow-Origin", "*")
            if status_code == 206 and file_size > 0:
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.end_headers()

            if file_size > 0 and content_length > 0:
                with open(filepath, "rb") as f:
                    f.seek(start)
                    remaining = content_length
                    chunk_size = 1024 * 64
                    while remaining > 0:
                        read_len = min(chunk_size, remaining)
                        chunk = f.read(read_len)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)

        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            try:
                self.send_error(500, f"Internal error: {e}")
            except Exception:
                pass

    def _handle_sse_stream(self, client_attr: str, initial_payloads: list = None):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        client_queue = queue.Queue()
        client_list = getattr(self.server.manager, client_attr)
        with self.server.manager.lock:
            client_list.append(client_queue)

        if initial_payloads:
            for item in initial_payloads:
                if item is not None:
                    client_queue.put(item)

        try:
            while True:
                try:
                    msg = client_queue.get(timeout=2.0)
                    if msg is None:
                        break
                    self.wfile.write(f"data: {json.dumps(msg)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception:
            pass
        finally:
            with self.server.manager.lock:
                if client_queue in client_list:
                    client_list.remove(client_queue)

    def log_message(self, format, *args):
        pass
