# Walkthrough Técnico — MiniKick v1.6.8 (Paso 10)

El auditor de ubicación ahora exige la convención de nombres `<tema>_<rol>.py` en backend y frontend, para que los renombres de los pasos 08 y 09 no se pierdan con el tiempo.

---

## Novedades

- `project_file_placement_auditor.py` incorpora `NAMING_RULES`: una tabla por carpeta con los sufijos permitidos. Un archivo que no los cumple se reporta como `NAMING_CONVENTION_VIOLATION`.
- La suite de calidad (`project_quality_suite.py`) ya usa esta regla sin cambios, porque invoca al mismo auditor.

## Mejoras

- **Backend:** `interfaces/` (`*_interface.py`), `models/` (`*_models.py`), `core/` (`*_core.py`), `utils/` (`*_utils.py`), `handlers/` (`*_handler.py`), `connections/` (`*_connection.py`), `providers/` (`*_provider.py`, con subcarpetas) y `services/` (`*_service.py`, con subcarpetas).
- **Frontend:** `dialogs/` (`*_dialog.py`), `navigation/` (`*_component.py`), `components/` (`*_panel`, `*_card`, `*_widget`, `*_mockup`, `*_utils`, con subcarpetas) y `window/` (`*_coordinator`, `*_presenter`, `*_handler`, `*_router`, `*_manager`, `*_tracker`, `*_cache`, `*_protocols`).
- **Excepciones explícitas** (nombres con rol propio): `chat_command_config`, `command_help_formatter`, `connection_hub`, `worker_slot`, `worker_shutdown`, `chat_pipeline`, `alerts_queue`, `overlay_manager`, `overlay_routes`, `overlay_ws_client`, `splash_screen`, `update_flow`, `main_window_core`, `view_factory` y `view_prewarmer`. Además, `services/` admite `webhook_*.py` para los archivos de webhooks que conservan el prefijo.
- **Alcance:** cada regla es por carpeta (`recursive` para incluir subcarpetas) y los `__init__.py` quedan fuera. El resto de reglas del auditor (pureza de carpetas, ubicación inversa y utilidades centralizadas) no cambia.
- **Pruebas:** `resources/tests/test_file_naming_auditor.py` comprueba que el repo cumple la convención, que se detectan archivos sin sufijo de rol (`i_tts.py`, `startup.py`, `bot_mute.py`…), que se aceptan nombres válidos, excepciones y subcarpetas, y que las carpetas no recursivas no miran sus subcarpetas.
- **Documentación:** `resources/tools/README.md` describe la nueva regla.

## Limitaciones conocidas

- No se validan `frontend/widgets/`, `frontend/common/` ni `backend/config/`: sus nombres siguen estilos propios (Qt, tokens de diseño, constantes).
- Un archivo nuevo con un rol que no está en la tabla (por ejemplo `*_adapter.py` en `services/`) se reportará hasta que se agregue el patrón o la excepción en `NAMING_RULES`.
- La regla revisa nombres, no que el rol coincida con la clase principal del archivo.
