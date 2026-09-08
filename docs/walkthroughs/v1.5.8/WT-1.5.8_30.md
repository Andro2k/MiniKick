# Walkthrough WT-1.5.8_30: Estandarización de Dimensiones en frontend/widgets y Vistas hacia Theme QSS

## 1. Contexto y Objetivos
Se realizó una auditoría profunda de dimensiones hardcodeadas (`.setFixedHeight()`, `.setFixedWidth()`, `.setFixedSize()`, `.setMinimumWidth()`) en los componentes de `frontend/widgets/` y en las vistas que los consumen (`alerts_view.py` y `dashboard_view.py`). El objetivo fue migrar la definición de geometría hacia tokens y selectores centralizados en `frontend/common/theme.py`, preservando el principio de **Separación de Responsabilidades (SoR)** y permitiendo que los layouts de Qt se adapten de forma responsiva y fluida ante cambios de fuentes y DPI.

---

## 2. Cambios Implementados

### A. Hoja de Estilos Centralizada ([theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py))
- **`QFrame[role="badge"]`**: Añadido `min-height: 20px; max-height: 22px;` para estandarizar la altura de todos los badges de la aplicación.
- **`QLabel[role="badge_kick"]` y `QLabel[role="badge_twitch"]`**: Añadido `min-height: 18px; max-height: 22px;`.
- **`QComboBox`**: Incorporado `min-width: 120px;` en el selector base para garantizar ancho suficiente sin necesidad de llamadas manuales en Python.
- **`QPushButton[role="btn_icon_sm"]`**: Creado rol para botones icono cuadrados pequeños (`min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px;`).
- **`QPushButton[role="btn_cell_action"]`**: Creado rol para botones de acción dentro de celdas de tabla (24x24 px).
- **`QPushButton[role="color_swatch"]` y `QPushButton[role="color_preset"]`**: Creados roles para swatches y presets del selector de color (32x32 y 22x22 px).

### B. Widgets Limpiados
- **[blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)**:
  - En `create_badge()`, se eliminó `tag.setFixedHeight(22)`, aprovechando la regla de QSS.
  - En `ExpandableCard`, se reemplazó `btn_expand.setFixedSize(30, 30)` por la asignación de rol `role="btn_icon_sm"`.
- **[category_search.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/category_search.py)**:
  - En `CategoryItemWidget`, se eliminó `self.badge.setFixedHeight(20)`.
- **[no_wheel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/no_wheel.py)**:
  - En `NoWheelComboBox`, se eliminó `self.setMinimumWidth(130)`.

### C. Vistas Limpiadas
- **[alerts_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py)**:
  - Se eliminó `setFixedHeight(32)` en `btn_tab_kick`, `btn_tab_twitch` y `btn_notice_connect`, delegando la altura al padding `PADDING_BUTTON` de `ModernButton`.
- **[dashboard_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py)**:
  - Se eliminó `setFixedHeight(30)` en `btn_tab_kick`, `btn_tab_twitch` y `btn_open_channel`.
  - Se eliminó `setFixedHeight(22)` en `lbl_platform_badge`.

---

## 3. Verificación y Resultados
- Se ejecutó la suite completa de pruebas de UI:
  ```bash
  uv run pytest resources/tests/unit/ui/
  ```
  **Resultado:** `124/124 passed in 33.04s`.
- Se verificó la integridad de los nuevos roles con:
  ```bash
  uv run pytest resources/tests/unit/ui/test_roles_integrity.py
  ```
  **Resultado:** `2/2 passed` sin roles faltantes ni discrepancias.
