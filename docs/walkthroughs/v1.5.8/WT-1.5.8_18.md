# Walkthrough: WT-1.5.8_18 - Compatibilidad Multiplataforma (Linux/Ubuntu) y Corrección de Inicio en `GlobalMediaWorker`

## Resumen Ejecutivo

Al ejecutar `uv run main.py` en Ubuntu 26 / Linux, la aplicación fallaba inmediatamente en tiempo de arranque con la siguiente traza:
```text
File "/home/andro/Documentos/MiniKick/backend/workers/global_media_worker.py", line 30, in <module>
    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
               ^^^^^^^^^^^^^^^^^^
AttributeError: module 'ctypes' has no attribute 'WINFUNCTYPE'. Did you mean: 'CFUNCTYPE'?
```

En este walkthrough se abordó y resolvió de forma integral la causa raíz, implementando una barrera estricta de aislamiento de plataforma que garantiza que MiniKick pueda inicializarse y operar con total normalidad en Linux/macOS sin comprometer ninguna de las funcionalidades nativas en Windows.

---

## 1. Análisis de Causa Raíz y Arquitectura

### Diagnóstico
1. **Convenciones de Llamada Win32 (`WINFUNCTYPE`)**:
   - La función `ctypes.WINFUNCTYPE` genera punteros a funciones con convención de llamada `stdcall` (específica de la API de Windows en arquitecturas x86/x64).
   - En sistemas POSIX (Linux/Ubuntu, macOS), Python compila `ctypes` únicamente con `CFUNCTYPE` (`cdecl`), por lo que el atributo `WINFUNCTYPE` no existe en el módulo `ctypes`.
2. **Evaluación Incondicional al Importar**:
   - En [global_media_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/global_media_worker.py), las estructuras `ctypes.wintypes`, `KBDLLHOOKSTRUCT` y `HOOKPROC = ctypes.WINFUNCTYPE(...)` se evaluaban a nivel de módulo (top-level).
   - Debido a que `backend.workers` es importado de forma transitiva durante la inicialización de controladores (`rewards_controller` -> `YouTubeMusicProvider` -> `YouTubeResolveWorker`), el error detenía la ejecución del programa completo antes de crear la ventana principal (`MainWindowCore`).
3. **Puntos Adicionales de Fricción Multiplataforma**:
   - **Rutas Temporales**: En [updater_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/updater_service.py), se usaba `os.getenv('TEMP')` directamente sin fallback. En Linux, la variable `TEMP` no existe de forma predeterminada (`None`), lo que provocaba `TypeError` al llamar a `os.path.join()`.
   - **Silenciamiento de Logging FFmpeg**: En [app_logger_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_logger_core.py), la función `_silence_ffmpeg_native_logging()` solo buscaba archivos terminados en `.dll`. En Linux, las librerías nativas poseen extensión `.so`.

---

## 2. Cambios Implementados

### A. Barrera de Plataforma en `GlobalMediaWorker`
- **Archivo**: [global_media_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/global_media_worker.py)
- **Aislamiento Condicional**:
  ```python
  if sys.platform == "win32":
      import ctypes.wintypes

      class KBDLLHOOKSTRUCT(ctypes.Structure):
          _fields_ = [
              ("vkCode", ctypes.wintypes.DWORD),
              ("scanCode", ctypes.wintypes.DWORD),
              ("flags", ctypes.wintypes.DWORD),
              ("time", ctypes.wintypes.DWORD),
              ("dwExtraInfo", ctypes.c_size_t)
          ]

      HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
  else:
      KBDLLHOOKSTRUCT = None
      HOOKPROC = None
  ```
- **Ciclo de Vida Neutro en Linux**:
  En `run()`, si `sys.platform != "win32"`, el worker registra un log a nivel de depuración y retorna inmediatamente sin intentar acceder a `ctypes.windll`. La interfaz de señales (`play_pause_pressed`, `skip_pressed`, `stop_pressed`) se preserva intacta como un componente no-op.

### B. Fallback Seguro de Directorio Temporal
- **Archivo**: [updater_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/updater_service.py)
- Se sustituyó `os.getenv('TEMP')` por `os.getenv('TEMP') or tempfile.gettempdir()`, asegurando que tanto en Windows (`%TEMP%`) como en Linux (`/tmp`) se obtenga una ruta válida sin excepciones de tipo `TypeError`.

### C. Detección de Librerías Nativas de FFmpeg en Linux
- **Archivo**: [app_logger_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_logger_core.py)
- Se amplió la búsqueda en `_silence_ffmpeg_native_logging()` para detectar extensiones `.so`, `.dylib` además de `.dll`:
  ```python
  if 'avutil' in f and (f.endswith('.dll') or f.endswith('.so') or '.so.' in f or f.endswith('.dylib')):
      dll_path = os.path.join(root, f)
      avutil = ctypes.CDLL(dll_path)
      avutil.av_log_set_level(16)
      return
  ```

---

## 3. Pruebas y Verificación

### Pruebas Automatizadas
1. **Prueba de Reproducción en Entorno Simulado**:
   - Se simuló el entorno Linux eliminando `ctypes.WINFUNCTYPE` y configurando `sys.platform = "linux"`.
   - Se verificó que `from backend.core import ...` y el bootstrap completo de `main.py` carguen exitosamente sin excepciones.
2. **Suite de Pruebas Unitarias de `test_global_media_worker.py`**:
   - Se adaptó la prueba de ciclo de vida `test_global_media_worker_start_stop_lifecycle` para respetar el comportamiento según la plataforma anfitriona.
   - Se añadió `test_global_media_worker_non_windows_simulation` y `test_global_media_worker_import_on_non_windows` para validar la instanciación y recarga del módulo bajo simulación de Linux.
   - Resultado: **6 pruebas pasadas en 0.16s**.
3. **Suite Completa de Pruebas**:
   - Se ejecutó `uv run pytest resources/tests/unit/`:
   - Resultado: **251 pruebas unitarias superadas exitosamente (100% pasando)**.

---

## 4. Principios Arquitectónicos y Eficiencia Big-O

- **Separation of Responsibilities & Dependency Inversion**: Las llamadas de bajo nivel específicas del sistema operativo se mantienen estrictamente encapsuladas tras una barrera de plataforma, impidiendo que dependencias propietarias de Win32 afecten la portabilidad de los servicios de negocio o de la interfaz.
- **Complejidad Temporal ($\mathcal{O}(1)$)**: La comprobación `sys.platform == "win32"` se evalúa en tiempo constante en el momento de la carga de los módulos y en los métodos de arranque.
- **Complejidad Espacial ($\mathcal{O}(1)$)**: En Linux no se reservan estructuras ctypes ni manejadores de hilos Win32.
- **Strict i18n & Clean Code**: Se respetan las convenciones de guard clauses tempranas y cero cadenas de texto de interfaz hardcodeadas.
