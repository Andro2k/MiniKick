# Walkthrough - Refactorización de `MainWindowCore` & `UpdateController`

## Resumen de Cambios

Se ha refactorizado la orquestación del diálogo de actualización y simplificado `frontend/core/main_window_core.py` (de 782 a ~735 líneas).

### Cambios Realizados:

1. **[update_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/update_controller.py)**:
   - Se incorporó el método `show_update_dialog(parent_window, i18n, on_restart_callback)` que encapsula la instanciación de `UpdateDialog`, la conexión de signals de progreso y descarga, el manejo de errores y la limpieza de eventos.

2. **[main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/core/main_window_core.py)**:
   - Se simplificó `handle_update_check()` reemplazando ~50 líneas de código anidado por una sola llamada limpia: `self.update_controller.show_update_dialog(self, self.i18n, on_restart_callback=self._force_quit)`.

---

## Verificación Realizada

Se ejecutaron pruebas automáticas de importación y suite completa de pruebas:

```powershell
uv run python -c "from frontend.core.main_window_core import MainWindowCore; from backend.controllers import UpdateController; print('MainWindowCore Refactor Import OK')"
uv run pytest
```
**Resultado**:
- `MainWindowCore Refactor Import OK`
- `17 passed in 0.54s`
