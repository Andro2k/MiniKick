# Walkthrough Técnico — MiniKick v1.6.6 (Paso 11)

Auditoría de `backend/database` y primera fase de su limpieza y organización, sobre el HEAD `bc99415` de `release/v1.6.6`. La auditoría inventarió las 19 tablas declaradas (25 objetos con las tablas virtuales de búsqueda de texto completo), buscó columnas y tablas sin lectores, revisó la retención de datos y el sistema de migraciones. Este paso corrige un error que introdujo el paso 09, elimina la única tabla obsoleta confirmada y añade un servicio de mantenimiento que informa del estado de la base de datos y detecta objetos que el esquema actual ya no declara. La consolidación de columnas en JSON y la división de `DatabaseManager` quedan como fases siguientes, con los datos de este informe. Módulos afectados: `backend/database/database_manager.py`, `backend/database/migrations.py`, `backend/services/system/identity.py` (nuevo), `backend/services/system/db_maintenance_service.py` (nuevo), `backend/services/chat/timers_service.py`, `backend/core/app_container_core.py`, `backend/config/toml_config_provider.py`, `bootstrap/config.py`, `bootstrap/crash.py`, `backend/controllers/settings_controller.py`, `backend/controllers/logs_controller.py`, `frontend/main_window.py` y las pruebas `test_primary_identity.py`, `test_database_schema_cleanup.py` y `test_database_maintenance.py` (nuevas).

Validado con 16 pruebas nuevas (7 de identidad, 3 de migración, 6 de mantenimiento), una migración real de una base creada con el código anterior, la batería de pruebas relevante (183 pasan) y los auditores del proyecto (fronteras de arquitectura, DRY, código muerto, ubicación de archivos, parámetros sin uso y textos hardcodeados), todos en verde. Los cambios se entregan como `0014-database-obsolete-cleanup-and-identity-fix.patch` y `0015-database-maintenance-service.patch`; aplican en secuencia sobre `bc99415`.

---

## Corrección del paso 09

El walkthrough del paso 09 afirmaba que `DatabaseManager` seguía leyendo `tiktok_target_channel` y `youtube_target_channel` de la tabla `settings` «en su propia migración de esquema». Era incorrecto: esa lectura estaba en `DatabaseManager.get_primary_identity()`, un método de ejecución normal, no una migración. Tras migrar los ajustes a TOML, esas dos claves se leen y escriben únicamente a través de `settings_storage` (`config.toml`), de modo que `get_primary_identity()` leía una copia obsoleta de SQLite. Efecto: el contacto inicial del formulario de errores y del informe de fallos salía vacío o desactualizado cuando la única identidad disponible era un canal de TikTok o YouTube configurado a mano y no había perfil de canal en caché. Se corrige en este paso (ver «Novedades»).

## Auditoría

| Hallazgo | Evidencia |
| --- | --- |
| `timer_execution_logs` es de solo escritura | Solo `log_timer_execution` (llamado desde `TimersService`) la escribe; ninguna consulta la lee ni el panel de analíticas la usa; su columna `message_sent` no se referencia en ningún otro lugar |
| `channel_profiles` duplica datos | `save_channel_profile` guarda 9 columnas sueltas (`username`, `bio`, `avatar_url`, `followers`, `room_id`, `category`, `affiliate_status`, `vods_enabled`, `created_at`) y además el perfil completo en `raw_json`; `load_all_channel_profiles` solo lee `platform` y `raw_json` |
| `alert_configs` tiene 30 columnas | 3 de identidad y estado (`platform`, `alert_type`, `enabled`) más 27 de contenido y estilo que se consumen siempre juntas como un diccionario |
| `DatabaseManager` mezcla responsabilidades | ~900 líneas: conexión y recuperación, 400 líneas de DDL, migraciones y además lógica de negocio (registros de spam, canjes y comandos, cola de música, analíticas del panel, perfiles de canal, identidad); los servicios llaman a `self.storage.db_manager.log_*` |
| DDL duplicado | `_create_tables` y la migración 001 mantienen listas paralelas de columnas esperadas |
| Método sin llamadores | `DatabaseManager.load_channel_profile` |
| Crecimiento acotado | Ya existe retención mediante disparadores SQL (`system_logs` 2000 filas, `spam_violations`, `timer_execution_logs`, `reward_redemptions` y `music_queue` por cantidad, `command_execution_logs` 30 días, `avatar_cache` 15 días); las tablas de registro tienen límite. La caché de búsquedas de YouTube (`youtube_search_cache`) no tiene disparador de recorte (se eliminó `prune_youtube_cache`) ni borrados en `music_storage`: cada consulta distinta añade una fila pequeña, y el informe de mantenimiento mostrará su tamaño |
| `settings` | Tabla heredada: origen de la migración a TOML y de su marca; no debe eliminarse todavía |

## Novedades

