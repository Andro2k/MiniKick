# Walkthrough Técnico — MiniKick v1.6.6 (Paso 05)

Optimización del lag al navegar rápido entre módulos, a partir del análisis de `minikick.log` y `minikick_1.log` sobre el HEAD `f8bb1de` de `release/v1.6.6`. Se elimina el coste por visita de lecturas SQLite repetidas (`ChatService.get_settings()` abría 50 conexiones por llamada), se difiere la importación de `edge_tts`/`aiohttp` hasta el primer uso de la voz web, se añade el desglose `create` / `switch` / `hooks` al log de navegación y se cachea el descifrado DPAPI de tokens, que mantenía a Settings en ~300 ms por visita. Módulos afectados: `backend/database/settings_storage.py`, `backend/database/encrypted_token_storage.py`, `backend/providers/voices/online_provider.py`, `backend/utils/text_utils.py`, `frontend/main_window.py` y las pruebas `test_settings_storage_cache.py` y `test_encrypted_token_storage.py`.

Validado con 5 pruebas nuevas de la caché de ajustes, 6 pruebas nuevas de la caché de descifrado y los auditores del proyecto (fronteras de arquitectura, DRY, código muerto, ubicación de archivos y parámetros sin uso), todos en verde. Los cambios se entregan como `0006-perf-settings-cache-lazy-edge-tts.patch` y `0007-perf-token-decrypt-cache.patch`; ambos aplican en secuencia sobre `f8bb1de`.

---

## Diagnóstico a partir de los logs

El log nuevo incorpora el desglose de navegación añadido en este paso, lo que permite separar creación de la vista, cambio de página y hooks posteriores.

| Medida | Log 1 | Log 2 |
| --- | --- | --- |
| Chat, revisita | 149.85 / 151.30 / 149.54 ms | 14.36 / 33.77 ms |
| Chat, primera visita | 1177 ms | 608 ms |
| Hidratación `chat settings` | 134 ms | 3.42 ms |
| Settings, revisita | 322 / 331 ms | 315.45 / 329.58 ms (`hooks` 295.68 / 305.04) |
| Triggers, revisita | 62–64 ms | 60.27 ms (`hooks` 25.35) |
| Bootstrap total | 8282 ms | 1664 ms |
| Imports de módulos | 2886 ms | 869 ms |

- **Chat**: el coste recurrente de ~150 ms desapareció. Cada `view_shown` dispara `_sync_tts_command_from_db`, que llama a `ChatService.get_settings()`. Esa función abría 50 conexiones SQLite por llamada (cada `load_string` abría una nueva y ejecutaba 4 PRAGMA).
- **Settings**: sigue en ~300 ms por visita y el log lo localiza en `hooks` (el `switch` ronda 2–8 ms): la causa es `_update_integrations_status_ui()`. Esa función llama a `is_authenticated()` para Kick y Twitch, y cada llamada descifra `access_token` y `refresh_token` con DPAPI (`CryptUnprotectData`), es decir, 4 descifrados por visita.
- **Arranque**: la mejora de 8282 a 1664 ms no es atribuible solo a este paso. El segundo log es muy probablemente un arranque en caliente (caché de archivos y de bytecode), mientras que el primero parece un arranque en frío. Lo atribuible a los cambios es la hidratación de `chat settings` (134 ms a 3.42 ms).

## Novedades

- **Caché de lecturas en `SQLiteSettingsStorage`**: un snapshot por base de datos, compartido entre todas las instancias (el contenedor, el proveedor de YouTube, el traductor y `bootstrap` crean la suya) y poblado con una sola consulta `SELECT key, value FROM settings`. `load_string`, `load_bool` y `get_all` leen del snapshot; `save_string`, `save_all` y `delete_key_prefix` lo invalidan por completo tras confirmar la escritura, de modo que la siguiente lectura recarga con una única conexión. El snapshot nunca se muta una vez creado, por lo que las lecturas concurrentes no necesitan bloqueo.
- **Caché de descifrado en `EncryptedTokenStorage`**: memoiza el texto plano por payload cifrado (clave: valor tras el prefijo `enc:v1:`), con un máximo de 4 entradas y orden LRU. Un token rotado produce un payload distinto y se descifra de nuevo. `save()` y `clear()` vacían la caché. Los campos no sensibles (`expires_at`, `scope`, etc.) nunca se sirven desde la caché: se leen siempre del almacenamiento interno.
- **Desglose en el log de navegación**: `[Perf/Navigation] ... completed in X ms (create=…, switch=…, hooks=…)`. `create` incluye la creación perezosa de la vista, `switch` el `setCurrentWidget` (y por tanto los manejadores de `view_shown`) y `hooks` los refrescos que ejecuta `_handle_navigation` (Dashboard, Settings, Triggers).

