# Walkthrough Técnico — MiniKick v1.6.6 (Paso 02)

Estandarización visual del frontend sobre la base del refactor de arranque del Paso 01. Se unifican el tamaño y el color de los iconos, la tipografía y el borde de los controles de entrada, los tokens de espaciado y de radio, los botones de acción de las tablas y la barra de búsqueda. Además, las herramientas y pruebas que construían la ventana principal se adaptan a la nueva inyección de dependencias. Módulos afectados: `frontend/common/theme.py`, `frontend/common/icons.py`, `frontend/widgets/*`, `frontend/components/*`, `frontend/navigation/*`, `frontend/views/*`, `frontend/dialogs/*`, `resources/tools/generate_screenshots.py` y `resources/tests/*`.

---

## Novedades

- **Botones de acción tonales para tablas**: nuevos roles `row_action`, `row_action_accent` y `row_action_danger`, con fondo del color al 14 % de opacidad, borde sutil y estados `:focus`, `:hover`, `:pressed` y `:disabled`. `TableActionCell.add_button(icon_name, role, tooltip, callback)` ya no recibe el color del icono: lo resuelve el rol.
- **`ROW_ACTION_COLORS`** en `theme.py`: única fuente de los colores de los roles tonales; genera el QSS y el color del icono.
- **Tokens nuevos**: `Size.ICON_ACTION` (28 px) para los botones de fila, `Size.Padding.PAD_MINI` y el helper `rgba(color_hex, alpha)` para transparencias en QSS.
- **Estado deshabilitado de la barra de búsqueda**: fondo y borde atenuados en el contenedor y texto en `NEUTRAL_500` en el campo.

## Mejoras

- **Iconos**:
  - `get_icon_colored` y `get_pixmap_colored` usan `NEUTRAL_050` como color por defecto (antes `NEUTRAL_400`) y 16 px como tamaño por defecto.
  - Se eliminan las llamadas redundantes a `setIconSize(QSize(16, 16))` y los argumentos de color y tamaño repetidos en más de 30 archivos del frontend.
  - `ModernButton.set_icon` y el constructor de `ModernButton` ya no reciben tamaño (`icon_size` no se usaba), y se eliminan los 15 argumentos equivalentes en vistas, diálogos y componentes.
  - Los botones de la paginación pasan de `QPushButton` con configuración manual a `ModernButton`.
  - Ambas funciones aceptan un entero como segundo argumento (tamaño) por compatibilidad con llamadas existentes.
- **Controles de entrada unificados**: `QLineEdit`, `QTextEdit`, `QPlainTextEdit`, `QSpinBox`, `QDoubleSpinBox` y `QTimeEdit` comparten con `QComboBox` la tipografía (tamaño de texto base, peso 500, color `NEUTRAL_050`) y el borde `BRD_BASE`. El foco se simplifica sin el borde superior adicional.
- **Iconos y botones internos de QSS**: flechas de combo y spinbox, indicadores de casillas y radios, indicador de menús y manija del slider pasan de 14 a 16 px; los botones de spinbox de 22 a 24 px y los de navegación del calendario de 26 a 24 px. Los iconos de chevrón, calendario y check se tiñen con `NEUTRAL_050`.
- **Tokens de espaciado**: se eliminan los tokens sin uso (`PAD_TGHT`, `PAD_CMBO`, `PAD_LIST`, `PAD_CALL`, `FLAT_MID`, `MRG_HMD`, `SEC_SCR`); `PAD_COMP`, `FLAT_MIN` y `ASYM_ONE` pasan a 2 px de padding vertical; el botón base usa `PAD_BASE` en lugar de `PAD_WIDE`. Se ajustan márgenes y espaciados en widgets, paneles y diálogos.
- **Radios**: los valores fijos de 3, 4, 7 y 9 px (sliders, barras de progreso, badges, pills de estado, radios) se reemplazan por tokens `Size.Radius`.
- **Nomenclatura**: `RED_PRESSED`, `GREEN_PRESSED`, `TIKTOK_PRESSED` y `ACCENT_PRESSED` pasan a `RED_PRESS`, `GREEN_PRESS`, `TIKTOK_PRESS` y `ACCENT_PRESS`.
- **Barra de búsqueda**: hover del botón interno con `NEUTRAL_750`, 2 px de holgura a la derecha del botón y eliminación del selector `:focus` que nunca se activaba. En `CategorySearchComboBox` se ajustan márgenes y espaciado, y la altura del popup pasa a `visible_count * 50` sin tamaños fijos por ítem.
- **Popups**: `SearchableComboBox` y el desplegable de `controls_widget` dibujan sobre un contenedor propio (`bg_frame` y `popup_window` con fondo translúcido) en lugar de estilizar el propio widget.
- **Componentes**:
  - `ModernSwitch` pasa de 44×22 a 48×24.
  - Se quitan los divisores entre botones de la paginación.
  - Los toasts miden 340 px de ancho, con altura calculada con relleno vertical simétrico e iconos de 16 px.
  - La tarjeta de plataforma ajusta espaciados y los símbolos de los estados conectando y desconectado.
- **Herramientas y pruebas**: `generate_screenshots.py` construye la ventana con `StartupServices`, `get_or_create_application` y `configure_environment` del paquete `bootstrap`; `test_window_state_persistence.py` crea la ventana con un container inyectado; se regeneran las capturas de `docs/screenshots`.

## Correcciones

- **Hover invisible en la barra de búsqueda**: el botón interno usaba en hover el mismo color que el fondo de la barra, por lo que no había retroalimentación visual.
- **Estado deshabilitado sin efecto visible en la barra de búsqueda**: la regla del campo interno forzaba el texto blanco y anulaba el estilo global de deshabilitado.
- **Orden de estados en los botones tonales**: `:focus` se declara antes de `:hover` y `:pressed`, de modo que el estado presionado se aprecia también cuando el botón tiene el foco.
- **Generador de capturas y prueba de persistencia de ventana**: ambos fallaban con `TypeError` por usar la firma anterior de `MainWindowCore`, que ahora recibe `container` y `q_log_handler`.
- **Pruebas desactualizadas**: se retiran de `test_antigravity_ui_theme.py` las referencias al token `Size.Margin.SEC_SCR` y al borde divisor de la paginación, ya eliminados del tema. Las pruebas de popups y de toast se adaptan a la nueva estructura: el contenedor translúcido del autocompletado es `popup_window`, el rol del popup de búsqueda está en `bg_frame` y el alto del toast sin mensaje es 56 px.
- **Respaldo de iconos del toast**: el valor por defecto era un texto en lugar de una tupla `(icono, color)` y fallaba con un estado desconocido; ahora usa el icono de información.
- **Filtro de eventos del gestor de toasts**: compara con el padre de Qt (`self.parent()`) en lugar del atributo de Python `main_window`, para no depender de ese atributo durante la destrucción de la ventana.
