# Walkthrough Técnico - v1.6.3 / WT-1.6.3_04

**Versión**: v1.6.3
**Fecha**: 2026-10-09
**Origen**: "Plan 1 — Correcciones y refactor del backend". Alcance: **Fase 2 (Fiabilidad e higiene)** completa (tareas 2.1 a 2.4).
**Precedente**: ver `WT-1.6.3_03.md` (Fase 1 — Seguridad).

---

## Novedades

### Excepción `TransientAuthError`

Nueva excepción en la capa de interfaces (`backend/interfaces/i_auth.py`) para distinguir un fallo de
refresco transitorio de un token inválido. Los proveedores pueden capturarla sin acoplarse a la capa de auth.

### Registro numerado de migraciones

Nuevo módulo `backend/database/migrations.py` con `MIGRATIONS: list[tuple[int, Callable[[Connection], None]]]`.
La versión de esquema pasa a derivarse del registro (`CURRENT_SCHEMA_VERSION = max(version)`).

### `requirements-build.txt`

Separación de dependencias de compilación (PyInstaller) de las de ejecución.

---

## Mejoras

### 2.1 Refresh de tokens: transitorio vs inválido

**Archivos**: `backend/services/auth/auth_service.py`, `backend/interfaces/i_auth.py`, `backend/providers/chat/kick_provider.py`

`refresh_token` de Kick y Twitch devolvía `{}` (Kick) o relanzaba y cerraba sesión (Twitch) ante **cualquier**
`RequestException`, tratando un corte de red como sesión caducada. Ahora se clasifica el error:

- `HTTP 400/401` → refresh **inválido**: se limpia la sesión (`logout`) y se registra `logger.warning`.
- Red/timeout/5xx → fallo **transitorio**: se conservan los tokens y se lanza `TransientAuthError`.

`KickAPIClient` captura `TransientAuthError` en su reintento tras un 401 y continúa (no propaga), preservando
el comportamiento previo sin tumbar el worker.

### 2.2 `except Exception: pass` en rutas críticas

**Ámbitos**: `backend/services/auth/`, `backend/database/`, `backend/providers/chat/`, `backend/workers/`

Los `pass` silenciosos se reemplazaron por `logger.debug`/`logger.warning` con contexto, salvo la limpieza de
recursos (`close`, `rollback`, `os.remove` de temporales), donde se mantiene el `pass` con un comentario de una
línea justificando el motivo. Casos destacados:

- `commands_storage`: el fallo al actualizar `command_execution_logs` en un rename ya no es silencioso.
- `database_manager`: un perfil de canal ilegible se registra en `debug` en vez de descartarse en silencio.
- `youtube_provider` / `voice_worker`: fallos de parseo y de inicialización COM pasan a `debug`.
- `kick_ws_provider._on_raw_frame`: los errores de frame ahora se registran en **`warning` la primera vez por
  tipo de evento** (set `_warned_frame_events`), y en `debug` las repeticiones, evitando inundar el log.

### 2.3 Dependencias y `.gitignore`

**Archivos**: `requirements.txt`, `requirements-build.txt`, `.gitignore`

- Se eliminó `asyncio` de `requirements.txt` (es de la stdlib; instalarlo como paquete puede romper el entorno).
- `pyinstaller` se movió a `requirements-build.txt`.
- Se fijaron versiones mínimas `>=` con las que funcionan en el entorno actual (sin upgrades), y se completó el
  archivo con las dependencias de runtime que faltaban (`piper-tts`, `pytchat`, `tiktoklive`) para que la
  instalación en un venv limpio sea funcional.
- `.gitignore`: se añadieron `!requirements.txt` y `!requirements-build.txt` (la regla `*.txt` los ignoraba).

### 2.4 Migraciones numeradas

**Archivos**: `backend/database/migrations.py` (nuevo), `backend/database/database_manager.py`

- El contenido de `_upgrade_schema` se movió **verbatim** a la migración `1` (`_migration_001_...`), sin cambiar
  su lógica (idempotente: solo altera lo que falta).
- `database_manager` ahora aplica las migraciones pendientes en orden mediante `_apply_migrations()`, cada una en
  su propia conexión/transacción, y estampa `PRAGMA user_version` tras cada una.
