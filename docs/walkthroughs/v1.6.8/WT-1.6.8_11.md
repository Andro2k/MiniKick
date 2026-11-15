# Walkthrough Técnico — MiniKick v1.6.8 (Paso 11)

`bootstrap/` y `resources/` adoptan la convención de nombres del backend y el frontend, y el auditor de ubicación pasa a exigirla también en esas carpetas.

---

## Novedades

- **`bootstrap/`:** los módulos de arranque con funciones pasan a `*_setup` y el resto se nombra por su clase: `environment` → `environment_setup`, `config` → `config_setup`, `crash` → `crash_handler` y `services` → `startup_services`. `application`, `qt_setup` y `translator` conservan su nombre.
- **`resources/tests/`:** seis pruebas toman el nombre del módulo que prueban, que cambió en los pasos 08 y 09: `test_tts_speech_text` → `test_speech_utils`, `test_tiktok_provider` → `test_tiktok_chat_provider`, `test_audio_devices` → `test_audio_devices_provider`, `test_gui_bridge` → `test_gui_bridge_utils`, `test_config_bootstrap` → `test_config_setup` y `test_main_window_support` → `test_main_window_core`.
- **Docstrings en español** en los 69 módulos que no los tenían: 7 de `bootstrap/`, 23 de `resources/tools/` y 39 de `resources/tests/`.
- **Auditor:** `NAMING_RULES` suma tres carpetas: `bootstrap/` (`*_setup.py`, `*_handler.py`), `resources/tools/` (`*_auditor`, `*_manager`, `*_probe`, `*_tool`, `*_suite`, `*_profiler`) y `resources/tests/` (`test_*.py`).

## Mejoras

- Los imports (`bootstrap.config`, `bootstrap.services`, etc.), el mapa `_EXPORTS` de `bootstrap/__init__.py` y el diagrama y la tabla de `bootstrap/README.md` se actualizaron con el nuevo nombre de cada archivo.
- **Excepciones explícitas:** `application`, `startup_services` y `translator` en `bootstrap/`; `_project_sources` y `generate_screenshots` en `resources/tools/`; `conftest` y `_webhook_helpers` en `resources/tests/`.
- `resources/tests/test_file_naming_auditor.py` cubre las tres carpetas nuevas con archivos válidos, inválidos y excepciones.
- **Verificación:** se importan los 310 módulos de `backend`, `frontend` y `bootstrap` con Qt (offscreen) sin fallos, `resources/tests` da 290 aprobadas, `project_quality_suite.py --quick` da 14/14 y el auditor de ubicación sale limpio.

## Limitaciones conocidas

- Los nombres de logger y los walkthroughs anteriores conservan los nombres antiguos.
- Las descripciones de las herramientas de `resources/tools/` y de las pruebas se redactaron a partir de sus nombres y de los nombres de sus pruebas, sin una lectura completa de cada archivo.
- `generate_screenshots.py` mantiene un nombre de verbo en lugar de un sufijo de rol, por ser el comando que se invoca desde la línea de comandos.
- `scripts/` solo contiene `install.ps1` y no se tocó.
