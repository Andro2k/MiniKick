# Walkthrough - Diferenciación de Notificaciones Toast al Activar/Desactivar Alertas (v1.5.8_41)

## Resumen de Cambios

Se diferenció la notificación tipo *Toast* emitida cuando un usuario activa o desactiva una alerta (mediante el switch de la barra lateral o de la tarjeta de alerta) respecto al guardado convencional de la configuración.

### 1. Claves de Internacionalización (i18n)
Se añadieron las siguientes claves en [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) bajo el grupo `alerts.status`:
- `enabled_title`: "Alerta Activada" / "Alert Enabled"
- `enabled_msg`: "La alerta de '{event}' ha sido activada." / "The '{event}' alert has been enabled."
- `disabled_title`: "Alerta Desactivada" / "Alert Disabled"
- `disabled_msg`: "La alerta de '{event}' ha sido desactivada." / "The '{event}' alert has been disabled."

### 2. Controlador de Alertas (`AlertsController`)
En [alerts_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/alerts_controller.py):
- Se incorporó el seguimiento del estado anterior de activación en `self._previous_enabled` con complejidad $\mathcal{O}(1)$ de consulta y actualización.
- En `load_initial_data()`, se registran los estados iniciales cargados desde el servicio o base de datos.
- En `_handle_config_changed(config)`:
  - Se detecta si `enabled` cambió respecto a `_previous_enabled`.
  - Si cambió a `True`, se emite un toast de éxito (`state="success"`, título `"Alerta Activada"` y mensaje con el nombre traducido del evento).
  - Si cambió a `False`, se emite un toast de advertencia (`state="warning"`, título `"Alerta Desactivada"` y mensaje con el nombre traducido del evento).
  - Si no cambió `enabled` (ej. guardado de colores, tipografía, plantilla o duración), se mantiene el toast estándar `"Alerta Guardada"`.

### 3. Pruebas Unitarias
En [test_alerts_ui.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_alerts_ui.py):
- Se añadió la prueba `test_alerts_controller_toggle_toast_differentiation` que valida la emisión de los títulos, mensajes y estados correspondientes ante eventos de activación, desactivación y guardado general.

## Verificación

```powershell
uv run pytest resources/tests/unit/ui/test_alerts_ui.py resources/tests/unit/ui/test_i18n_integrity.py
```
Resultado: **14 passed in 1.37s** (100% de pruebas pasando satisfactoriamente).
