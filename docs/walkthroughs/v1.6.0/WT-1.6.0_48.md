# Walkthrough WT-1.6.0_48: Erradicación DRY Fase 2 - Reducción a 24 Clusters y 3 a Umbral Estándar

## Novedades
- **Helpers de Pintura y Badge en `AlertMockupWidget`**:
  - `_draw_platform_badge`: Encapsula el cálculo de geometría, selección de paleta (Twitch vs Kick), pintado de píldora redondeada y tipografía de insignia de plataforma.
  - `_draw_text_with_shadow`: Centraliza la elisión de texto y pintado bicapa (sombra + color principal) en `QPainter`.
  - `_draw_side_alert_layout`: Unifica los layouts laterales izquierdo y derecho (`_draw_side_layout` y `_draw_side_right_layout`) parametrizando la orientación y alineación.
- **Fila Unificada de Icono y Métrica en `overlay_settings.py`**:
  - `_build_icon_text_row`: Función helper que instancia un contenedor con icono coloreado de tamaño estándar, etiqueta elíptica con política fija y soporte opcional de tooltips.

## Mejoras
- **Erradicación Masiva de Clusters en Mockups de Alertas (`alert_mockup.py`)**:
  - Reducidos más de 12 clusters duplicados derivados de bloques de renderizado superpuestos en `_draw_above_layout`, `_draw_below_layout`, `_draw_side_layout` y `_draw_side_right_layout`.
- **Estandarización de Métricas y Toggles en Chat Overlay (`overlay_settings.py`)**:
  - Unificados `CompactToggleItem.__init__` y `ChatOverlaySettingsPanel._create_metric_header` a través de `_build_icon_text_row`, erradicando 4 clusters continuos.
- **Limpieza de Nulificación de Workers en `MainWindowCore`**:
  - Implementado `_nullify_worker_attributes(*attrs)`, eliminando asignaciones redundantes en `_stop_kick_connection_workers`, `_stop_twitch_connection_workers` y `_stop_all_workers`.
- **Modernización de `create_badge` y `ModernToast`**:
  - `frontend/widgets/block_widget.py`: `create_badge` migrado a `create_row_layout`.
  - `frontend/navigation/toast_component.py`: Layout de `ModernToast` migrado a `create_row_layout`.
- **Limpieza de Cabecera en `ScheduleQuickChangePanel`**:
  - Uso de `create_row_layout`, `create_col_layout` y `create_text_label` en `_setup_quick_change_card`.
- **Métricas Finales DRY**:
  - Clusters a umbral de 5 sentencias reducidos de **67 -> 46 -> 24 clusters** en `reports/dry_report.json` y `reports/dry_report2.json` (reducción neta del 64.2%).
  - Clusters a umbral estándar ($\ge 8$ sentencias) reducidos a solo **3 clusters** en todo el proyecto.

## Correcciones
- Eliminadas las repeticiones de código redundante de pintado y ensamblado de layouts sin alterar el comportamiento visual ni las firmas públicas de los componentes.
- Suite de pruebas unitarias 100% pasando: 82/82 PASS en 2.41s (`pytest resources/tests`).
- Suite maestra de salud 100% pasando: 11/11 PASS (`system_health_audit.py --all`).
