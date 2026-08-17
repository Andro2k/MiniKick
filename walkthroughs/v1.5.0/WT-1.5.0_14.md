# Walkthrough: Desactivación de Scroll Accidental y Botón de Incremento en QDateEdit

## Resumen del Problema y Solución

### 1. Comportamiento SpinBox de QDateEdit y Scroll Accidental
- **Problema**:
  1. `QDateEdit` heredaba las reglas de CSS de `QDateTimeEdit::up-button`, dejando un área interactiva a la derecha que aumentaba el día o el año al hacer clic.
  2. Al mover la rueda del ratón (scroll) sobre el campo de fecha o tiempo, `QAbstractSpinBox` incrementaba/decrementaba la sección seleccionada (año, mes, día o minutos) involuntariamente.

---

### 2. Solución Implementada
- **Clases `NoWheelDateEdit` y `NoWheelTimeEdit`** ([`frontend/common/utils.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/utils.py)):
  - Implementan `wheelEvent(self, event): event.ignore()`, permitiendo que el scroll del usuario desplace la ventana o formulario de forma natural sin modificar accidentalmente la fecha ni la hora.
- **Aislamiento en `theme.py`** ([`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)):
  - Se eliminó `QDateTimeEdit` de las reglas de `QSpinBox` para evitar que `QDateEdit` herede el subcontrol `::up-button` desplazado.
- **Integración en Panel de Horarios** ([`schedule_form_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_form_panel.py)):
  - Se actualizaron los campos a `NoWheelDateEdit` y `NoWheelTimeEdit`.

---

## Verificación

- Suite completa de pruebas unitarias (`uv run pytest`):
  - **57 / 57 pruebas aprobadas** (100% éxito).
