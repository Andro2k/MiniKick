# backend/services/rewards/overlay/websocket_client.py

import json
import logging
import struct
import threading

logger = logging.getLogger("minikick.services.overlay.websocket")

class WebSocketClient:
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
            logger.debug("[WebSocketClient] Error serializing JSON: %s", e)

    def send_text(self, text: str):
        if self.closed:
            return
        payload = text.encode("utf-8")
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

    def send_pong(self, body: bytes = b""):
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
                mask_repeated = (mask_key * (len(payload) // 4 + 1))[:len(payload)]
                payload = bytes(a ^ b for a, b in zip(payload, mask_repeated))

            if opcode == 0x8:
                self.close()
                return None
            elif opcode == 0x9:
                self.send_pong(payload)
                return None
            elif opcode == 0x1:
                return payload.decode("utf-8", errors="ignore")
            elif opcode == 0x2:
                return payload
            else:
                return None

        except Exception:
            self.closed = True
            return None
