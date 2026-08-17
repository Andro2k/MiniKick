# Walkthrough: Corrección de QDateEdit y Estilización de QCalendarWidget

## Resumen de los Problemas y Soluciones

### 1. Botones Fantasma de `QDateEdit` ([`theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py))
- **Problema**: `QDateEdit` hereda internamente de `QDateTimeEdit` / `QAbstractSpinBox`. Los estilos de subcontroles para `QDateTimeEdit::up-button` y `QDateTimeEdit::down-button` dejaban áreas interactivas invisibles en la parte derecha del `QDateEdit`, provocando que al hacer clic en espacios vacíos se incrementara o modificara la fecha en vez de abrir el calendario emergente.
- **Solución**: Se anularon explícitamente `QDateEdit::up-button` y `QDateEdit::down-button` con dimensiones `0px`, sin borde y sin fondo en [`theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py), dejando únicamente operativo el subcontrol `::drop-down`.

---

### 2. Estilización Visual del `QCalendarWidget` ([`theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) & [`schedule_form_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_form_panel.py))
- **Problemas corregidos**:
  1. **Flechas de navegación oscuras/invisibles**: Los SVG `chevron-left.svg` y `chevron-right.svg` utilizaban `stroke="currentColor"`, lo que provocaba que Qt los renderizara en color negro en lugar de blanco. Se actualizaron con `stroke="#FFFFFF"`.
  2. **Flecha/indicador duplicado bajo el mes**: El `QToolButton` del mes mostraba un `menu-indicator` nativo desalineado. Se ocultó mediante `QCalendarWidget QToolButton::menu-indicator { image: none; width: 0px; }`.
  3. **Texto rojo en fines de semana**: Qt colorea por defecto los fines de semana ("sáb.", "dom.", 5, 6, 12...) en color rojo brillante. Se restableció el formato de caracteres de sábado y domingo en `schedule_form_panel.py` con el color neutral de la paleta (`COLOR_NEUTRAL_200`).
  4. **Encabezado vertical**: Se desactivó la columna vertical innecesaria (`NoVerticalHeader`).

---

## Verificación

- Suite completa de pruebas unitarias (`uv run pytest`):
  - **57 / 57 pruebas aprobadas** (100% éxito).
