# Walkthrough v1.6.0_01: Cobertura Completa de Pseudo-Estados QSS y Estandarización de Foco

Se ha completado una revisión e implementación integral de los pseudo-estados de Qt Style Sheets (QSS) en el sistema de temas y componentes de interfaz de usuario de MiniKick.

---

## 1. Novedades
- **Soporte Completo de `QRadioButton`**: Se implementó el conjunto completo de estilos e indicadores para `QRadioButton` en el tema global ([theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)), incluyendo estados `:hover`, `:focus`, `:pressed`, `:checked`, `:disabled` y la variante combinada `:checked:disabled`. Se integró el nuevo activo [radio-dot.svg](file:///c:/Users/TheAn/Desktop/python/Kick/assets/icons/radio-dot.svg) para el indicador activo.
- **Soporte de Casillas Indeterminadas (`QCheckBox::indicator:indeterminate`)**: Añadido soporte visual oficial para el estado parcial (`Qt.CheckState.PartiallyChecked`) tanto en modo normal, hover, pressed como disabled mediante el activo [minus.svg](file:///c:/Users/TheAn/Desktop/python/Kick/assets/icons/minus.svg).
- **Estilo para Botón por Defecto (`QPushButton:default`)**: Incorporado el borde distintivo verde para acciones predeterminadas en modales y diálogos.

---

## 2. Mejoras
- **Estandarización de Estados en Controles de Entrada**:
  - Se añadieron selectores `:read-only` y `:read-only:focus` a `QLineEdit`, `QTextEdit`, `QPlainTextEdit`, `QSpinBox` y `QDateEdit`, garantizando que los campos no editables tengan una apariencia visual protegida sin bordes interactivos de edición.
  - Se agregó `:hover` sutil en campos de texto para feedback preliminar de interacción.
- **Feedback Táctil en Botones Utilitarios y Navegación**:
  - Incorporado el estado `:pressed` en botones `btn_ghost`, `btn_icon_sm`, `btn_dismiss` y `nav_button`.
  - Añadidas las variantes compuestas `:checked:hover` y `:checked:pressed` para `nav_button` y `segmented_item`.
  - Incorporado el estado `:disabled` en `btn_icon_sm`, `btn_dismiss`, `nav_button` y `segmented_item`.
- **Interactividad en Tablas y Encabezados**:
  - `QHeaderView::section` ahora cuenta con `:hover` y `:pressed` para tablas con ordenamiento de columnas por clic.
  - `QTableWidget::item` cuenta con `:hover:!selected` y estado `:disabled`.
- **Estados en Deslizadores (`QSlider`)**:
  - Añadido `:hover` y `:pressed` para el tirador (`handle`) y soporte completo de `:disabled` en `groove`, `sub-page` y `handle`.
- **Estados en Desplegables (`QComboBox`)**:
  - Compatibilidad nativa con el pseudo-estado `:on` cuando la lista emergente está abierta, y atenuación de flecha en `:disabled`.
- **Pestañas (`QTabBar`) y Barras de Progreso (`QProgressBar`)**:
  - `QTabBar::tab` ahora maneja `:disabled` y `:pressed:!selected`.
  - `QProgressBar` ahora refleja estados deshabilitados `:disabled`.

---

## 3. Correcciones
- **Corrección de Icono Central Fantasma en `QComboBox`**:
  - **Problema**: En [theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) se había incluido la combinación de selector `QComboBox:on::down-arrow`. En la especificación QSS de Qt, los pseudo-estados no pueden preceder a los sub-controles (`::down-arrow`). Al fallar el parseo del sub-control, Qt interpretaba la regla como `QComboBox:on { image: url(...) }`, aplicando la imagen directamente al widget principal y dibujando el chevron hacia arriba centrado en el medio de los desplegables.
  - **Solución**: Se eliminó el selector inválido `QComboBox:on::down-arrow`, manteniendo la sintaxis estándar y soportada por Qt: `QComboBox::down-arrow:on, QComboBox[state="active"]::down-arrow`.
- **Reemplazo del Selector Inválido `:focus-within` en QSS**:
  - **Problema**: `QFrame[role="search_bar"]:focus-within` no es soportado por el motor de estilos de Qt, provocando que los contenedores de búsqueda nunca resaltaran cuando su campo de texto interno ganaba foco.
  - **Solución**: Se reemplazó el selector en [theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) por `QFrame[role="search_bar"]:focus, QFrame[role="search_bar"][state="focused"]` y se instaló un `eventFilter` en los componentes compuestos ([search_bar.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/search_bar.py), [clearable_line_edit.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/clearable_line_edit.py) y [category_search.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/category_search.py)) para alternar reactivamente la propiedad dinámica `state="focused"` con repulido (`unpolish` / `polish`) en tiempo $\mathcal{O}(1)$.
