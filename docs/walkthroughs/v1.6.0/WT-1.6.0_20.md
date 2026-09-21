# Walkthrough WT-1.6.0_20: Alineación de Líneas de Tablas con el Card (Edge-to-Edge) y Estandarización Visual

## Novedades
- **Alineación Continua de Tablas Edge-to-Edge en `ModernTableCard`**:
  - En [frontend/widgets/table_widget.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table_widget.py), `ModernTableCard` fue reestructurado como un contenedor con `margin=MARGIN_NONE` y `spacing=SPACING_NONE`.
  - La barra superior (título, buscador y botón de acción) se encapsuló en un `header_widget` con márgenes semánticos `MARGIN_MD = (8, 8, 8, 8)` y espaciado `SPACING_MD = 12`.
  - Se intercaló una línea divisoria continua [ModernDivider](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/block_widget.py) de 1px conectando de extremo a extremo con el marco del card.
  - La tabla (`ModernTable`) se aloja con margen cero horizontal, permitiendo que la línea de la cabecera (`QHeaderView::section`) y las líneas separadoras de filas toquen 100% de borde a borde las paredes laterales de la tarjeta en:
    - [CommandsView](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/commands_view.py)
    - [RewardsView](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py)
    - [TimersView](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/timers_view.py)
    - [ScheduleTablePanel](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_table_panel.py)
    - [QueuePanel](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/queue_panel.py)
- **Estandarización de `LogView` con Divisor Edge-to-Edge**:
  - En [frontend/views/logs_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/logs_view.py), `table_page_layout` se configuró con `MARGIN_NONE` y `SPACING_NONE`. Se intercaló un `ModernDivider` de ancho completo entre la tabla de logs y la barra de paginación (`pagination_bar`), logrando que las líneas de la tabla toquen los marcos del card sin sangrías laterales.

## Mejoras
- **Armonización de Curvatura de Esquinas Inferiores en QSS**:
  - En [frontend/common/theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py), se asignó `border-bottom-left-radius: {RADIUS_LG}px` y `border-bottom-right-radius: {RADIUS_LG}px` a la regla `QTableWidget` para que las filas inferiores respeten la curvatura del contenedor sin desbordes angulares.
- **Calibración de la Tarjeta OBS en `RewardsView`**:
  - En [frontend/views/rewards_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py), se estandarizó `obs_card` con `margin=MARGIN_MD` y `spacing=SPACING_SM`, asignando `contents_margins=MARGIN_NONE` a `SettingRow` para eliminar el doble padding interno.

## Correcciones
- **Eliminación de Líneas de Tabla Flotantes con Sangría**:
  - Corregido el defecto donde las líneas de cabecera y filas de las tablas flotaban con 8px de margen interno dentro de `ModernTableCard`, logrando una apariencia integrada y unida al card.

## Verificación
- Prueba unitaria automatizada agregada en `resources/tests/test_antigravity_ui_theme.py`:
  - `test_table_cards_and_edge_to_edge_alignment` (evalúa `ModernTableCard` sin márgenes, presencia del `ModernDivider` continuo, y la integración en `CommandsView`, `RewardsView`, `TimersView` y `LogView`).
- Ejecución completa: `uv run pytest resources/tests/` (42 pruebas superadas al 100% en 2.04s).
