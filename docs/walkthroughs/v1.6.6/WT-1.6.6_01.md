# Walkthrough Técnico — MiniKick v1.6.6 (Paso 01)

Reorganización completa de la ruta de inicialización. `main.py` pasa a ser un punto de entrada mínimo y la lógica de arranque se reparte en el nuevo paquete `bootstrap/` (entorno, Qt, i18n, composición de servicios, manejo de fallos y ciclo de vida). `AppContainerCore` y `MainWindowCore` dejan de crear sus propias dependencias y las reciben inyectadas, el logging se inicializa al inicio del arranque, y `MainWindowCore.__init__` y `_setup_ui` se dividen en métodos de una sola responsabilidad. Módulos afectados: `main.py`, `bootstrap/*`, `backend/config/__init__.py`, `backend/core/app_container_core.py`, `backend/core/app_logger_core.py`, `backend/utils/perf.py` y `frontend/main_window.py`.

Validado con una ejecución real (`minikick.log`, 2026-10-25): arranque completo en 2127.94 ms, conexión a Kick y Twitch, navegación por las 11 vistas, comandos de chat, controles de música, minimizado a bandeja y cierre ordenado de los 6 workers, sin advertencias ni errores registrados.

---

## Novedades

- **Paquete `bootstrap/`**: nuevo paquete con módulos de una sola responsabilidad:
  - `environment.py`: variables de entorno, saneo de `PATH`, parche de `asyncio` en Windows y `AppUserModelID`.
  - `qt_setup.py`: creación única de `QApplication` (paleta, fuentes, QSS e ícono) y `get_or_create_application()` para reutilizarla en el diálogo de fallos.
  - `translator.py`: carga de i18n con resolución del archivo `.install_lang`.
  - `services.py`: raíz de composición `StartupServices`, único lugar que conoce las implementaciones concretas (base de datos, traductor, container, guardia de instancia única y actualizador).
  - `crash.py`: clase `CrashHandler` con proveedores inyectables.
  - `application.py`: clase `Application` con el ciclo de vida del arranque.
- **`FallbackTranslator`**: traductor de respaldo que devuelve la clave cuando la base de datos o `TranslationService` fallan.
- **`backend/utils/perf.py`**: utilidades `perf_phase` (context manager) y `elapsed_ms` para el cronometrado de fases con formato `[Perf/<scope>]`.
- **`backend.config`**: nuevas exportaciones `API_KEYS_MISSING` y `TWITCH_REDIRECT_URI`.
- **`MainWindowCore`**: nuevos helpers de inicialización `_init_flags`, `_init_worker_state`, `_init_session_state`, `_bind_container`, `_init_shutdown_support` e `_init_updater`.

## Mejoras

- **`main.py`**: reducido a 11 líneas. Solo configura el entorno antes de importar PySide6, registra `CrashHandler` como `sys.excepthook` y ejecuta `Application().run()`.
- **Inversión de dependencias**:
  - `AppContainerCore` recibe `db_manager` e `i18n` en su constructor.
  - `MainWindowCore` recibe `container` y `q_log_handler` (firma nueva: `container, q_log_handler, updater_manager, app_version`) en lugar de crear el container y el logging internamente.
  - `Application` acepta un `StartupServices` inyectado.
- **Una sola instancia de base de datos e i18n en el arranque**: antes se creaban dos `DatabaseManager` y tres servicios de traducción (arranque previo, container y crash handler).
- **Resolución de `.install_lang` en el arranque**: ahora ocurre antes de mostrar el splash, por lo que este usa el idioma elegido en el instalador, igual que la ventana principal.
- **`AppContainerCore`**: `__init__` dividido en `_init_storages`, `_init_services`, `_init_auth` e `_init_overlay_and_alerts`; `shutdown()` unificado en un único bucle sobre componentes y métodos, sin cadenas de `hasattr`.
- **`backend/config/__init__.py`**: lectura de credenciales unificada con el helper `_key`, eliminando el bloque duplicado de siete nombres entre el `try` y el `except`; la URL de redirección por defecto queda centralizada en `DEFAULT_REDIRECT_URI`.
- **`setup_application_logging`**: dividida en funciones pequeñas (`_reset_handlers`, `_build_file_handler`, `_quiet_noisy_libraries`, `_redirect_std_streams`, `_enable_faulthandler`, `_install_qt_message_handler`).
- **`MainWindowCore._setup_ui`**: dividido en `_build_layout_shell`, `_create_services`, `_create_views_registry`, `_create_controllers`, `_start_background_workers` y `_assemble_layout`.
- **Tema de Qt centralizado**: paleta, fuente, QSS e ícono se aplican en un solo punto, compartido por el arranque normal y el diálogo de fallos (antes estaba duplicado).
- **Cronometrado unificado**: las mediciones de arranque pasan por `perf_phase`, con el mismo formato de log que ya mostraba la aplicación.
- **Logger de la ventana consistente**: `MainWindowCore` usa siempre el logger `minikick.core`.

## Correcciones

- **Logging tardío**: el logging se inicializaba dentro de `MainWindowCore.__init__`, por lo que los mensajes `[Perf/Bootstrap]` y las excepciones ocurridas antes de crear la ventana no llegaban a `minikick.log` ni a `minikick_crash.log`. Ahora se inicializa como primer paso de `Application.run()` y el primer registro del log es la inicialización del propio logging.
- **Fallo de i18n en el splash**: `_get_safe_i18n()` podía devolver `None` y el arranque llamaba a `.get(...)` sobre él. Ahora se usa `FallbackTranslator`.
- **Advertencia de claves de API ausentes**: el `try/except ImportError` del container nunca se disparaba porque `backend.config` siempre se importa, de modo que el aviso final era inalcanzable. Ahora se emite según `API_KEYS_MISSING`, y se elimina la bandera global `sys._api_keys_missing`.
- **`session_metrics` duplicado**: se definía dos veces en la construcción de la ventana y la segunda sobrescribía a la primera. Queda una sola definición con las cuatro claves.
- **Logger reasignado**: `self.logger` pasaba a ser el logger raíz a mitad del `__init__`, mientras `WorkerShutdownCoordinator` conservaba el anterior. Ahora ambos usan `minikick.core`.
- **Código redundante**: se eliminan el `import time` interno del `__init__`, el `getattr` defensivo sobre `twitch_auth_manager` y el `os.stat` posterior a `os.path.isdir` en el saneo de `PATH`.