## Mejoras

- **Separación de responsabilidades**: el coste de acceso a datos deja de caer sobre la ruta de presentación de cada visita.
- **`ChatService.get_settings()`**: de 35.4 ms y 50 conexiones SQLite por llamada a 0.03 ms y 0 conexiones (medido en el entorno de validación sobre una base temporal, 20 llamadas tras la primera). En Windows el ahorro esperado es mayor, porque abrir conexiones es más caro.
- **Importación perezosa de `edge_tts`** (`online_provider.py`): `edge_tts` y su dependencia `aiohttp` dejan de cargarse al arrancar. `import frontend.main_window` pasa de 781 ms a 546 ms (−30 %) en el entorno de validación. El coste (~260 ms allí) se paga una sola vez, la primera vez que se usa la voz web.
- **Descifrado DPAPI**: 4 llamadas por visita a Settings pasan a 0 tras el primer descifrado de cada token.

## Correcciones

- **Cabecera de `backend/utils/text_utils.py`**: tenía el comentario de ruta con doble barra invertida (`backend\\utils\\...`); ahora sigue la convención del resto de archivos.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `test_settings_storage_cache.py` | 5 pasan (una sola conexión para 100 lecturas, visibilidad entre instancias, conversión de booleanos, invalidación por prefijo, default de `load_bool`) |
| `test_encrypted_token_storage.py` | 12 pasan (6 previas + 6 nuevas: descifrado único, token rotado, campos no sensibles, `save`/`clear`, fallo no cacheado, caché acotada) |
| Batería relevante (contratos, handlers, controladores, auditores) | 96 pasan |
| Auditores CLI (fronteras, DRY, código muerto, ubicación, parámetros sin uso) | Sin hallazgos |

**Fallos preexistentes, sin relación con este paso:**

- `test_giphy_and_tts_filter.py` (3 pruebas): dependen de la API key y de red de Giphy.
- `test_worker_and_core_lifecycle.py::test_chat_and_reward_workers_stop_sets_interruption_and_quit`: intermitente (carrera entre `run()` y `stop()` con `channel_name=""`).
- La suite completa y `test_window_state_persistence.py` producen *segmentation fault* en el entorno de validación (Qt sin pantalla), también sin estos cambios. Conviene correr la suite completa en la máquina de desarrollo.

## Compromisos y riesgos a tener en cuenta

- **Caché de ajustes**: si algo modifica la tabla `settings` desde fuera del proceso mientras la app corre, el cambio no se verá hasta la siguiente escritura hecha por la propia aplicación. Se comprobó que ningún otro código del repositorio escribe en esa tabla.
- **Caché de descifrado**: mantiene en memoria el texto plano de hasta 4 tokens por almacenamiento hasta que se llame a `save()` o `clear()`. La protección en reposo (DPAPI) no cambia, y los tokens ya viven en memoria mientras la sesión está conectada, pero es un compromiso explícito entre seguridad y latencia. Alternativa si se prefiere no retener texto plano: cachear solo un booleano de «descifrable» para `is_authenticated()`, a costa de ampliar la interfaz `TokenStorage`.

## Pendiente (no incluido en este paso)

- **Confirmar el efecto del parche 0007 con un log nuevo**: se espera que `hooks` de Settings baje de ~300 ms. Si no baja, los sospechosos restantes son los 4 `unpolish`/`polish` de `SettingsView.set_integrations_status` y el reparto de `set_connected_platforms` a ~7 vistas.
- **Triggers**: `_fetch_api_rewards()` se ejecuta en cada visita (25–30 ms de `hooks`).
- **Primera visita a cada módulo**: Chat tarda ~540 ms solo en crearse (Settings ~390 ms, Alerts, Triggers, Music y Comandos ~160–220 ms). Una creación anticipada de vistas en tiempo ocioso, por fragmentos, trasladaría ese coste fuera de la interacción.
- **Arranque**: trabajo previo al splash (aplicación, fuentes, base de datos, traductor) e importación de `frontend.main_window` (controladores y servicios) que podrían diferirse tras mostrar el splash.
- **Cierre de la aplicación**: ~1.1 s con detención de workers que no se solapa por completo.
