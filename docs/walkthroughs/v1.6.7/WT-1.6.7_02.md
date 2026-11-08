# Walkthrough Técnico — MiniKick v1.6.7 (Paso 02)

Se estandarizaron los mensajes de log de la aplicación: todos se emiten en inglés fijo y ya no dependen del sistema de traducción. Donde el mismo texto también se muestra al usuario (avisos y toasts), se mantuvo la traducción en la interfaz y se escribió por separado la línea de log en inglés. Módulos afectados: conexiones de Kick y chat en vivo, proveedores de TikTok, YouTube y Twitch, workers de autenticación, actualizador y Twitch, proveedor de música de YouTube, ventana de recompensas, conexiones de plataformas y arranque (diálogo de crash).

---

## Novedades

- Los logs de recompensas de Kick (fallo de API, preparación de la consulta, archivo de media ausente y recompensa sin configurar) se escriben en inglés fijo.
- Los logs de TikTok (usuario inexistente, transmisión sin conexión, restricción de edad, rechazo HTTP 400 del WebSocket y usuario vacío) se escriben en inglés fijo.
- Los proveedores de YouTube (video no encontrado, transmisión no disponible) y el worker de Twitch (canal vacío) registran ahora una línea de log propia en inglés en el punto donde ocurre el error.

## Mejoras

- Se retiró la traducción de todas las llamadas de log detectadas por un análisis AST (directas o mediante variables intermedias): kick, platform_connections, rewards, tiktok_provider, kick_auth_worker, updater_worker y crash.
- `live_chat` deja de registrar el texto traducido del error del worker: registra un mensaje fijo ("stream is offline or unavailable" o "worker stopped after an error") y el detalle queda en el log del worker de origen.
- La línea de Loudness del proveedor de música de YouTube estaba escrita en español; ahora está en inglés.
- El `ValueError` de "usuario no encontrado" de Twitch Helix usa un texto fijo en inglés (sus llamadores solo lo capturan y lo registran).
- Se eliminaron de `en.json` y `es.json` las claves que quedaron sin uso: `crash_dialog_failed`, `ws_rejected_400`, `user_not_found`, `api_error`, `api_error_setup`, `reward_file_missing` y `reward_no_rewards`. Se conserva `api_offline`, que alimenta un toast de la interfaz.

## Correcciones

- Con el canal de Twitch vacío, el log mostraba el mensaje traducido a través del manejador genérico de excepciones; ahora el worker registra la causa en inglés, emite el mensaje traducido a la interfaz y termina sin lanzar excepción.
- Se evita que el idioma de la interfaz cambie el texto de los logs, lo que dificultaba comparar registros de usuarios con distinto idioma.

> [!NOTE]
> Quedan guiones largos (—) en algunos logs en inglés. No afectan al idioma, pero pueden sustituirse por "-" si se quiere ASCII puro.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| Análisis AST de llamadas de log que usan i18n (directo o por variable) | 1 coincidencia, falso positivo: `tiktok_provider.py:313` usa un f-string en inglés |
| Pruebas de live chat, workers, TikTok, Twitch, contratos de proveedores, logging estructurado y conexión de Kick | 73 aprobadas, 1 fallida |
| Prueba fallida: `test_chat_and_reward_workers_stop_sets_interruption_and_quit` | Intermitente por una carrera con el hilo del worker; también falla en el commit anterior a estos cambios (4 de 5 ejecuciones) |
| `resources/tests/test_architecture_and_placement_auditors.py` | 9 aprobadas |
| Suite rápida de auditorías de calidad | 11 de 12 aprobadas; falla Project Translation Keys por la clave `music.youtube.com` detectada en `backend/utils/youtube_url.py`, ajena a este paso |
| Entorno | Python 3.12 en la verificación; el proyecto declara 3.14 |
