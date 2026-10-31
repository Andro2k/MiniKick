# Walkthrough Técnico — MiniKick v1.6.6 (Paso 10)

Migración del sistema de configuración (la tabla `settings` de SQLite) a un archivo TOML, sobre el HEAD `009b0ea` de `release/v1.6.6`. La abstracción `SettingsStorage` ya existía en `backend/interfaces/i_settings.py`, pero solo la usaban dos servicios como anotación de tipo; el contenedor, el proveedor de YouTube y el arranque instanciaban `SQLiteSettingsStorage` directamente en cinco puntos, de modo que cambiar de almacenamiento obligaba a tocar código de negocio. Este paso sustituye esa interfaz por `IConfigProvider`, una clase abstracta que concentra la semántica común (caché, bloqueo, coerción de tipos, manejo de errores) y exige a cada formato solo dos primitivas (`_load` y `_store`), añade `TomlConfigProvider` como implementación concreta, mueve la selección de la implementación al único punto de composición (`StartupServices`) y migra automáticamente la configuración existente en el primer arranque. Módulos afectados: `backend/interfaces/i_config_provider.py` (nuevo), `backend/config/toml_config_provider.py` (nuevo), `bootstrap/config.py` (nuevo), `bootstrap/services.py`, `bootstrap/translator.py`, `backend/core/app_container_core.py`, `backend/providers/music/youtube_provider.py`, `backend/controllers/music_controller.py`, `backend/services/system/backup_service.py`, `backend/services/system/browser_service.py`, `pyproject.toml` y `requirements.in`. Se eliminan `backend/interfaces/i_settings.py`, `backend/database/settings_storage.py` y `resources/tests/test_settings_storage_cache.py`.

Validado con 17 pruebas nuevas (`test_config_provider.py`, `test_config_bootstrap.py`), la batería de pruebas relevante (146 pasan), una prueba de extremo a extremo del arranque con una base SQLite preexistente y los auditores del proyecto (fronteras de arquitectura, DRY, código muerto, ubicación de archivos, parámetros sin uso y textos hardcodeados), todos en verde. El cambio se entrega como `0013-toml-config-provider.patch`; aplica limpio sobre `009b0ea` y también tras `0011` y `0012`.

---

## Diagnóstico

| Medida | Valor |
| --- | --- |
| Puntos que construían `SQLiteSettingsStorage` | 5 (contenedor, 2 en el proveedor de YouTube, arranque y traductor) |
| Llamadas a la API de ajustes en el código | `load_string` 61, `load_bool` 34, `save_string` 29, `save_bool` 15, `save_all` 9, `get_all` 1, `delete_key_prefix` 1 |
| Consumidores tipados con la abstracción | 2 (`BackupService`, `BrowserService`) |
| `delete_key_prefix` en la interfaz anterior | No declarado, aunque se usa |

El volumen de llamadas (unas 150) justifica conservar los nombres de método actuales: la migración no toca ninguno de esos consumidores.

## Novedades

- **`IConfigProvider`** (`backend/interfaces/i_config_provider.py`): clase abstracta con la API que ya consumía la aplicación (`load_string`, `save_string`, `load_bool`, `save_bool`, `get_all`, `save_all`, `delete_key_prefix`). Es la plantilla del comportamiento común: carga perezosa a un snapshot inmutable (las lecturas no necesitan bloqueo), escrituras de lectura-modificación-escritura bajo un `RLock`, confirmación en memoria solo si la persistencia tiene éxito, y errores de carga o escritura registrados sin propagarse. Cada implementación solo aporta `_load()` y `_store(data)`.
- **`TomlConfigProvider`** (`backend/config/toml_config_provider.py`): lectura con `tomllib` (con `tomli` como respaldo en Python 3.10) y escritura con `tomli-w`. La escritura es atómica: se vuelca a un archivo temporal en el mismo directorio y se reemplaza con `os.replace`, con hasta 5 reintentos de 20 ms ante `PermissionError` (antivirus o indexadores en Windows). Un archivo ilegible como TOML se mueve a `config.toml.corrupt-<fecha>` y se arranca con valores por defecto.
- **Migración de arranque** (`bootstrap/config.py`): si `config.toml` no existe y la tabla `settings` tiene filas, se importan tal cual (como texto, sin inferir tipos) y se registra la marca `settings_migrated_to_toml` en SQLite. La marca evita reimportar valores obsoletos si el TOML se borra o se pone en cuarentena. Si la escritura falla, no se marca y se reintenta en el siguiente arranque. En una instalación nueva no se crea nada hasta el primer guardado.
- **Composición única**: `StartupServices.create_config(db_manager)` crea el proveedor una sola vez (memoizado) y lo reutilizan `create_translator` y `create_container`; el contenedor lo expone como `settings_storage`, por lo que ningún consumidor cambia. `YouTubeMusicProvider` recibe ahora `settings_storage` por constructor en lugar de construir su propio almacenamiento.

## Mejoras

