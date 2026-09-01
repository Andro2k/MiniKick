# Walkthrough: Arquitectura de Logging Dedicado, Telemetría de Inicio y Visor de Crashes con Faulthandler

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_02.md`  
**Módulos Involucrados:**
- `backend/core/app_logger_core.py`
- `backend/services/system/log_service.py`
- `backend/controllers/log_controller.py`
- `backend/database/` (todos los módulos de storage)
- `backend/workers/` (todos los workers)
- `backend/handlers/log_handler.py`
- `frontend/views/log_view.py`
- `frontend/dialogs/crash_report_dialog.py`

---

## 1. Resumen de Objetivos y Cambios

### A. Estandarización de Loggers Jerárquicos Dedicados
- **Principio:** Reemplazo de todas las llamadas directas `logging.info(...)` o `logging.getLogger()` por instancias jerárquicas con nombres de módulo canónicos (`minikick.controllers.*`, `minikick.services.*`, `minikick.workers.*`, `minikick.storage.*`).
- Eliminación de interferencias de librerías externas mediante el filtrado de niveles de log (`urllib3`, `cloudscraper`, `httpx`, `asyncio` a `WARNING`).

### B. Telemetría Exhaustiva de Arranque (Bootstrap Logging)
- Registro detallado en `DEBUG`/`INFO` de cada fase de inicialización:
  1. Configuración de `AppUserModelID` en Windows.
  2. Carga y verificación de fuentes tipográficas TTF/OTF.
  3. Adquisición del socket lock de instancia única.
  4. Inicialización de contenedor de dependencias `AppContainerCore`.
  5. Carga de tokens y perfiles en caché.
  6. Conexión de señales y arranque de sockets en segundo plano.

### C. Captura y Visualización Integral de Crashes Nativos (`Faulthandler`)
- Integración de `faulthandler` en `backend/core/app_logger_core.py` escribiendo directamente a `minikick_crash.log` con volcados de memoria de todos los hilos (`all_threads=True`).
- Incorporación del botón y visor **Ver Crashes** en `LogView` con soporte para analizar marcas de tiempo, trazas de excepción de Python y fallos de segmentación C/C++ (`Access Violation`).

### D. Reubicación de `log_handler.py` a la Capa Backend Handlers
- Reubicación arquitectónica de `LogEmitter`, `QLogHandler` y `StreamToLogger` desde `frontend/common/` hacia `backend/handlers/log_handler.py`, asegurando la estricta separación de responsabilidades (*SoR*).

### E. Identificación de Usuario y Versión en Logs de Reportes
- En `BugReportWorker` y `CrashReportWorker`, el archivo `.log` adjunto enviado por webhook a Discord ahora se nombra dinámicamente como `minikick_{user}_{version}.log` o `minikick_crash_{user}_{version}.log` con sanitización de caracteres especiales.
- Se inserta un encabezado al inicio del `.log` con el usuario/contacto, versión, plataforma y severidad, combinando los volcados nativos de `minikick_crash.log` con la traza de ejecución de `minikick.log`.

---

## 2. Verificación
- Pruebas unitarias de integridad de logging y reportes en `resources/tests/unit/core/test_logging.py` y `resources/tests/unit/workers/test_report_workers.py` pasando al 100%.
- Verificación del archivo de logs con formato estándar:
  `[YYYY-MM-DD HH:MM:SS] [LEVEL] Mensaje`
