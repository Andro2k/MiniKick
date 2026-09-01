# Walkthrough: Registro con Fecha/Hora y Visualización de Crashes en la App

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_09.md`  
**Módulos Modificados:**
- [`backend/core/app_logger_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_logger_core.py)
- [`main.py`](file:///c:/Users/TheAn/Desktop/python/Kick/main.py)
- [`backend/services/system/log_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/log_service.py)
- [`backend/controllers/log_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/log_controller.py)
- [`frontend/views/log_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/log_view.py)
- [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
- [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)
- [`resources/tests/unit/core/test_logging.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/core/test_logging.py)

---

## 1. Resumen de Cambios

### A. Marcas de Tiempo en `minikick_crash.log`
1. **Encabezado de Sesión**:
   Al inicializar la aplicación en `app_logger_core.py`, se registra un encabezado con fecha/hora indicando el arranque de la sesión y la activación de `faulthandler`:
   ```text
   ================================================================================
   [2026-08-31 22:35:00] [BOOTSTRAP] --- MiniKick Session Started (Faulthandler active) ---
   ================================================================================
   ```
2. **Caídas de Hilos y Globales**:
   - `_threading_excepthook` registra inmediatamente la traza con `[YYYY-MM-DD HH:MM:SS] [THREAD_CRASH]`.
   - `global_crash_handler` (`main.py`) registra la traza no controlada con `[YYYY-MM-DD HH:MM:SS] [FATAL_CRASH]`.

### B. Visualizador y Botón en la App (Developer -> Logs)
1. **Botón "Ver Fallos" (`btn_view_crashes`)**:
   - Integrado en `LogControlsPanel` (`log_view.py`) con icono `bomb.svg` y color de alerta.
   - Cuenta con tooltip internacionalizado.
2. **Carga y Agrupación Inteligente**:
   - `LogService.parse_log_file` ahora agrupa trazas multilínea asociadas a un mismo crash en una sola entrada expandible en la tabla.
   - `LogController.handle_view_crashes_requested` carga el archivo, cambia a la vista histórica y emite un toast informativo indicando cuántos fallos se encontraron.
   - Si no hay fallos o el archivo está vacío, notifica al usuario sin bloquear la interfaz.

---

## 2. Verificación y Resultados

```powershell
uv run pytest resources/tests/unit/ -q --tb=short
```
- **145/145 tests unitarios aprobados al 100%**.
- 100% de paridad en claves i18n (`locales/es.json` y `locales/en.json`).
- Cero advertencias ni iconos faltantes.