- **Inversión de dependencias**: lógica de negocio, controladores y vistas dependen de `IConfigProvider`; solo `StartupServices` conoce `TomlConfigProvider`. Cambiar a otro formato es escribir una subclase con `_load` y `_store` y modificar una línea de composición. Las pruebas lo demuestran ejecutando el mismo contrato contra el TOML y contra una implementación en memoria.
- **Separación de responsabilidades**: la persistencia de ajustes ya no pasa por SQLite ni por el gestor de la base de datos; la presentación no conoce rutas ni formatos.
- **Alta cohesión**: `IConfigProvider` solo gestiona configuración clave-valor; la migración vive en `bootstrap`, no en el proveedor; el formato de archivo vive únicamente en `TomlConfigProvider`.
- **DRY y YAGNI**: la coerción de tipos, la caché, el bloqueo y el manejo de errores existen una sola vez. No hay esquema versionado, secciones anidadas, recarga en caliente ni escritura diferida: no hay evidencia de que hagan falta.
- **Formato legible**: los booleanos nuevos se guardan como `true`/`false` y los enteros como enteros; el archivo `config.toml` es editable a mano.

## Compromisos y riesgos a tener en cuenta

- **Valores migrados como texto**: la migración copia lo que había (`"1"`, `"0"`, `"65"`) como cadenas. Los lectores toleran ambas formas (`load_bool` acepta `"1"`/`"true"` y booleanos nativos; `load_string` devuelve `"1"`/`"0"` para booleanos), y cada valor se reescribe con su tipo nativo la próxima vez que se guarda. `get_all()` mantiene el comportamiento anterior (convierte `"1"`/`"0"` en booleano), así que las copias de seguridad en JSON no cambian.
- **Visibilidad de `overlay_session_token`**: esta clave (que `BackupService` ya excluye de las copias) pasaba de una base SQLite a un archivo de texto plano en el mismo directorio de datos del usuario. La exposición es equivalente a la anterior, pero ahora es legible con un editor. Los tokens de autenticación siguen en sus tablas cifradas y no se migran.
- **Escritura completa por cada guardado**: cada cambio reescribe el archivo (centenares de bytes) de forma atómica. Es comparable a la escritura SQLite anterior; si algún día se observa en el log un coste en el hilo de interfaz, la opción es escritura diferida (no incluida por no haber evidencia).
- **SQLite sigue existiendo para el resto de datos** (comandos, recompensas, temporizadores, tokens, logs, etc.). La tabla `settings` se conserva como origen de la migración y como copia de respaldo; `DatabaseManager` sigue leyendo `tiktok_target_channel` y `youtube_target_channel` de ella en su propia migración de esquema, por lo que no debe eliminarse.
- **Dependencias**: se añaden `tomli-w` (siempre) y `tomli` (solo Python < 3.11) a `pyproject.toml` y `requirements.in`. `uv.lock` y `requirements.txt` están generados y deben recompilarse (`uv lock` y `uv pip compile pyproject.toml -o requirements.txt`).
- **Reversión**: volver a SQLite requiere una implementación de `IConfigProvider` para SQLite (dos primitivas) y revertir la línea de composición; los valores guardados después de la migración solo estarían en el TOML.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `test_config_provider.py` | 13 pasan (contrato idéntico en TOML y en memoria, flags heredados, borrado por prefijo, normalización, persistencia entre instancias, archivo ausente, archivo corrupto en cuarentena, fallo de escritura sin pérdida ni residuos, escrituras concurrentes) |
| `test_config_bootstrap.py` | 4 pasan (importación única, segundo arranque ignora SQLite, TOML borrado no se reimporta, instalación nueva sin archivo ni marca) |
| Batería relevante | 146 pasan |
| Arranque real con SQLite previo | Idioma leído de `config.toml`, proveedor reutilizado entre traductor y contenedor, escritura con tipos nativos y `get_all()` compatible con copias de seguridad |
| Auditores CLI (fronteras, DRY, código muerto, ubicación, parámetros sin uso, textos) | Sin hallazgos |

**Limitaciones del entorno de validación:**

- No se pudo ejecutar la aplicación con interfaz ni las pruebas que instancian la ventana principal (*segmentation fault* con Qt sin pantalla, también sin estos cambios): `test_window_state_persistence.py` y `test_auto_update_setting.py`. La API de `StartupServices` que usan esas pruebas y `resources/tools/generate_screenshots.py` no cambia de firma.
- `test_worker_and_core_lifecycle.py::test_chat_and_reward_workers_stop_sets_interruption_and_quit` sigue siendo intermitente (carrera entre `run()` y `stop()`), sin relación con este paso.
- `test_giphy_and_tts_filter.py` (3 pruebas) depende de la API key y de red de Giphy.

## Pendiente (no incluido en este paso)

- **Recompilar `uv.lock` y `requirements.txt`** tras añadir las dependencias.
- **Mover los consumidores a los nombres de la API que prefieras** si algún día se quiere una API tipada (`get`/`set`); hoy se conservaron los 150 puntos de llamada intactos a propósito.
- **Probar en la máquina de desarrollo** el primer arranque con una base existente (comprobar `config.toml` y la marca) y el cierre y reapertura de la aplicación.
