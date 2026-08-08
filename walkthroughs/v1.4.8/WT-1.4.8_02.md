# Walkthrough - Guardado Automático de Logs con Fecha en Inspector WebSocket

## Resumen de Cambios Completados

Se implementó el guardado automático en archivo de registro con fecha y hora (`ws_<channel>_YYYY-MM-DD_HH-MM-SS.log`) para el script [test_kick_websocket_live.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_kick_websocket_live.py).

### Funcionalidad Añadida

1. **Guardado Automático en `tests/logs/`**:
   - Por defecto, toda sesión ejecutada creará automáticamente un archivo de log con fecha y hora en `tests/logs/ws_<channel>_<timestamp>.log` (ej: `tests/logs/ws_rebeca-arenas_2026-08-07_23-43-15.log`).
   - Se escribe en tiempo real (`flush=True`) tanto la consola como el archivo de log.

2. **Parámetros CLI de Logs**:
   - `--no-log`: Desactiva la creación del archivo de log si solo se desea ver la salida por pantalla.
   - `--log-path <ruta>`: Permite especificar una ubicación o nombre de archivo de log personalizado.

---

## Verificación

- **CLI Help Test**: `uv run python tests/test_kick_websocket_live.py --help` -> **Éxito (0 errores)**.
- **Pytest**: `uv run pytest tests/` -> **11/11 pasadas (100%)**.
- **Guardado en Disco**: Creación automática de carpeta `tests/logs/` y rotación de nombres por fecha/hora.
