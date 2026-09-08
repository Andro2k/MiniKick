# Walkthrough WT-1.5.8_29: Estandarización de Geometría en QSS (Theme) y Eliminación de .setFixed Redundantes

## 1. Contexto y Objetivos
Se identificó que el colapso visual del `ClearableLineEdit` (salto de altura entre el estado vacío y el estado con texto) provenía de la ausencia de padding vertical en `QFrame[role="search_bar"] QLineEdit` en `frontend/common/theme.py`.
Adicionalmente, se auditaron y eliminaron dimensiones fijas (`.setFixedHeight()`) quemadas en código Python en componentes y diálogos para centralizar el control de diseño en la hoja de estilos global (`theme.py`), respetando el principio de **Separación de Responsabilidades (SoR)**.

---

## 2. Cambios Implementados

### A. Hoja de Estilos Centralizada ([theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py))
- **`QFrame[role="search_bar"]`**:
  - Incorporado `min-height: 34px;` para garantizar que la barra de búsqueda y campos con botón de limpieza mantengan exactamente la misma altura ya sea que el botón esté visible u oculto.
  - Asegurado `padding: {PADDING_INPUT};` en `QFrame[role="search_bar"] QLineEdit` para un espaciado vertical armónico.
- **`QFrame[role="divider"]`**:
  - Actualizado con `min-height: 1px; max-height: 1px; border: none;`, controlando el grosor y color del divisor mediante QSS puro.

### B. Widgets Limpiados
- **[blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)**:
  - En `ModernDivider`, se eliminó la llamada imperativa `self.setFixedHeight(2.5)` permitiendo que el divisor sea gobernado limpiamente por el token de `theme.py`.

### C. Diálogos Estandarizados
- **[bug_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/bug_report_dialog.py)**:
  - Eliminado `self.txt_username.setFixedHeight(34)`.
  - Migrados `btn_cancel` y `btn_send` a `ModernButton` (`role="action_outlined"` y `role="action_accent"`), removiendo `setFixedHeight(38)` y unificando el estilo con el resto de modales modernos.
- **[crash_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/crash_report_dialog.py)**:
  - Eliminado `self.txt_contact.setFixedHeight(34)`.
  - Migrados `btn_copy_tb` y `btn_send` a `ModernButton` (`role="action_outlined"` con icono y `role="action_danger_border"`), removiendo `setFixedHeight(38)` y `setFixedHeight(26)`.

---

## 3. Verificación y Pruebas

### Pruebas Automatizadas
Se ejecutó la suite completa de pruebas unitarias y de integración:
```bash
uv run pytest
```
**Resultado:** `288 passed in 50.24s` (100% de pruebas pasando).

Pruebas específicas añadidas:
- `test_bug_and_crash_report_dialog_styling`: Valida que los diálogos instancien `ModernButton` y no restrinjan artificialmente la altura de los campos de texto.
- `test_modern_divider`: Valida que `ModernDivider` utilice la regla QSS sin llamadas forzadas de altura en Python.