- **Identidad primaria** (`backend/services/system/identity.py`): `pick_primary_identity(profiles, config)` es una función pura (perfiles en orden Kick, Twitch, TikTok, YouTube; después los canales configurados) y `resolve_primary_identity()` compone las fuentes reales: perfiles de la base de datos y `config.toml` ubicado junto a ella. Los tres llamadores (`SettingsController`, `LogsController` y el informe de fallos de `bootstrap/crash.py`) la usan en lugar del método eliminado. `CONFIG_FILE_NAME` pasa a `toml_config_provider.py` como única definición del nombre del archivo.
- **Migración 002**: elimina `timer_execution_logs`, sus dos índices y su disparador de recorte. Se retiran además la creación de esa tabla, `log_timer_execution`, la llamada de `TimersService` y el método muerto `load_channel_profile`. La versión de esquema actual pasa a 2. En una base nueva el objeto no llega a crearse.
- **`DatabaseMaintenance`** (`backend/services/system/db_maintenance_service.py`):
  - `collect_stats()` devuelve tamaño del archivo, tamaño del WAL, espacio libre y filas por tabla (sin tablas sombra de búsqueda de texto completo).
  - `find_obsolete_objects()` detecta tablas, índices o disparadores presentes en la base pero que el esquema actual no declara. Compara con una base de referencia recién creada por el propio `DatabaseManager`, así que no hay una lista paralela que mantener.
  - `run()` ejecuta un punto de control del WAL, un `VACUUM` solo si el espacio libre supera 4 MB y el 20 % del archivo, `PRAGMA optimize` y escribe un resumen en el log; los objetos no declarados se registran como advertencia y **nunca se eliminan automáticamente**. Nunca propaga excepciones.
  - Se construye en el contenedor (`container.db_maintenance`) y se ejecuta en un hilo de segundo plano 10 s después de mostrarse la ventana, salvo que ya se esté cerrando.

## Mejoras

- **Separación de responsabilidades**: la identidad ya no vive en el gestor de la base de datos ni depende de su tabla de ajustes; la política de mantenimiento vive en un servicio, no en el gestor.
- **Alta cohesión**: `DatabaseManager` pierde dos métodos de negocio y la tabla muerta; el servicio de mantenimiento solo se ocupa de higiene física y diagnóstico.
- **DRY**: la detección de objetos obsoletos reutiliza el esquema real en lugar de duplicarlo.
- **Demostración real**: sobre una base con 400 filas de 30 KB insertadas y borradas más una tabla `viejo_cache` creada a mano, `run()` recuperó 11.72 MB y registró `table:viejo_cache` como objeto no declarado.

## Compromisos y riesgos a tener en cuenta

- **Pérdida intencionada**: el contenido de `timer_execution_logs` desaparece al migrar. Ningún código lo leía; la tabla se limitaba a las últimas 1000 filas.
- **Volver a un binario anterior**: tras abrir una base con esta versión, un binario anterior debería seguir arrancando (recrearía la tabla vacía y no vería su propia versión de esquema como pendiente); no se ha probado.
- **`VACUUM` y escrituras**: mientras dura un `VACUUM` las escrituras esperan (con `busy_timeout` de 30 s). Solo se ejecuta cuando hay un mínimo de 4 MB recuperables, por lo que será poco frecuente y breve en bases del tamaño actual.
- **Detección de objetos obsoletos**: crea un archivo temporal con el esquema de referencia en cada ejecución de `run()` (decenas de milisegundos, en segundo plano). Un objeto creado a mano por el usuario se informa pero no se toca.
- **Informe de fallos y TOML**: leer `config.toml` en `bootstrap/crash.py` puede, como en cualquier lectura, mover un archivo ilegible a cuarentena; el comportamiento es el mismo que en el arranque normal.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `test_primary_identity.py` | 7 pasan (orden de perfiles, retirada de `@`, canales configurados como respaldo, vacío, lectura de TOML en lugar de SQLite obsoleto, perfil en caché, el resolutor nunca propaga errores) |
| `test_database_schema_cleanup.py` | 3 pasan (base nueva sin objetos de temporizadores, actualización de una base heredada conservando los demás datos, reapertura sin cambios) |
| `test_database_maintenance.py` | 6 pasan (estadísticas sin tablas sombra, recuperación de espacio con umbrales bajos, sin tocar el archivo con poco espacio libre, base nueva sin objetos obsoletos, detección de objetos no declarados, `run` sin excepciones con la base inutilizable) |
| Migración real | Base creada con el código anterior (versión 1) y datos en 7 tablas; al abrirla con el nuevo código pasa a versión 2, conserva todas las filas, sin la tabla obsoleta, con `integrity_check` correcto y sin violaciones de claves foráneas |
| Batería relevante | 183 pasan |
| Auditores CLI (fronteras, DRY, código muerto, ubicación, parámetros sin uso, textos) | Sin hallazgos |

**Limitaciones del entorno de validación:**

- No se pudo ejecutar la aplicación con interfaz ni las pruebas que instancian la ventana principal (*segmentation fault* con Qt sin pantalla, también sin estos cambios). El cableado del mantenimiento en `main_window.py` no tiene prueba automatizada; se valida revisando el log 10 s después del arranque (línea `[Maintenance]`).
- `test_worker_and_core_lifecycle.py::test_chat_and_reward_workers_stop_sets_interruption_and_quit` sigue siendo intermitente y `test_giphy_and_tts_filter.py` depende de la API key y de red de Giphy; ninguno guarda relación con este paso.

## Pendiente (siguientes fases)

- **Consolidación en JSON.** Candidatos con datos: `channel_profiles` (conservar `platform` y `raw_json`, eliminar 9 columnas redundantes sin pérdida de información) y `alert_configs` (conservar `platform`, `alert_type` y `enabled` y mover las 27 columnas de contenido y estilo a una columna JSON, como ya hace `widgets_config` con `config_json`). Se propone columna JSON dentro de SQLite en lugar de archivos sueltos: conserva transaccionalidad, copias de seguridad y granularidad por fila. Cada una requiere una migración con copia previa y verificación.
- **División de `DatabaseManager`**: extraer el DDL a un módulo de esquema, mover los registros de eventos, la cola de música, las analíticas, los perfiles de canal a sus almacenamientos y eliminar las llamadas `storage.db_manager.log_*` de los servicios.
- **Tabla `settings`**: eliminarla en una versión futura, cuando la migración a TOML lleve el tiempo suficiente en producción.
