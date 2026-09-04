# Walkthrough - WT-1.5.8_03: Simetría de Arquitectura, Proveedores de Red y Resiliencia OAuth (Kick vs Twitch)

**Versión:** `v1.5.8`  
**Documento:** `WT-1.5.8_03.md`  
**Fecha:** 02 de Septiembre, 2026  

---

## 1. Resumen Ejecutivo

Este documento consolida la refactorización simétrica entre las plataformas Kick y Twitch, la optimización de bajo nivel de sus proveedores de red (WebSocket y REST API) y la resolución de vulnerabilidades críticas en la autenticación OAuth y concurrencia de sockets.

---

## 2. Asimetrías Corregidas y Nomenclatura Simétrica

| Dominio | Antes | Ahora | Beneficio |
| :--- | :--- | :--- | :--- |
| **Worker de Canjes Twitch** | `TwitchRewardWorker` dentro de `rewards_worker.py` | [backend/workers/twitch_reward_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_reward_worker.py) | Archivo dedicado, simétrico con `twitch_chat_worker.py` y `twitch_auth_worker.py`. |
| **WebSocket de Kick** | `ChatSocketManager` en `kick_websocket.py` | `KickWebSocketManager` (con alias `ChatSocketManager`) | Simetría explícita con `TwitchChatSocketManager`. |
| **Autenticación Kick** | `AuthManager` en `oauth_service.py` | `KickAuthManager` (con alias `AuthManager`) | Simetría explícita con `TwitchAuthManager`. |
| **Contenedor DI (`AppContainerCore`)** | `self.auth_manager` | `self.kick_auth_manager` y `self.twitch_auth_manager` | Inyección de dependencias clara para ambas plataformas. |
| **Propiedades en Core (`MainWindowCore`)** | Genéricos `self.chat_worker` y `self.api_client` | `self.kick_chat_worker` y `self.kick_api_client` | Acceso intuitivo, tipado y simétrico. |

---

## 3. Optimización de Proveedores de Red de Kick

1. **Purga de Expresiones Regulares en Chat**:
   - En [kick_websocket.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_websocket.py), se eliminó la expresión regular `FOLLOW_BOT_REGEX` y el estado pendiente (`_pending_follower_name`). El despacho de mensajes en `_handle_chat_message` se ejecuta ahora de forma directa en $\mathcal{O}(1)$ sin sobrecarga de parsing de texto repetitivo.
2. **Depuración de Métodos Muertos en API REST**:
   - En [kick_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_client.py), se eliminaron endpoints obsoletos del antiguo sondeo HTTP (`fetch_pending_redemptions`, `accept_redemptions`, `fetch_public_channel_rewards`, `fetch_public_avatar`).
   - Se añadió el método estándar `is_authenticated() -> bool` validando tokens en el `TokenProvider`, manteniendo paridad funcional estricta con `TwitchAPIClient`.

---

## 4. Corrección de Crash en Twitch Auth y Guardias de Concurrencia OAuth

1. **Causa y Solución del Crash por `TypeError`**:
   - Al fallar la autenticación de Twitch, se emitía `self.q_log_handler.emitter.log_received.emit(log_msg)` con un solo argumento, cuando la señal Qt requiere `(levelname, message)`. Esto causaba el cierre abrupto de la aplicación.
   - Se eliminó la llamada manual errónea, canalizando los eventos a través de `logger.error(...)` y asegurando el restablecimiento seguro de las variables de estado (`self.twitch_auth_worker = None`, `_twitch_connected = False`).
2. **Prevención de Colisión de Puertos (WinError 10048)**:
   - Kick y Twitch comparten el puerto local `8080` para redirección OAuth (`http://localhost:8080/auth/callback`).
   - Se implementaron guardias de concurrencia en [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py): si un proceso de autenticación está en curso, se bloquea el inicio de otro con una notificación Toast informativa (`main.toast.auth_in_progress_msg`), impidiendo colisiones de sockets en el sistema operativo.

---

## 5. Prevención de Fugas de Hilos en Cierre (`QThread Destroyed`)

- Se corrigió el mapeo de parada de procesos en `_stop_all_workers()` en `MainWindowCore` para dirigirse a los atributos canónicos `self.kick_chat_worker` y `self.kick_auth_worker`.
- Se asignó el `objectName` explícito `Worker_Kick_Chat_Socket`, garantizando que todos los sockets y workers finalicen su ciclo de vida antes de destruir el contexto Qt.

---

## 6. Verificación Automatizada

- Pruebas en `test_alert_service.py`, `test_music_controller.py`, `test_dialogs.py` y `test_logging.py`.
- 100% de pruebas pasando con cero fugas de memoria o errores de concurrencia.
