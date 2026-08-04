# backend\services\rewards\overlay_server.py

import logging
import os
import json
import queue
import sys
import threading
import mimetypes
import urllib.parse
import secrets
import hashlib
import base64
import struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

def get_resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


class WebSocketClient:
    """Manejador de cliente WebSocket optimizado (RFC 6455) para evitar el límite de sockets HTTP/1.1 de Chromium."""
    def __init__(self, handler, topic: str, token: str):
        self.handler = handler
        self.wfile = handler.wfile
        self.rfile = handler.rfile
        self.topic = topic
        self.token = token
        self.closed = False
        self.lock = threading.Lock()

    def send_json(self, data: dict):
        if self.closed:
            return
        try:
            msg = json.dumps(data)
            self.send_text(msg)
        except Exception as e:
            logging.debug("[WebSocketClient] Error al serializar JSON: %s", e)

    def send_text(self, text: str):
        if self.closed:
            return
        payload = text.encode('utf-8')
        payload_len = len(payload)
        
        header = bytearray([0x81])
        if payload_len < 126:
            header.append(payload_len)
        elif payload_len <= 65535:
            header.append(126)
            header.extend(struct.pack(">H", payload_len))
        else:
            header.append(127)
            header.extend(struct.pack(">Q", payload_len))

        with self.lock:
            try:
                self.wfile.write(header + payload)
                self.wfile.flush()
            except Exception:
                self.closed = True

    def send_pong(self, body=b""):
        if self.closed:
            return
        header = bytearray([0x8A, len(body)])
        with self.lock:
            try:
                self.wfile.write(header + body)
                self.wfile.flush()
            except Exception:
                self.closed = True

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            with self.lock:
                self.wfile.write(bytearray([0x88, 0x00]))
                self.wfile.flush()
        except Exception:
            pass

    def read_frame(self):
        try:
            b1 = self.rfile.read(1)
            if not b1:
                self.closed = True
                return None
            byte1 = b1[0]
            opcode = byte1 & 0x0F

            b2 = self.rfile.read(1)
            if not b2:
                self.closed = True
                return None
            byte2 = b2[0]
            masked = (byte2 & 0x80) != 0
            payload_len = byte2 & 0x7F

            if payload_len == 126:
                len_bytes = self.rfile.read(2)
                if len(len_bytes) < 2:
                    self.closed = True
                    return None
                payload_len = struct.unpack(">H", len_bytes)[0]
            elif payload_len == 127:
                len_bytes = self.rfile.read(8)
                if len(len_bytes) < 8:
                    self.closed = True
                    return None
                payload_len = struct.unpack(">Q", len_bytes)[0]

            mask_key = b""
            if masked:
                mask_key = self.rfile.read(4)
                if len(mask_key) < 4:
                    self.closed = True
                    return None

            payload = b""
            if payload_len > 0:
                remaining = payload_len
                chunks = []
                while remaining > 0:
                    chunk = self.rfile.read(min(remaining, 65536))
                    if not chunk:
                        self.closed = True
                        return None
                    chunks.append(chunk)
                    remaining -= len(chunk)
                payload = b"".join(chunks)

            if masked:
                unmasked = bytearray(payload)
                for i in range(len(unmasked)):
                    unmasked[i] ^= mask_key[i % 4]
                payload = bytes(unmasked)

            if opcode == 0x8:
                self.close()
                return None
            elif opcode == 0x9:
                self.send_pong(payload)
                return None
            elif opcode == 0x1:
                return payload.decode('utf-8', errors='ignore')
            elif opcode == 0x2:
                return payload
            else:
                return None

        except Exception:
            self.closed = True
            return None


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
                    import time
                    song_data = dict(self.server.manager._last_song)
                    if song_data.get("type") == "playing" and song_data.get("is_playing"):
                        ts = song_data.get("timestamp")
                        if ts:
                            elapsed = (time.time() * 1000) - ts
                            dur = song_data.get("duration", 0)
                            calc_prog = song_data.get("progress", 0) + elapsed
                            if dur > 0:
                                song_data["progress"] = min(dur, calc_prog)
                            else:
                                song_data["progress"] = calc_prog
                    ws_client.send_json(song_data)
                elif topic == "widgets":
                    ws_client.send_json({"event": "death_update", **getattr(self.server.manager, "_last_death_data", {"count": 0, "is_active": True})})
                    ws_client.send_json({"event": "score", **getattr(self.server.manager, "_last_score_data", {"wins": 0, "losses": 0, "is_active": True})})

                while not ws_client.closed:
                    msg = ws_client.read_frame()
                    if msg is None and ws_client.closed:
                        break
            finally:
                self.server.manager.unregister_ws_client(ws_client)
            return

        if path == "/overlay":
            html_path = get_resource_path(os.path.join("assets", "overlays", "rewards", "rewards.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Overlay HTML not found at: {html_path}")

        elif path == "/chat":
            html_path = get_resource_path(os.path.join("assets", "overlays", "chat", "chat.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Chat Overlay HTML not found at: {html_path}")

        elif path == "/music":
            html_path = get_resource_path(os.path.join("assets", "overlays", "music", "music.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Music Overlay HTML not found at: {html_path}")

        elif path in ("/widgets/shoutout", "/widgets/shoutouts", "/shoutout"):
            html_path = get_resource_path(os.path.join("assets", "overlays", "widgets", "shoutout.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Shoutout Overlay HTML not found at: {html_path}")

        elif path in ("/widgets/deaths", "/widgets/death", "/deaths"):
            html_path = get_resource_path(os.path.join("assets", "overlays", "widgets", "deaths.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Death Counter Overlay HTML not found at: {html_path}")

        elif path in ("/widgets/score", "/widgets/scores", "/score"):
            html_path = get_resource_path(os.path.join("assets", "overlays", "widgets", "score.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Score Overlay HTML not found at: {html_path}")

        elif path in ("/widgets/emote_explosion", "/widgets/explosion", "/widgets/emotes", "/explosion"):
            html_path = get_resource_path(os.path.join("assets", "overlays", "widgets", "emote_explosion.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Emote Explosion Overlay HTML not found at: {html_path}")

        elif path in ("/widgets/emote_combo", "/widgets/combo", "/combo"):
            html_path = get_resource_path(os.path.join("assets", "overlays", "widgets", "emote_combo.html"))
            try:
                with open(html_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"Emote Combo Overlay HTML not found at: {html_path}")

        elif path.startswith("/css/"):
            css_filename = os.path.basename(path)
            css_path = get_resource_path(os.path.join("assets", "overlays", "chat", "css", css_filename))
            try:
                with open(css_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/css; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, f"CSS file not found at: {css_path}")

        elif path == "/media":
            query = parse_qs(parsed.query)
            if "path" not in query:
                self.send_error(400, "Path not specified")
                return
                
            filepath = query["path"][0]
            if not os.path.exists(filepath):
                self.send_error(404, "Media file not found")
                return
                
            mime_type, _ = mimetypes.guess_type(filepath)
            
            try:
                self.send_response(200)
                self.send_header("Content-Type", mime_type or "application/octet-stream")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                with open(filepath, "rb") as f:
                    chunk_size = 1024 * 64 
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
            except Exception as e:
                try:
                    self.send_error(500, f"Internal error: {e}")
                except:
                    pass

        elif path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            client_queue = queue.Queue()
            with self.server.manager.lock:
                self.server.manager.clients.append(client_queue)
            
            try:
                while True:
                    try:
                        rewards = client_queue.get(timeout=2.0)
                        if rewards is None:
                            break
                        self.wfile.write(f"data: {json.dumps(rewards)}\n\n".encode("utf-8"))
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
                    if client_queue in self.server.manager.clients:
                        self.server.manager.clients.remove(client_queue)

        elif path == "/chat_events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            client_queue = queue.Queue()
            with self.server.manager.lock:
                self.server.manager.chat_clients.append(client_queue)
            
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
                    if client_queue in self.server.manager.chat_clients:
                        self.server.manager.chat_clients.remove(client_queue)

        elif path == "/music_events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            client_queue = queue.Queue()
            with self.server.manager.lock:
                self.server.manager.music_clients.append(client_queue)

            last = self.server.manager._last_song
            if last is not None:
                client_queue.put(last)

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
                    if client_queue in self.server.manager.music_clients:
                        self.server.manager.music_clients.remove(client_queue)

        elif path == "/widget_events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            client_queue = queue.Queue()
            with self.server.manager.lock:
                self.server.manager.widget_clients.append(client_queue)

            last_death = getattr(self.server.manager, "_last_death_count", 0)
            client_queue.put({"event": "death_update", "count": last_death})

            last_score = getattr(self.server.manager, "_last_score", {"wins": 0, "losses": 0})
            client_queue.put({"event": "score", "wins": last_score.get("wins", 0), "losses": last_score.get("losses", 0)})

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
                    if client_queue in self.server.manager.widget_clients:
                        self.server.manager.widget_clients.remove(client_queue)

        else:
            relative_path = path.lstrip("/")
            file_path = get_resource_path(os.path.join("assets", "overlays", relative_path))
            
            if os.path.isfile(file_path):
                abs_base = os.path.abspath(get_resource_path(os.path.join("assets", "overlays")))
                abs_target = os.path.abspath(file_path)
                if abs_target.startswith(abs_base):
                    mime_type, _ = mimetypes.guess_type(file_path)
                    try:
                        self.send_response(200)
                        self.send_header("Content-Type", mime_type or "application/octet-stream")
                        self.end_headers()
                        with open(file_path, "rb") as f:
                            self.wfile.write(f.read())
                        return
                    except Exception as e:
                        self.send_error(500, f"Error reading file: {e}")
                        return
            
            self.send_error(404, "Invalid endpoint")

    def log_message(self, format, *args):
        pass


class OverlayServerManager:
    def __init__(self, port=8090, settings_storage=None):
        self.port = port
        self.server = None
        self.thread = None
        
        self.clients = []
        self.chat_clients = []
        self.music_clients = []
        self.widget_clients = []

        self.ws_clients = {
            "rewards": set(),
            "chat": set(),
            "music": set(),
            "widgets": set()
        }
        self.ws_lock = threading.Lock()

        self._last_song: dict | None = None
        self._last_death_count: int = 0
        self._last_score: dict = {"wins": 0, "losses": 0}
        self._last_death_data: dict = {"count": 0, "is_active": True}
        self._last_score_data: dict = {"wins": 0, "losses": 0, "is_active": True}
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

    def get_widgets_overlay_url(self) -> str:
        return self.get_shoutout_overlay_url()

    def start(self):
        try:
            self.server = ThreadingHTTPServer(("127.0.0.1", self.port), OverlayRequestHandler)
            self.server.manager = self 
            
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logging.info("Overlay server active: %s", self.get_overlay_url())
        except OSError as e:
            logging.error("[OverlayServer] Could not start Overlay server on port %s: %s", self.port, e)

    def trigger_rewards(self, reward_name: str, config: dict):
        if isinstance(config, str):
            config = {"filepath": config, "volume": 1.0, "scale": 1.0, "pos_x": 0, "pos_y": 0}
            
        safe_path = urllib.parse.quote(config['filepath'])
        
        payload = {
            "reward": reward_name,
            "file_url": f"http://localhost:{self.port}/media?path={safe_path}&token={self.session_token}",
            "volume": config.get("volume", 1.0),
            "scale": config.get("scale", 1.0),
            "pos_x": config.get("pos_x", 0),
            "pos_y": config.get("pos_y", 0),
            "is_random_pos": config.get("is_random_pos", False)
        }
        
        with self.lock:
            clients_copy = list(self.clients)
        for client_queue in clients_copy:
            client_queue.put(payload)
        with self.ws_lock:
            ws_copy = list(self.ws_clients["rewards"])
        for ws_client in ws_copy:
            ws_client.send_json(payload)

    def trigger_chat_message(self, user: str, message: str, color: str, badges: list = None):
        payload = {
            "user": user,
            "message": message,
            "color": color,
            "badges": badges or []
        }
        
        with self.lock:
            clients_copy = list(self.chat_clients)
        for client_queue in clients_copy:
            client_queue.put(payload)
        with self.ws_lock:
            ws_copy = list(self.ws_clients["chat"])
        for ws_client in ws_copy:
            ws_client.send_json(payload)

    def trigger_music_change(self, song: dict):
        import time
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
        
        with self.lock:
            clients_copy = list(self.music_clients)
        for client_queue in clients_copy:
            client_queue.put(payload)
        with self.ws_lock:
            ws_copy = list(self.ws_clients["music"])
        for ws_client in ws_copy:
            ws_client.send_json(payload)

    def trigger_widget_event(self, event_type: str, data: dict):
        if event_type == "death_update":
            self._last_death_count = data.get("count", 0)
            self._last_death_data.update(data)
        elif event_type == "score":
            self._last_score = {"wins": data.get("wins", 0), "losses": data.get("losses", 0)}
            self._last_score_data.update(data)
        elif event_type == "widget_toggle":
            w_id = data.get("widget_id")
            if w_id == "death":
                self._last_death_data["is_active"] = data.get("is_active", True)
            elif w_id == "score":
                self._last_score_data["is_active"] = data.get("is_active", True)

        payload = {"event": event_type, **data}
        
        with self.lock:
            clients_copy = list(self.widget_clients)
        for client_queue in clients_copy:
            client_queue.put(payload)
        with self.ws_lock:
            ws_copy = list(self.ws_clients["widgets"])
        for ws_client in ws_copy:
            ws_client.send_json(payload)

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
            for client_queue in clients_copy:
                client_queue.put(None)
            for client_queue in chat_copy:
                client_queue.put(None)
            for client_queue in music_copy:
                client_queue.put(None)
            for client_queue in widget_copy:
                client_queue.put(None)
            self.server.shutdown()
            self.server.server_close()
