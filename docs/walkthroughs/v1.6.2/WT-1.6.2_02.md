# Walkthrough WT-1.6.2_02: Soporte Híbrido Offline y Remoto para Novedades de Versión (WhatsNewDialog)

## Resumen de la Versión
* **Versión:** `v1.6.2`
* **Tipo:** Corrección de Distribución, Resiliencia de Empaquetado PyInstaller y Sincronización Remota GitHub
* **Módulos Afectados:**
  * [`MiniKick.spec`](file:///c:/Users/TheAn/Desktop/python/Kick/MiniKick.spec)
  * [`backend/services/system/whats_new_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/whats_new_service.py)
  * [`backend/services/system/updater_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/updater_service.py)
  * [`backend/workers/updater_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/updater_worker.py)
  * [`backend/workers/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/__init__.py)
  * [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)
  * [`resources/tests/test_whats_new_system.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_whats_new_system.py)
  * [`docs/historial_crashes_y_errores.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/historial_crashes_y_errores.md)

---

## Novedades

* **Consulta Asíncrona de Releases en GitHub (`WhatsNewWorker`)**:
  Se implementó el worker asíncrono [`WhatsNewWorker`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/updater_worker.py) basado en `QThread`. Si la aplicación se ejecuta en un entorno donde no existan notas de versión locales, consulta de forma reactiva la release correspondiente en la API oficial de GitHub (`https://api.github.com/repos/Andro2k/MiniKick/releases/tags/v{version}` o `/latest`), procesa la tabla de novedades e inyecta dinámicamente las tarjetas destacadas e insignias reactivas en el sidebar sin congelar la interfaz de usuario.
* **Consulta por Tag en `GithubUpdateProvider`**:
  Se incorporaron los métodos `fetch_release_by_tag` y `fetch_release_for_version` en [`GithubUpdateProvider`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/updater_service.py), permitiendo recuperar los metadatos y cuerpo Markdown de cualquier versión etiquetada en el repositorio remoto.

---

## Mejoras

* **Caché $\mathcal{O}(1)$ de Novedades en SQLite (`whats_new_state`)**:
  Se extendió la persistencia atómica en [`WhatsNewService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/whats_new_service.py) para almacenar el catálogo de `highlights` dentro del objeto JSON `whats_new_state`. Tras la primera lectura exitosa (local o remota), los inicios subsiguientes acceden a las novedades en tiempo constante $\mathcal{O}(1)$ sin latencia de red ni reanálisis sintáctico.
* **Desacoplamiento de E/S y Función Pura de Parseo (`parse_release_notes_content`)**:
  Se aisló el análisis sintáctico de la tabla Markdown en [`parse_release_notes_content`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/whats_new_service.py). Esta función pura procesa en una sola pasada $\mathcal{O}(N)$ tanto el texto leído de archivos `.md` del disco como el cuerpo retornado por peticiones HTTP a GitHub.
* **Resolución Resiliente de Rutas Multi-Entorno (`_resolve_release_notes_path`)**:
  Se reemplazó la ruta estática por un resolvedor determinista que audita en cascada: ruta inyectada (`base_dir`), directorio temporal de extracción de PyInstaller (`sys._MEIPASS`), directorio base del ejecutable (`sys.executable`), subdirectorio `_internal` y raíz del repositorio en modo desarrollo.

---

## Correcciones

* **Inclusión de Notas de Versión en el Bundle de PyInstaller (`MiniKick.spec`)**:
  Se solucionó la omisión en [`MiniKick.spec`](file:///c:/Users/TheAn/Desktop/python/Kick/MiniKick.spec) incorporando `('docs/walkthroughs', 'docs/walkthroughs')` en `all_datas`. Al generar el distribuible (`MiniKick.exe`), las notas de versión viajan compiladas dentro del paquete, garantizando que [`WhatsNewDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/whats_new_dialog.py) se proyecte de inmediato de forma 100% offline en el primer arranque.
* **Activación Reactiva del Modal Tras Consulta Remota**:
  En [`MainWindowCore`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py), se corrigió el flujo por el cual una lista vacía de novedades descartaba silenciosamente el modal. Al concluir la descarga en segundo plano desde GitHub, se dispara `_on_remote_whats_new_fetched`, se iluminan las insignias de la barra lateral y se presenta el diálogo modal al streamer.