- `_upgrade_schema` fue eliminado (sin delegadores permanentes).

---

## Correcciones / decisiones de proceso

1. **Conflicto plan ↔ convención del repo (auditor de ubicación).** El Plan 1 pide crear
   `backend/database/migrations.py`, pero el auditor `resources/tools/file_placement_auditor.py` solo admitía
   `*_storage.py`, `database_manager.py` y `__init__.py` en esa carpeta. Como ambos artefactos son del proyecto,
   se **extendió la convención** añadiendo `migrations.py` a `FOLDER_PURITY_RULES` (y a la regla documentada en
   el encabezado del auditor), en lugar de renombrar el módulo. Queda constancia aquí para revisión.
2. **Nueva prueba de arquitectura en rojo por diseño controlado.** Tras aplicar (1), `test_architecture_and_placement_auditors`
   vuelve a pasar sin tocar la aserción de la prueba.

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| backend/interfaces/i_auth.py | Nuevo - excepción `TransientAuthError` |
| backend/interfaces/__init__.py | Mejora - export de `TransientAuthError` |
| backend/services/auth/auth_service.py | Mejora - clasificación de errores de refresh (invalid/transient) |
| backend/providers/chat/kick_provider.py | Mejora - captura de `TransientAuthError` en reintento 401 |
| backend/database/migrations.py | Nuevo - migración 1 + registro `MIGRATIONS` |
| backend/database/database_manager.py | Mejora - `_apply_migrations`, versión derivada, `except` con contexto |
| backend/database/cache_storage.py | Mejora - comentarios en limpieza best-effort |
| backend/database/commands_storage.py | Mejora - log en fallo de actualización de logs |
| backend/database/logs_storage.py | Mejora - comentarios en escritura best-effort a stderr |
| backend/database/music_storage.py | Mejora - comentarios en rollback best-effort |
| backend/providers/chat/kick_ws_provider.py | Mejora - warn-once por evento en `_on_raw_frame` |
| backend/providers/chat/tiktok_provider.py | Mejora - comentarios en desconexión best-effort |
| backend/providers/chat/twitch_ws_provider.py | Mejora - log en callbacks on_connected/on_disconnected |
| backend/providers/chat/youtube_provider.py | Mejora - logs y comentarios en limpieza/parseo |
| backend/workers/music_worker.py | Mejora - log/limpieza en hooks y formateo de duración |
| backend/workers/twitch_rewards_worker.py | Mejora - comentario en cierre de socket best-effort |
| backend/workers/voice_worker.py | Mejora - log en fallo de inicialización COM |
| requirements.txt | Mejora - sin `asyncio`, sin `pyinstaller`, versiones mínimas, runtime completo |
| requirements-build.txt | Nuevo - PyInstaller |
| .gitignore | Mejora - negaciones para los requirements |
| resources/tools/file_placement_auditor.py | Convención - `migrations.py` admitido en `backend/database/` |

---

## Pruebas

- `resources/tests/test_auth_refresh_classification.py` (3 casos): 400/401 → inválido; 5xx/red → transitorio; `TransientAuthError` es `Exception`.
- `resources/tests/test_db_migrations.py` (3 casos): migraciones ordenadas y versionadas; BD nueva alcanza `CURRENT_SCHEMA_VERSION`; migración 1 idempotente.
- Regresión completa: `resources/tests` en **186 pruebas superadas**. Los 2 fallos restantes
  (`test_sqlite_widgets_storage_pruning` por fecha hardcodeada y `test_modern_toast_dynamic_geometry_scaling`
  por geometría de fuente) son **preexistentes y ajenos** a esta fase.

---

## Discrepancias / pendientes anotados (no bloqueantes)

- **`pyproject.toml` aún declara `asyncio` y `pyinstaller`** en `dependencies`. El plan 2.3 solo cubría
  `requirements.txt`, así que no se modificó el `pyproject` (hacerlo obliga a regenerar `uv.lock`). Se deja
  anotado para una tarea aparte si se quiere alinear el manifiesto de `uv`.
- **Aceptación "pip install -r requirements.txt en venv limpio"**: no verificada en esta sesión (requiere red).
- Fase 3 (arquitectura) pendiente.
