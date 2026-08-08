# Walkthrough - Solución TypeError en argparse ('100%% en crudo')

## Resumen de Cambios Completados

Se corrigió la excepción `TypeError: must be real number, not dict` ocurrida al usar la bandera `--raw` en [test_kick_websocket_live.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_kick_websocket_live.py).

### Causa y Solución

1. **Causa del Error en Python 3.14**:
   - `argparse` procesa la sintaxis de formateo `%` dentro del parámetro `help="..."`. El texto `100% en` era interpretado como `% e` (especificador de número real), lanzando `TypeError` al recibir el diccionario de parámetros del parser.

2. **Solución Aplicada**:
   - Se escapó el signo de porcentaje cambiando `100%` a `100%%` en la cadena de ayuda de `add_argument("--raw", ...)`.

---

## Verificación

- **Ejecución `--help`**: `uv run python tests/test_kick_websocket_live.py --help` -> **Éxito (0 errores)**.
- **Ejecución `--raw`**: `uv run python tests/test_kick_websocket_live.py --channel theandro2k --raw` -> **Ejecución limpia y sin errores de parseo**.
- **Pytest**: `uv run pytest tests/` -> **11/11 pasadas (100%)**.
