# Walkthrough WT-1.6.0_18: Descongestión Visual y Modernización de Alertas (AlertsView) al Estándar Antigravity con ExpandableCard

## Novedades
- **Unificación de Secciones de Alertas con `ExpandableCard`**:
  - En [frontend/components/alerts/event_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py), las 4 tarjetas de configuración (`card_general`, `card_design`, `card_typography`, `card_media`) fueron transformadas en instancias de `ExpandableCard`.
  - Cada tarjeta ahora cuenta con un encabezado interactivo con cursor de mano, icono temático, título descriptivo, subtítulo explicativo contextual y un chevron animado (`chevron-down-filled.svg` / `chevron-up-filled.svg`) para expandir/colapsar bajo demanda.
  - Se añadieron descripciones en [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) para cada sección (`general_desc`, `appearance_desc`, `text_speech_desc`, `media_sound_desc`).
- **Estado de Expansión Inteligente por Defecto (Reducción de Ruido Visual >50%)**:
  - `card_general` (duración, animación de entrada/salida) y `card_typography` (plantilla de texto, voz TTS, volumen) inician expandidas por defecto (`is_expanded=True`).
  - `card_design` (colores, sombras, bordes) y `card_media` (audio e imagen) inician colapsadas (`is_expanded=False`), manteniendo el foco en el contenido principal y reduciendo drásticamente la saturación de controles en pantalla.
- **Botonera de Acciones en `header_row` al Estilo Antigravity**:
  - En [frontend/components/alerts/event_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py), se estilizó la botonera superior eliminando textos verbosos y adoptando el diseño limpio de Antigravity:
    - `btn_discard`: Botón de icono `x-filled.svg` con tooltip contextual (`alerts.buttons.discard_tooltip`).
    - `btn_duplicate`: Botón de icono `copy-filled.svg` con tooltip contextual (`alerts.buttons.duplicate_tooltip`).
    - `btn_test`: Botón compacto `[ ▶ Probar ]` (`alerts.buttons.test_short`).
    - `btn_save`: Botón de acción principal `[ ✓ Guardar ]` (`alerts.buttons.save_short`).
- **Tarjeta de OBS Overlay Compacta y Minimalista**:
  - En [frontend/components/alerts/overlay_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/overlay_card.py), `AlertsOverlayCard` se redujo a una única fila horizontal elegante con icono, título/descripción y el botón `btn_copy_url` ("Copiar Enlace"). Se ocultó la URL en texto plano y se retiró el botón redundante de previsualización, manteniendo los atributos en memoria para retrocompatibilidad total.

## Mejoras
- **Líneas Divisorias Edge-to-Edge Continuas en `card_preview`**:
  - `card_preview` se reestructuró con `margin=MARGIN_NONE` y `spacing=SPACING_NONE`. Se intercalaron llamadas a `add_separator()` para que las líneas divisorias de 1px conecten perfectamente de extremo a extremo con el marco de la tarjeta, alojando el encabezado, el mockup interactivo y los controles de dimensiones en contenedores internos con `MARGIN_MD`.
- **Soporte de `add_widget` y `add_layout` en `ExpandableCard`**:
  - En [frontend/widgets/block_widget.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/block_widget.py), se añadieron los métodos delegados `add_widget()` y `add_layout()` apuntando a `self.body_layout`, además de permitir los parámetros `desc` o `description` indistintamente y ocultar automáticamente `lbl_desc` cuando el texto esté vacío para evitar padding residual.
- **Calibración y Estandarización de Márgenes y Espaciados**:
  - En [frontend/components/alerts/overlay_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/overlay_card.py), `AlertsOverlayCard` utiliza `margin=MARGIN_MD` y `spacing=SPACING_SM`.
  - En [frontend/views/alerts_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py), `self.notice_banner` se estandarizó con `margin=MARGIN_MD`.
  - En [frontend/components/alerts/event_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py), `header_card` utiliza `margin=MARGIN_MD`, y el espaciado de columnas `self.body_box` se compactó a `SPACING_MD` (12px).

## Correcciones
- **Eliminación de Estiramiento Vertical en `ExpandableCard` Colapsado**:
  - Corregido el defecto donde las tarjetas contraídas se expandían a 300px dividiendo el título en la parte superior y la descripción en el fondo. Se fijó `QSizePolicy.Policy.Maximum` al contraer, `text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)` para mantener agrupados título y subtítulo, y se añadieron `col_left.addStretch(1)` y `col_right.addStretch(1)` con alineación superior en las columnas.
- **Eliminación de Divisores Hendidos en `card_preview`**:
  - Corregida la sangría lateral de 8px en las líneas divisorias de la tarjeta de vista previa al migrar a márgenes cero y separadores continuos.
- **Eliminación de Saturación de 28+ Controles Simultáneos**:
  - Se solucionó la sobrecarga visual donde todos los formularios de configuración se renderizaban desplegados simultáneamente en 3 columnas rígidas.

## Verificación
- Prueba unitaria automatizada agregada en `resources/tests/test_antigravity_ui_theme.py`:
  - `test_alerts_view_and_expandable_cards_standard` (evalúa `ExpandableCard`, divisores continuos en `card_preview`, botones compactos en `header_row`, y tarjeta OBS compacta).
- Ejecución completa: `uv run pytest resources/tests/` (40 pruebas superadas al 100% en 1.91s).
