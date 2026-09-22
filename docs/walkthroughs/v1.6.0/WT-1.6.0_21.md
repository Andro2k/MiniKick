# Walkthrough WT-1.6.0_21: Adaptación de Estilos de QComboBox, Segmented Control, Botones Sólidos y Chat Compacto Sin Microcortes

## Novedades
- **Armonización Visual de `QComboBox` con `action_outlined`**: Se actualizaron las reglas QSS en [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) para que `QComboBox` herede la misma paleta y comportamiento interactivo que los botones `action_outlined`:
  - Fondo `{COLOR_NEUTRAL_850}` (`#18191E`) en estado de reposo.
  - Borde `1px solid {COLOR_NEUTRAL_700}` (`#343741`) y tipografía con `font-weight: 500;`.
  - Padding de `6px 28px 6px 14px;` para alinear horizontalmente el contenido con los 14px de padding de los botones `action_outlined`.
  - Estados `:hover` (`background-color: {COLOR_SURFACE_HOVER}; border: 1px solid {COLOR_BORDER_HOVER}; color: {COLOR_PURE_WHITE};`), `:focus` (`border: 1px solid {COLOR_BORDER_FOCUS};`) y `:pressed` (`background-color: {COLOR_SURFACE_PRESSED}; border: 1px solid {COLOR_NEUTRAL_750};`) idénticos a los botones de acción.

- **Estandarización a Botones de Acción Sólidos (`action_danger_solid` y `action_accent_solid`)**:
  - Se retiraron definitivamente los estilos de degradados y bordes sutiles (`action_danger_border` y `action_accent_border`).
  - Se incorporó `action_accent_solid` en [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) con fondo verde sólido `{COLOR_GREEN_SOLID}` (`#16A34A`), hover `{COLOR_GREEN_HOVER}` (`#22C55E`), pressed `{COLOR_GREEN_PRESSED}` (`#15803D`), borde de 1px a tono, texto blanco puro y `font-weight: 600`.
  - Se actualizaron todos los botones de acción y tablas del proyecto a los roles sólidos con iconos blancos (`COLOR_WHITE`): comandos ([commands_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/commands_view.py)), recompensas ([rewards_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py)), temporizadores ([timers_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/timers_view.py) y [timers_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/timers_dialog.py)), horarios ([schedule_table_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_table_panel.py)), ajustes TTS ([tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py)), voces piper ([piper_voice_item.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/piper_voice_item.py)), dropzone de imágenes ([image_dropzone.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/image_dropzone.py)), diálogo de confirmación ([base_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py)), reporte de crashes ([crash_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/crash_report_dialog.py)) y resolución automática de colores de iconos en [controls_widget.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls_widget.py).

- **Renderizado de Cápsulas de Chat en Texto Puro Optimizado (`frontend/components/chat/chat_display.py`)**:
  - Se eliminó la generación dinámica de mapas de bits (`QPixmap` / `QPainter`), migrando a una estructura HTML de texto puro de alto rendimiento ($\mathcal{O}(1)$ real sin consumo de recursos gráficos ni lag en chats de alto flujo).
  - **Alineación a Ras Sin Microcortes**: Al eliminar los espacios `&nbsp;` internos que causaban desfases métricos en la fuente `GoogleSansCode Nerd Font`, los glifos curvados (`\ue0b6` y `\ue0b4`) encajan de forma perfectamente continua sobre el fondo `#29315A`.
  - **Copia al Portapapeles Limpia (`ChatConsoleEdit`)**: Se implementó una subclase personalizada de `QTextEdit` con `createMimeDataFromSelection`, permitiendo copiar mensajes al portapapeles en texto legible y natural (` 21:35:35  Streamer TheAndro2K !sr birds`) sin caracteres de reemplazo de objeto (`￼`) ni glifos privados corruptos.
  - **Orden y Espaciado Compacto**: Cápsula de plataforma y hora (`Icono + Hora`), rol y usuario, con espaciado inter-cápsula estrecho (`" "`) para maximizar la amplitud del mensaje.

