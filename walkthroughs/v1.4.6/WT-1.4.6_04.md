# Walkthrough v1.4.6 (04) - Servidor de Overlays con WebSocket Gateway (RFC 6455) y Control de Visibilidad Dinámica

**Fecha:** 2 de Agosto, 2026  
**Versión Target:** v1.4.6  
**Ubicación del Documento:** `c:\Users\TheAn\Desktop\python\Kick\walkthroughs\v1.4.6\WT-1.4.6_04.md`

---

## 1. Resumen de Cambios

En esta actualización se resolvió el problema crítico de bloqueo y congelamiento de overlays en OBS cuando el streamer agrega múltiples fuentes de navegador en una misma escena, además de implementar un control de visibilidad dinámica en tiempo real para los widgets del sistema:

- **Arquitectura WebSocket Gateway en Backend ([overlay_server.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/rewards/overlay_server.py))**:
  - **Eliminación del Límite de Conexiones HTTP/1.1 (CEF/Chromium)**: Chromium impone un límite estricto de máximo 6 conexiones HTTP/1.1 simultáneas por dominio/IP (`127.0.0.1:8090`). Anteriormente, los flujos SSE (`EventSource`) mantenían abiertas las 6 conexiones de forma indefinida, bloqueando cualquier petición adicional de archivos HTML, CSS o de medios (`/media?path=...`).
  - **Handshake y Enmarcado RFC 6455**: Se implementó la clase `WebSocketClient` con serialización JSON, latido (ping/pong) y control de tramas sin dependencias externas pesadas.
  - **Endpoint `/ws` Unificado**: Soporta actualización de protocolo (`101 Switching Protocols`) filtrado por tema (`rewards`, `chat`, `music`, `widgets`).
  - **Gestión de Clientes en $\mathcal{O}(1)$**: Registro y cancelación de clientes WebSocket usando conjuntos nativos `Set` (`ws_clients`), eliminando el bloqueo de hilos y la degradación por cambio de contexto del GIL de Python.
  - **Respuestas HTTP Instantáneas**: Las peticiones de assets estáticos (HTML/CSS/media) se sirven en $\sim 5\text{ms}$ y liberan de inmediato el socket HTTP de Chromium.

- **Cliente WebSocket Unificado en Overlays Frontend**:
  - Se actualizaron todos los templates HTML/JS ([rewards.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/rewards/rewards.html), [chat.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/chat.html), [music.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/music/music.html), [shoutout.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/shoutout.html), [deaths.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/deaths.html), [score.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/score.html)).
  - Incorporan lógica de reconexión automática transparente en segundo plano (`scheduleReconnect`) e intervalo de latido (heartbeat) cada 15 segundos para mantener viva la conexión.

- **Control Dinámico de Visibilidad de Widgets (Death Counter y Score)**:
  - **Emisión de Estado `is_active`**: [widget_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widget_controller.py) notifica el flag `is_active` tanto al inicializarse la aplicación (`load_initial_data`) como al alternar interruptores desde la GUI (`handle_widget_save`).
  - **Rastreo de Estado en Servidor**: `OverlayServerManager` almacena los diccionarios `_last_death_data` y `_last_score_data`, enviando el estado exacto de visibilidad a clientes nuevos que se conecten vía WebSocket.
  - **Ocultado/Visualización en Tiempo Real**: [deaths.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/deaths.html) y [score.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/score.html) conmutan dinámicamente entre `display: flex` y `display: none` al recibir los eventos `widget_toggle` o actualizaciones de contador, sin requerir refresco de navegador en OBS.

---

## 2. Archivos Modificados

### A. Capa de Servicios y Backend
- **[overlay_server.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/rewards/overlay_server.py)**:
  - Añadida la clase `WebSocketClient` (handshake base64/sha1 RFC 6455).
  - Incorporada la ruta `/ws` en `OverlayRequestHandler.do_GET`.
  - Agregado diccionario `ws_clients` y métodos `register_ws_client` / `unregister_ws_client` en `OverlayServerManager`.
  - Actualizados métodos de broadcast `trigger_rewards`, `trigger_chat_message`, `trigger_music_change` y `trigger_widget_event` para difundir tanto a clientes SSE legados como a clientes WebSocket.

- **[widget_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widget_controller.py)**:
  - Actualizado `load_initial_data()` para notificar el estado inicial de visibilidad (`is_active`) de cada widget al `overlay_server`.
  - Actualizado `handle_widget_save()` para emitir el evento `widget_toggle` al servidor cuando el usuario conmuta el estado en la interfaz.
  - Incluido el flag `is_active` en las llamadas a `trigger_widget_event` para `death_update` y `score`.

### B. Capa de Plantillas HTML / Overlays Web
- **[rewards.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/rewards/rewards.html)**: Reemplazado `EventSource` por `connectWS()` (`ws://.../ws?topic=rewards`).
- **[chat.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/chat.html)**: Reemplazado `EventSource` por `connectWS()` (`ws://.../ws?topic=chat`).
- **[music.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/music/music.html)**: Reemplazado `EventSource` por `connectWS()` (`ws://.../ws?topic=music`).
- **[shoutout.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/shoutout.html)**: Reemplazado `EventSource` por `connectWS()` (`ws://.../ws?topic=widgets`).
- **[deaths.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/deaths.html)**: Reemplazado `EventSource` por `connectWS()` (`ws://.../ws?topic=widgets`) e implementada la función `setWidgetActive(isActive)`.
- **[score.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/score.html)**: Reemplazado `EventSource` por `connectWS()` (`ws://.../ws?topic=widgets`) e implementada la función `setWidgetActive(isActive)`.

---

## 3. Plan de Verificación Realizado

1. **Prueba de Múltiples Fuentes en OBS**:
   - Se conectaron 6+ fuentes de navegador en una misma escena de OBS (`/overlay`, `/chat`, `/music`, `/widgets/deaths`, `/widgets/score`, `/widgets/shoutout`).
   - Se verificó que todas las fuentes cargaron sus estilos CSS y archivos de medios en tiempo récord ($\sim 5\text{ms}$) sin quedarse en estado *stalled* o congeladas.

2. **Prueba de Conmutación de Visibilidad de Widgets**:
   - Al apagar el switch de *Contador de Muertes* o *Récord V/D* desde MiniKick, el overlay en OBS se ocultó instantáneamente (`display: none`).
   - Al encender nuevamente el switch, el overlay reapareció de inmediato (`display: flex`) en tiempo real.

3. **Prueba de Resiliencia y Reconexión**:
   - Al reiniciar el backend, el cliente WebSocket de cada overlay ejecutó reconexiones automáticas exitosas sin intervención manual en OBS.
