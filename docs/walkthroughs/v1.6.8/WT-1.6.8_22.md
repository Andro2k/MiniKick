# Walkthrough Técnico — MiniKick v1.6.8 (Paso 22)

Un login OAuth pendiente impedía cerrar la app: al cerrar, `Worker_Auth` seguía esperando el callback y un Ctrl+C terminaba en aborto de Qt. Detectado en el log de una sesión en Linux.

---

## Correcciones

- **Cierre con login pendiente:** `OAuthCallbackServer.capture_auth_code` esperaba hasta 120 s sin comprobar si el worker había recibido `requestInterruption()` durante el apagado (`WorkerShutdownCoordinator._request_stop`). Se añade el parámetro opcional `should_cancel` y el bucle sale en cuanto devuelve `True` (respuesta en ≤1 s, el `timeout` de `handle_request`).
- **Sin acoplar el servicio a Qt:** `should_cancel` es un `Callable[[], bool]` propagado por `login()`/`_new_login()` de Kick y Twitch; los workers pasan `self.isInterruptionRequested`. El servicio de auth sigue sin importar Qt.

## Evidencia en el log

- `[Worker] 'Worker_Kick_Auth' is still running after 10.0 seconds` → `KeyboardInterrupt` en `_poll_workers` → `QThread: Destroyed while thread 'Worker_Auth' is still running` → `Fatal Python error: Aborted`.
- La primera URL de autorización tenía `client_id=` vacío por falta de `api_keys.py` (ya corregido por el usuario).

## Archivos afectados

| Capa | Archivo |
| --- | --- |
| Servicio | `backend/services/auth/auth_service.py` |
| Workers | `backend/workers/kick_auth_worker.py`, `backend/workers/twitch_auth_worker.py` |

## Verificación

- Servidor real en localhost: con `should_cancel` activado a los 0.5 s, `capture_auth_code` devuelve `None` en 1.0 s; sin cancelación respeta `timeout_seconds` (2 s).
- `project_quality_suite --quick`: sin cambios respecto a la base (`Frontend QSS Roles` y `Frontend Qt Windows` ya fallaban).
- Pendiente: probar en Linux cerrando la app con el navegador de login abierto, sin Ctrl+C.