- **Estandarización y Unificación de `LogView` en `ModernTableCard` con Cabecera Integrada y Reflow Responsivo**:
  - Se retiró el panel/card superior independiente `LogControlsPanel` en [`frontend/views/logs_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/logs_view.py), unificando la vista bajo el estándar universal de tarjetas de tabla `ModernTableCard`.
  - Se integraron todos los controles dentro de la cabecera del propio card:
    - **Fila Superior**: Título reactivo ("Registros de Eventos" con conteo dinámico), barra de búsqueda integrada (`UnifiedSearchBar`) y selector de rango temporal (`NoWheelComboBox`).
    - **Fila Secundaria de Acciones**: Los 6 botones de control (`Carpeta`, `Cargar Historial`, `Ocultar/Ver Logs`, `Vista en Vivo`, `Limpiar`, `Reportar Bug`) migrados como botones compactos contorneados (`action_outlined` con icono de 14px).
  - **Reflow Responsivo Dinámico (`reflow_header_actions`)**: Implementado en [`frontend/widgets/table_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py) con complejidad $\mathcal{O}(k)$ (donde $k$ es el número de botones visibles). Al reducir el ancho de la ventana (ej. 950px, 620px, 450px), los botones se reacomodan fluidamente en columnas automáticas (`cols = max(1, min(len(visible), content_width // 115))`), garantizando adaptabilidad completa sin desbordes.
  - **Soporte de Footer y Estado Vacío en `ModernTableCard`**: Se implementó `set_footer_widget` para anclar la barra de paginación con divisor continuo y `setup_empty_state` con soporte para icono personalizado (`eye-filled.svg`) para el estado de consola en pausa ("Ver logs en vivo").

