# Walkthrough: Corrección de Setter de `tts_enabled` en ChatView

## Resumen del Problema y Solución

Al ejecutar el comando de chat `!systts off` (o `!systts on`), la aplicación arrojaba la excepción:
`AttributeError: property 'tts_enabled' of 'ChatView' object has no setter`

---

### 1. Causa Raíz
- En [`chat_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py), la propiedad `tts_enabled` solo disponía de un decorador *getter* (`@property`), pero carecía del correspondiente *setter* (`@tts_enabled.setter`), imposibilitando que [`ChatController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) sincronizara el interruptor de la interfaz al cambiar de estado mediante comandos.

---

### 2. Solución Implementada ([`chat_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py))
- Se implementaron los setters para todas las propiedades de control de chat:
  - `@tts_enabled.setter`: actualiza `chk_tts.setChecked()` bloqueando señales transitorias.
  - `@read_name_enabled.setter`: actualiza `chk_name.setChecked()`.
  - `@use_command_enabled.setter`: actualiza `chk_command.setChecked()`.
  - `@tts_command.setter`: actualiza `txt_command.setText()`.
  - `@tts_volume.setter`: actualiza `slider_vol.setValue()`.

---

## Verificación

- Se añadió `test_chat_view_property_setters` en [`test_tts_role_filtering.py`](file:///c:/Users/TheAn/Desktop/python/Kick/tests/unit/test_tts_role_filtering.py).
- Suite completa de pruebas unitarias (`uv run pytest`):
  - **55 / 55 pruebas aprobadas** (100% éxito).
