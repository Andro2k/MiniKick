# backend/kick_websocket.py

import json
import re
import time
from typing import Callable
import websocket

class ChatFormatter:
    """Clase utilitaria pura (Alta Cohesión)."""
    @staticmethod
    def clean(text: str) -> str:
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        text = re.sub(r"\[emote:[^\]]*\]", "", text)
        return text.strip()

class ChatSocketManager:
    """Responsable exclusivamente de mantener vivo el flujo de eventos del Chat."""
    
    def __init__(self, cluster: str, key: str) -> None:
        self.cluster = cluster
        self.key = key
        self._running = False
        self.ws = None # 1. NUEVO: Guardamos la referencia del socket activo

    def start_socket(self, room_id: int, on_message: Callable[[str, str], None]) -> None:
        url = (
            f"wss://ws-{self.cluster}.pusher.com/app/{self.key}"
            f"?protocol=7&client=js&version=7.6.0"
        )
        self._running = True

        def _on_message(ws: websocket.WebSocketApp, raw: str) -> None:
            data = json.loads(raw)
            event = data.get("event")

            if event == "pusher:connection_established":
                ws.send(json.dumps({
                    "event": "pusher:subscribe",
                    "data": {"channel": f"chatrooms.{room_id}.v2"},
                }))

            elif event == "App\\Events\\ChatMessageEvent":
                payload = json.loads(data.get("data", "{}"))
                user = payload.get("sender", {}).get("username", "")
                
                msg = ChatFormatter.clean(payload.get("content", ""))
                
                if user and msg:
                    on_message(user, msg)

            elif event == "pusher:ping":
                ws.send(json.dumps({"event": "pusher:pong"}))

        # Bucle de resiliencia
        while self._running:
            try:
                # 2. MODIFICADO: Asignamos a self.ws en lugar de una variable local 'ws'
                self.ws = websocket.WebSocketApp(url, on_message=_on_message)
                self.ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as e:
                print(f"[Chat] Socket interrumpido: {e}")

            if self._running:
                print("[Chat] Reconectando en 5 segundos...")
                time.sleep(5) 

    def stop_socket(self) -> None:
        """Detiene el bucle y fuerza el cierre de la conexión de red bloqueante."""
        self._running = False
        # 3. NUEVO: Si existe un socket activo, lo cerramos a la fuerza
        if self.ws:
            self.ws.close()