- **Conteo Dinámico de Elementos Filtrados frente al Total en Tablas (`ModernTableCard`)**:
  - Se actualizó el método `set_title_count` en [`frontend/widgets/table_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py) para soportar el conteo dual `count` y `total_count`.
  - Cuando no hay filtros activos (o `count == total_count`), se mantiene el total estándar: `Título (total)` (ej. `Comandos Vinculados (15)`).
  - Al aplicar un filtro o búsqueda (`count < total_count`), se refleja automáticamente el número de coincidencias respecto al total mediante la nueva clave i18n `common.filtered_count`: `Título (filtrados de total)` (ej. `Comandos Vinculados (1 de 3)`, `Recompensas Vinculadas (1 de 2)`).
  - Integrado de forma reactiva en [`commands_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/commands_view.py), [`rewards_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py), [`schedule_table_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_table_panel.py) y en la barra de paginación de [`logs_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/logs_view.py) (`log.pagination.info_filtered`).

- **Overlay de Cero Coincidencias con Botón de Restablecimiento ("Limpiar Filtros")**:
  - Se implementó `no_results_overlay` en [`frontend/widgets/table_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py) centrado en el viewport de la tabla.
  - Cuando los filtros o la búsqueda no arrojan resultados, se muestra un mensaje explicativo (`common.no_results_filter`) junto con un botón interactivo `[Limpiar filtros]` (`common.buttons.clear_filters`).
  - Al pulsar el botón, se vacía la barra de búsqueda y se restablecen todas las opciones de los filtros de columna mediante `reset_filters()` en [`FilterHeaderView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/filter_header.py), refrescando la tabla a su estado original sin recargar vistas.

- **Nueva Herramienta de Auditoría y Saneamiento de Código Muerto (`resources/tools/dead_code_manager.py`)**:
  - Se desarrolló un motor de análisis estático integral en tiempo $\mathcal{O}(N)$ amortizado basado en el árbol sintáctico nativo de Python (`ast.NodeVisitor`), diseñado para auditar tanto `frontend/` como `backend/`.
  - **Capacidades Principales**:
    - **Archivos y Módulos Huérfanos**: Identifica archivos `.py` que no son importados por ningún componente activo en todo el proyecto ni por los módulos de arranque (`main.py`).
    - **Símbolos y Clases No Referenciadas**: Detecta clases, funciones y variables top-level en desuso. Incorpora una whitelist de PySide6/Qt (`resizeEvent`, `paintEvent`, `eventFilter`, etc.) y métodos de ciclo de vida para garantizar cero falsos positivos en vistas y widgets.
    - **Importaciones Innecesarias**: Localiza imports definidos en cabecera que no se consumen dentro del cuerpo del archivo.
    - **Modos de Ejecución**: Soporta `--scope {frontend,backend,all}`, `--orphans-only`, `--symbols-only`, `--imports-only`, `--vulture` (integración con `uvx vulture`), `--clean-orphans` y `--dry-run` para limpieza asistida.

---

## Mejoras
- **Saneamiento y Depuración Integral de Archivos Huérfanos, Símbolos Muertos e Importaciones Innecesarias**:
  - **Archivos Huérfanos Eliminados (Reducción a 0)**:
    - [`frontend/components/log/logs_controls.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/log/logs_controls.py) y paquete obsoleto `frontend/components/log/`.
    - [`frontend/components/alerts/sidebar_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/sidebar_panel.py) y [`frontend/components/alerts/variant_item.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/variant_item.py) (antigua lista lateral de variantes de alertas, reemplazada por las pestañas reactivas `AlertVariantsTabBar`).
    - [`frontend/widgets/platform_controls.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/platform_controls.py) (`PlatformSwitchGroup`, reemplazado por los componentes universales `SegmentedControl` y `ModernFilterHeader`).
    - 4 interfaces no adoptadas en [`backend/interfaces/`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/interfaces/): `i_browser.py`, `i_chat_provider.py`, `i_chat_service.py` e `i_instance.py`.
  - **Clases y Símbolos Top-Level No Usados Eliminados (Reducción a 0)**:
    - `FormField` en [`frontend/widgets/block_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/block_widget.py) y su exportación en [`frontend/widgets/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/__init__.py).
    - `InspectorDualSpinBox`, `InspectorColorRow` e `InspectorFilePicker` en [`frontend/widgets/inspector_widgets.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/inspector_widgets.py) y sus exportaciones en [`frontend/widgets/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/__init__.py).
  - **Importaciones Innecesarias Depuradas (Reducción a 0)**:
    - Eliminadas importaciones olvidadas en `alerts_view.py`, `event_card.py`, `player_settings.py`, `block_widget.py`, `controls_widget.py`, `kick_ws_provider.py`, `piper_manager.py`, `overlay_manager.py` e `inspector_widgets.py`.
    - Blindaje de la herramienta `dead_code_manager.py` para reconocer referencias a submódulos (`import a.b`) y directivas de compilador (`from __future__ import annotations`).
  - **Resultado de la Auditoría Global**:
    - Archivos huérfanos: **0**
    - Símbolos no usados: **0**
    - Imports innecesarios: **0** (Código 100% limpio y optimizado).

- **Compactación y Optimización de Márgenes de Chat**:
  - Se redujo el padding de `QTextEdit[role="ConsoleDisplay"]` en `theme.py` a `2px 4px;` y se ajustó `document().setDocumentMargin(2)` en `ChatDisplayPanel`.
  - Se ajustó el margen del contenedor de tarjeta a `MARGIN_SM` (6px), maximizando el espacio útil de visualización de mensajes y evitando márgenes vacíos innecesarios.

- **Limpieza de Tokens de Degradados Obsoletos**:
  - Se eliminaron las constantes en desuso `GRADIENT_DANGER_*`, `GRADIENT_ACCENT_SUBTLE_*`, `COLOR_DANGER_BORDER_*` y `COLOR_ACCENT_SUBTLE_BORDER_*` de `theme.py`, reduciendo la superficie del módulo de temas.

- **Estandarización de `segmented_control` con la Estética `action_outlined`**:
  - Contenedor con borde `1px solid {COLOR_NEUTRAL_700}` y padding de 2px.
  - El botón seleccionado (`QPushButton[role="segmented_item"]:checked`) adopta el estilo de botón contorneado (`background-color: {COLOR_NEUTRAL_850}; border: 1px solid {COLOR_NEUTRAL_700}; color: {COLOR_WHITE}; font-weight: 500;`).
  - Los estados `:hover` y `:pressed` utilizan los mismos tokens interactivos `{COLOR_SURFACE_HOVER}` y `{COLOR_SURFACE_PRESSED}`.

- **Estandarización de `segmented_pagination`**:
  - Se eliminó el degradado rígido `{GRADIENT_NEUTRAL_FILL}` del contenedor y se reemplazó por la superficie limpia `{COLOR_NEUTRAL_850}` con borde `1px solid {COLOR_NEUTRAL_700}`.
  - Los divisores entre botones emplean `border-left: 1px solid {COLOR_NEUTRAL_700};`.
  - Estados interactivos en hover (`{COLOR_SURFACE_HOVER}`), pressed (`{COLOR_SURFACE_PRESSED}`) y disabled (`opacity: 0.35;`).

- **Alineación Geométrica de `SliderRow` (`frontend/widgets/block_widget.py`)**:
  - Se reestructuró el layout jerárquico de `SliderRow` para colocar el icono en una columna lateral independiente (`main_layout: QHBoxLayout`), conteniendo en la columna contigua (`content_layout: QVBoxLayout`) la cabecera y el control `slider_widget`.
  - El origen horizontal del deslizador coincide con el margen izquierdo de los textos, eliminando el desborde antiestético hacia la izquierda.

- **Redondeo, Geometría y Reposicionamiento del Icono de Filtro a la Izquierda (`FilterHeaderView` y `theme.py`)**:
  - Se rediseñó el estado `:hover` y `:pressed` de `QHeaderView::section` para adoptar una geometría redondeada (`border-radius: {RADIUS_SM}px;` / 6px) con margen (`margin: 3px 4px;`).
  - Al interactuar o abrir el menú desplegable de filtros, la sección se resalta como un botón interactivo redondeado flotante, eliminando el corte cuadrado a 90 grados que antes rompía la curvatura redondeada superior de la tarjeta contenedora (`table_card`).
  - La línea divisoria inferior de la cabecera se mantiene continua y de borde a borde mediante `border-bottom: 1.2px solid {COLOR_NEUTRAL_750};` aplicada al contenedor `QHeaderView`.
  - **Reposicionamiento del Icono de Filtro a la Izquierda**: Se reubicó el icono de filtro a la izquierda del título en lugar del extremo derecho. Esto previene colisiones visuales cuando la columna es estrecha, garantizando que el título se elida (`...`) a la derecha sin superponerse sobre el icono.

- **Fondo Opaco en `no_results_overlay` y Estabilidad Geométrica de Botones de Cabecera**:
  - Se configuró fondo sólido `{COLOR_NEUTRAL_900}` en `no_results_overlay` en [`ModernTableCard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py), evitando que las celdas o texto previo de la tabla se transparenten cuando no hay coincidencias de filtrado.
  - Se asignó política de tamaño `Minimum` al contenedor de cabecera (`header_widget`) y altura mínima de 30px (`setMinimumHeight(30)`) a los botones de acción, previniendo que los layouts de Qt colapsen verticalmente los botones durante el reacomodo responsivo.

