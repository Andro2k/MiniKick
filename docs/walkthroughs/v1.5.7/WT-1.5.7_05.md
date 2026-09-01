# Walkthrough: Telemetría y Registro Exhaustivo de Inicio (Startup Logs)

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_05.md`  
**Módulos Modificados:**
- [`main.py`](file:///c:/Users/TheAn/Desktop/python/Kick/main.py)
- [`backend/core/app_container_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_container_core.py)
- [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)

---

## 1. Resumen de Cambios

1. **Telemetría de Bootstrap en `main.py`**:
   - Registro de AppUserModelID en Windows.
   - Conteo de fuentes cargadas desde `assets/fonts/`.
   - Estado de la verificación de bloqueo de instancia única por socket (`port 45678`).
   - Inicialización del gestor de actualizaciones (`UpdateManager`) y de la ventana principal (`MainWindowCore`).
   - Entrada explícita al bucle de eventos de Qt (`app.exec()`).

2. **Diagnóstico del Contenedor de Dependencias en `app_container_core.py`**:
   - Registro cronológico de inicialización de los almacenes SQLite y servicios base (`BackupService`, `SettingsService`, `AvatarService`, `WidgetService`, `ScheduleService`).
   - Registro de la creación de los gestores de autenticación OAuth (Kick y Twitch) y servicios de TTS / Overlay.

3. **Trazado Detallado del Ciclo de Vida en `main_window_core.py`**:
   - Registro en `__init__` de la creación de la UI, sidebar, tray del sistema, controladores y conexión de señales.
   - En `_load_settings_into_ui`, trazado explícito de la hidratación de datos iniciales en los controladores.
   - En `autostart`, registro de qué integraciones se disparan (Kick, Twitch, YouTube, TikTok) con sus parámetros o nombres de canal de destino.

---

## 2. Verificación y Resultados

```powershell
uv run pytest resources/tests/unit/core/
```
- **9/9 tests aprobados (100% PASSED)**.
- Todos los módulos utilizan loggers dedicados respetando las políticas de arquitectura y clean logging.
