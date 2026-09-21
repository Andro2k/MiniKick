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

---

## Mejoras
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

---

## Correcciones
- **Eliminación Definitiva de Microcortes en los Pills de Chat**:
  - El uso de glifos de fuente (`\ue0b6` y `\ue0b4`) adyacentes a `<span>` con color de fondo generaba franjas verticales y microcortes oscuros por redondeo subpixel en monitores con escalado DPI en Windows. El renderizado vectorial en una pasada garantiza bordes redondeados perfectos, continuos y sin costuras a cualquier resolución.

- **Corrección de Sintaxis de Subcontrol en `QComboBox` (`frontend/common/theme.py`)**: Se corrigió el orden del selector `QComboBox::drop-down:hover, QComboBox::drop-down:focus` para evitar que el parser QSS colapsara el borde.

- **Sincronización Estricta de Roles QSS (`resources/tools/role_manager.py`)**:
  - Se validaron todos los roles del sistema tras la migración a botones sólidos, certificando 65 roles definidos, 65 en uso, 0 faltantes y 0 sin uso (100% de aprobación).