---

## Correcciones
- **Subsanación de Ocultamiento Indebido de Tablas y Disparo de Empty State al Filtrar Cero Elementos (`INC-006`)**:
  - En `commands_view.py`, `rewards_view.py` y `schedule_table_panel.py`, la condición enviada a `set_empty(...)` evaluaba erróneamente la lista filtrada (`len(filtered) == 0`) en vez de los datos totales del sistema (`len(raw) == 0`). Esto provocaba que, al aplicar un filtro restrictivo sin coincidencias, la tabla y sus cabeceras desaparecieran, reemplazándose por el estado vacío inicial de bienvenida ("Crea un comando...").
  - Se corrigió evaluando `set_empty(len(raw) == 0)` para reservar el onboarding únicamente a tablas vacías de origen, y se incorporó `set_no_results(True)` con el overlay interactivo y botón de limpieza inmediata.

- **Crash Fatal al Navegar a Música por Destrucción en Cascada de Overlay C++ (`INC-007`)**:
  - **Problema**: En `queue_panel.py`, se ejecutaba `old_table.deleteLater()` para sustituir la tabla por defecto por `DragDropQueueTable`. Al destruirse la tabla nativa en C++, Qt eliminaba en cascada a su widget hijo `self.no_results_overlay`. Al navegar a la vista de Música, `card_queue.resizeEvent` invocaba `self.no_results_overlay.isVisible()`, disparando un crash fatal: `RuntimeError: libshiboken: Internal C++ object (PySide6.QtWidgets.QWidget) already deleted`.
  - **Solución**: Se añadió inyección de dependencias `custom_table: QTableWidget = None` en el constructor de [`ModernTableCard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py), eliminando el patrón destructivo `old_table.deleteLater()`. Adicionalmente, se blindaron los métodos de eventos con la comprobación `_is_valid_widget()` mediante `shiboken6.isValid()` y bloques `try ... except RuntimeError: pass`.

- **Corrección de Conteo Estático al Filtrar Tablas**:
  - Anteriormente, el título de la tarjeta en tablas como Comandos, Recompensas y Horarios solo renderizaba el total absoluto (`len(raw)`), permaneciendo inmutable aunque la búsqueda o los filtros de columna redujeran los resultados visibles. Ahora se calcula y actualiza dinámicamente tanto la cantidad filtrada como el total acumulado en $\mathcal{O}(1)$.

- **Prevención de Colisión de Texto e Icono de Filtro en Tablas (`FilterHeaderView`)**:
  - Al posicionar previamente el icono a la derecha sobreescribiendo la cabecera por defecto, los títulos largos de columna se dibujaban por debajo del icono en anchos reducidos. Con el icono anclado a la izquierda (`pad_left = 10`, `gap = 6`) y el cálculo dinámico de `text_rect` con elisión a la derecha, el texto nunca colisiona con el icono de filtro.

- **Eliminación Definitiva de Microcortes en los Pills de Chat**:
  - El uso de glifos de fuente (`\ue0b6` y `\ue0b4`) adyacentes a `<span>` con color de fondo generaba franjas verticales y microcortes oscuros por redondeo subpixel en monitores con escalado DPI en Windows. El renderizado vectorial en una pasada garantiza bordes redondeados perfectos, continuos y sin costuras a cualquier resolución.

- **Corrección de Sintaxis de Subcontrol en `QComboBox` (`frontend/common/theme.py`)**: Se corrigió el orden del selector `QComboBox::drop-down:hover, QComboBox::drop-down:focus` para evitar que el parser QSS colapsara el borde.

- **Sincronización Estricta de Roles QSS (`resources/tools/role_manager.py`)**:
  - Se validaron todos los roles del sistema tras la migración a botones sólidos, certificando 65 roles definidos, 65 en uso, 0 faltantes y 0 sin uso (100% de aprobación).
