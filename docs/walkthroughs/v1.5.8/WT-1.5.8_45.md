# Walkthrough - Implementación de Telemetría Diagnóstica, Códigos RFC 6455 y Trazabilidad Avanzada (v1.5.8_45)

## 1. Resumen y Objetivos

Para facilitar el diagnóstico inmediato de fallos en producción (caídas de WebSockets, congelamientos de hilos en apagado, mensajes que no suenan en TTS, o excepciones internas no tipadas), se instrumentó la arquitectura de MiniKick con observabilidad de alta fidelidad sin penalización de rendimiento ($\mathcal{O}(1)$ overhead).

---

## 2. Componentes Instrumentados

### A. Diagnóstico de Ciclo de Vida y Tiempos de Parada de Workers
- **Archivo**: [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)
- **Mejoras**:
  - `_safe_stop_worker`: Mide con `time.perf_counter()` la duración exacta del proceso de apagado.
  - Registra a nivel `DEBUG` cuando el worker se detiene limpiamente (`[Worker] Worker '...' stopped cleanly in X.X ms`).
  - Registra a nivel `WARNING` cuando se excede el timeout de parada (`[Worker] Worker '...' still active after X.X ms (timeout: Y ms). Retaining in retirement registry.`).
  - `_stop_workers_parallel`: Instrumentado con cronometraje individual de cada hilo activo durante el cierre de la aplicación.

### B. Decodificación de Códigos de Cierre RFC 6455 en WebSockets
- **Archivos**:
  - [kick_websocket.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_websocket.py)
  - [twitch_websocket.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_websocket.py)
- **Mejoras**:
  - Se incorporó la tabla `RFC_6455_CLOSE_CODES` para mapear de inmediato códigos de cierre estándar (1000: *Normal Closure*, 1001: *Going Away*, 1006: *Abnormal Closure*, etc.).
  - En `_on_close`, se reporta tanto el código como la descripción legible y la razón suministrada por el servidor.
  - En `_on_error`, se captura el nombre de la clase de excepción (`type(err).__name__`) y se preserva el traceback (`exc_info=True`).
  - **Restauración de Tópicos de Puntos de Canal Kick (`chatroom_{room_id}`)**: Se restauró la suscripción activa a `chatroom_{room_id}` y `channel.{channel_id}`. En la infraestructura de Kick Pusher, `chatrooms.{room_id}.v2` entrega los mensajes de chat mientras que los canjes de recompensas de canal (`RewardRedeemedEvent`) se transmiten por `chatroom_{room_id}`. Se robusteció además `_handle_reward_redeemed` con extracción alternativa defensiva (`reward.title` y `user.username`).

### C. Tipado de Excepciones y Tracebacks en Workers de Chat
- **Archivos**:
  - [kick_chat_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/kick_chat_worker.py)
  - [twitch_chat_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_chat_worker.py)
  - [youtube_chat_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/youtube_chat_worker.py)
  - [youtube_chat_provider.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/youtube_chat_provider.py)
  - [tiktok_chat_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/tiktok_chat_worker.py)
  - [tiktok_chat_provider.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/tiktok_chat_provider.py)
- **Mejoras**:
  - Sustitución de logs genéricos `e` por formato estructurado `type(e).__name__` y `exc_info=True`.
  - Permite identificar de inmediato en `minikick.log` el tipo de error (HTTP timeout, SSL handshake error, socket hangup, etc.) y la línea de código exacta de origen.

### D. Trazabilidad de Decisiones TTS y Diagnóstico de Audio
- **Archivos**:
  - [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py)
  - [tts_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/tts_service.py)
  - [tts_piper.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_piper.py)
  - [tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py)
- **Mejoras**:
  - `_step_tts`: Registra a nivel `DEBUG` la razón precisa por la cual un mensaje no se sintetizó (rol de usuario desactivado en configuración, modo comando `use_command` activo esperando el trigger, usuario marcado como bot/ignorado, palabra prohibida detectada, o mensaje compuesto solo por emoticonos/URLs).
  - `TTSManager`: Registra a nivel `DEBUG` cada encolamiento de texto con su longitud y tamaño de cola; en `stop()`, reporta la cantidad de elementos descartados en texto y reproducción.
  - Proveedores de voz (`Piper` y `Web/Edge`): Reportan el enrutamiento exitoso hacia el dispositivo de audio configurado (`QMediaDevices`) o la traza de excepción si el dispositivo falla.

---

## 3. Pruebas y Verificación

### Pruebas Automatizadas
Se creó una suite de pruebas dedicada en [test_diagnostic_telemetry.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/core/test_diagnostic_telemetry.py) cubriendo:
1. Paridad de códigos RFC 6455 en Kick y Twitch.
2. Formato de cierre y errores con excepción tipada en WebSockets.
3. Telemetría de cola y comando stop en `TTSManager`.
4. Registro de razones de omisión en `ChatController._step_tts`.

```powershell
.\.venv\Scripts\python.exe -m pytest resources/tests/unit/core/test_diagnostic_telemetry.py -v
```
**Resultado**:
```text
collected 5 items
resources/tests/unit/core/test_diagnostic_telemetry.py::test_rfc_6455_codes_parity PASSED
resources/tests/unit/core/test_diagnostic_telemetry.py::test_kick_websocket_close_and_error_diagnostics PASSED
resources/tests/unit/core/test_diagnostic_telemetry.py::test_twitch_websocket_close_and_error_diagnostics PASSED
resources/tests/unit/core/test_diagnostic_telemetry.py::test_tts_manager_queue_and_stop_telemetry PASSED
resources/tests/unit/core/test_diagnostic_telemetry.py::test_chat_controller_step_tts_skip_reasons PASSED

============================== 5 passed in 0.08s ==============================
```
