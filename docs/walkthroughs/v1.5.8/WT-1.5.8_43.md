# Walkthrough - Auditoría y Optimización de Latencia del Chat de Kick (v1.5.8_43)

## 1. Diagnóstico de la Auditoría del Chat de Kick

### A. ¿Por qué no aparecían los mensajes en el log de Windows (`minikick.log`)?
- **Causa**: Ni `KickWebSocketManager`, ni `KickChatWorker`, ni `TwitchChatWorker`, ni `ChatController` registraban mensajes de chat entrantes en los logs del sistema.
- **La ilusión con Edge TTS**: En sesiones anteriores con el motor `web` (Edge TTS), los mensajes aparecían en el log únicamente porque `WebTTSProvider` imprimía métricas de benchmark (`[DEBUG] [Web TTS Benchmark] Pre-downloaded audio...`). Al cambiar al motor `piper`, esos mensajes dejaron de imprimirse y el log parecía "mudo".

### B. Prueba en Vivo de Conexión y Latencia
Se ejecutó una prueba de auditoría directa contra el WebSocket de Kick Pusher (`wss://ws-us2.pusher.com`):
```text
[17:27:18.424] WS Connected! Handshake took 472.4ms
[17:27:18.425] Pusher connection established! Socket ID: 1676570.1841432
[17:27:18.425] Subscribing to chatrooms.30913450.v2...
[17:27:18.425] Subscribing to channel_31201771...
[17:27:18.531] Subscription confirmed for: chatrooms.30913450.v2
[17:27:18.531] Subscription confirmed for: channel_31201771
[17:27:27.776] CHAT MSG RECEIVED | User: TheAndro2K | Server Latency: -0.224s | ID: 46f54c71 | Text: 'xd'
```
**Conclusiones de la prueba**:
- La conexión TCP y el handshake con Pusher tardaron **472 ms**.
- La confirmación de canales tardó solo **106 ms**.
- El mensaje enviado por el usuario (`TheAndro2K: 'xd'`) fue entregado por Pusher en **menos de 250 ms**.

---

## 2. Optimizaciones y Mejoras Aplicadas

1. **Desactivación del Algoritmo de Nagle (`TCP_NODELAY`)**:
   - En [kick_websocket.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_websocket.py), se añadió `sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),)` a `run_forever()`.
   - Evita que el sistema operativo agrupe o demore paquetes TCP de 40ms a 200ms.

2. **Limpieza de Suscripciones Redundantes**:
   - Se eliminaron canales duplicados (`chatroom_{room_id}` y `channel.{channel_id}`).
   - La app se suscribe únicamente a `chatrooms.{room_id}.v2` (canal moderno de chat) y `channel_{channel_id}` (canal de eventos del canal), reduciendo la sobrecarga de frames y confirmaciones.

3. **Trazabilidad Completa de Mensajes en el Log**:
   - Se añadió logging con timestamp exacto tanto en [kick_websocket.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_websocket.py), [kick_chat_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/kick_chat_worker.py) y [twitch_chat_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_chat_worker.py), como en [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py).
   - Registra además la latencia de tránsito del servidor Kick (`created_at`).
   - Todos los mensajes entrantes (de Kick y Twitch) ahora son plenamente visibles en el visor de logs y en `minikick.log` sin depender del motor TTS.

---

## 3. Verificación Automatizada

```powershell
uv run pytest resources/tests/unit/providers/test_kick_websocket.py resources/tests/unit/ui/test_chat_controller.py resources/tests/unit/ui/test_dialogs.py
```
Resultado: **28 passed in 0.40s**.
