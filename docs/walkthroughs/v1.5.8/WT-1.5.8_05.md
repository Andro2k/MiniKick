# Walkthrough v1.5.8_05: Separación y Renombrado Simétrico de Componentes Kick y Twitch

## 1. Resumen Ejecutivo
Siguiendo la auditoría de modernización de Kick (0 ms WebSocket) y el desacoplamiento arquitectónico, se estandarizó la nomenclatura y organización de módulos entre **Kick** y **Twitch**. Se resolvió la asimetría histórica derivada de los orígenes mono-plataforma del proyecto, separando workers y dotando a las clases y propiedades del Core de nombres simétricos y unívocos, garantizando el 100% de compatibilidad hacia atrás.

---

## 2. Asimetrías Corregidas

| Dominio | Antes | Ahora | Beneficio |
| :--- | :--- | :--- | :--- |
| **Worker de Canjes Twitch** | `TwitchRewardWorker` dentro de `rewards_worker.py` | `backend/workers/twitch_reward_worker.py` | Archivo dedicado, simétrico con `twitch_chat_worker.py` y `twitch_auth_worker.py`. |
| **WebSocket de Kick** | `ChatSocketManager` en `kick_websocket.py` | `KickWebSocketManager` (con alias `ChatSocketManager`) | Simetría explícita con `TwitchChatSocketManager`. |
| **Autenticación Kick** | `AuthManager` en `oauth_service.py` | `KickAuthManager` (con alias `AuthManager`) | Simetría explícita con `TwitchAuthManager`. |
| **Contenedor DI (`AppContainerCore`)** | `self.auth_manager` | `self.kick_auth_manager` y `self.auth_manager` | Nombres claros para ambas plataformas (`kick_auth_manager` vs `twitch_auth_manager`). |
| **Propiedades en Core (`MainWindowCore`)** | Solo `self.chat_worker` y `self.api_client` | `self.kick_chat_worker` / `self.kick_api_client` con alias heredados | Acceso intuitivo y simétrico en controladores y vistas. |

---

## 3. Detalle de Cambios Realizados

### A. Extracción de `TwitchRewardWorker`
- **Nuevo Archivo:** [`backend/workers/twitch_reward_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_reward_worker.py)
  - Contiene exclusivamente la lógica del WebSocket de Twitch EventSub para recompensas por puntos de canal y alertas.
- **Re-exportación:** En [`backend/workers/rewards_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/rewards_worker.py) se re-exporta `TwitchRewardWorker` desde el nuevo archivo para evitar rotura de referencias externas.
- **Paquete de Workers:** [`backend/workers/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/__init__.py) ahora importa directamente desde `.twitch_reward_worker`.

### B. Estandarización de `KickWebSocketManager`
- En [`backend/providers/chat/kick_websocket.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_websocket.py), la clase principal se renombró a `KickWebSocketManager`.
- Se definió el alias `ChatSocketManager = KickWebSocketManager` al final del archivo y se exportó en [`backend/providers/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/__init__.py).

### C. Estandarización de `KickAuthManager`
- En [`backend/services/auth/oauth_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py), la clase de OAuth de Kick se renombró a `KickAuthManager`.
- Se conservó `AuthManager = KickAuthManager` para total compatibilidad.
- Ambos gestores (`KickAuthManager` y `TwitchAuthManager`) están exportados en [`backend/services/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/__init__.py).

### D. Simetría y Eliminación de Redundancias en el Core, Contenedor y Controladores
- En [`backend/core/app_container_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_container_core.py):
  - Se eliminó la doble asignación `self.log_storage = self.system_log_storage`, conservando un único atributo canónico: `self.system_log_storage`.
  - Se eliminó la doble asignación `self.auth_manager = self.kick_auth_manager`, conservando de forma simétrica: `self.kick_auth_manager` y `self.twitch_auth_manager`.
- En [`backend/controllers/rewards_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/rewards_controller.py):
  - Se erradicó el parámetro y atributo genérico `auth_manager` y la asignación `self.auth_manager = self.kick_auth_manager`.
  - Ahora recibe y maneja exclusivamente `kick_auth_manager` en simetría directa con `twitch_auth_manager`.
- En [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py):
  - Se erradicaron por completo las dobles asignaciones (`self.auth_worker = self.kick_auth_worker` o `self.chat_worker = self.kick_chat_worker`).
  - Ahora se utilizan única y directamente los atributos canónicos: `self.kick_chat_worker`, `self.kick_api_client` y `self.kick_auth_manager`, simétricos con `self.twitch_chat_worker`, `self.twitch_api_client`, etc.

### E. Watchdog Auto-Advance en AlertQueue y Previsualización de Alertas
- **Causa del bloqueo de previsualización**: En [`AlertQueue`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/alerts/alert_queue.py), la primera alerta quedaba como activa indefinidamente si ningún cliente WebSocket enviaba el ACK `alert_finished` (por ejemplo, si el usuario probaba sin tener el overlay abierto en OBS). Esto congelaba la cola impidiendo probar más alertas (acumulándose en cola).
- **Watchdog Timer**: Se implementó un temporizador de seguridad automático en `AlertQueue` basado en `duration_ms` + margen que libera automáticamente `_active_alert` y despacha la siguiente alerta sin bloquearse jamás.
- **Botón Previsualizar Overlay**: En [`AlertsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py) y [`AlertsController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/alerts_controller.py), se añadió un botón directo para abrir el overlay en el navegador predeterminado del sistema con un clic, permitiendo ver las alertas animadas en tiempo real.

### F. Resolución de Fallo Crítico en Cierre (QThread Destroyed)
- **Causa**: Al cambiar `self.chat_worker` a `self.kick_chat_worker`, el método `_stop_all_workers()` en [`main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py) consultaba el atributo inexistente `chat_worker` (obteniendo `None`), por lo que nunca ordenaba la detención del socket de Kick. Al cerrarse la app, Qt lanzaba `QThread: Destroyed while thread 'Worker_Chat_Socket' is still running`.
- **Solución**: Se corrigió el mapeo en `_stop_all_workers()` para apuntar a `self.kick_chat_worker` y `self.kick_auth_worker`, y se renombró el `objectName` a `Worker_Kick_Chat_Socket`. El hilo ahora se detiene y cierra limpiamente.

---

## 4. Verificación y Resultados

```bash
.venv\Scripts\python -m pytest resources/tests/
============================ 196 passed in 11.87s =============================
```

- **196 pruebas unitarias pasando al 100%**.
- Nuevo test unitario `test_alert_queue_watchdog_auto_advance` validando el avance desatendido sin bloqueos.
- Cero advertencias ni hilos huérfanos en el apagado.
