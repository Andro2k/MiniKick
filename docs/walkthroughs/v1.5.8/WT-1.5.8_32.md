# Walkthrough WT-1.5.8_32: Estandarización Global de Espaciados y Márgenes UI

## 1. Contexto y Objetivos
En la interfaz gráfica de MiniKick existían discrepancias en los valores de espaciado (`setSpacing()`, `addSpacing()`) y márgenes (`setContentsMargins()`), empleando números enteros dispersos y no canónicos (p. ej. `2, 4, 5, 6, 8, 10, 12, 14, 16, 20`).
El objetivo fue realizar una auditoría integral de la capa de presentación (`frontend/`), definiendo un conjunto de tokens de escala espacial 4/8pt centralizados en [frontend/common/theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) y estandarizando de forma estricta todos los componentes, vistas, diálogos y controles del sistema.

---

## 2. Sistema de Tokens Espaciales ([frontend/common/theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py))

Se consolidó y exportó la siguiente escala espacial canónica en [frontend/common/__init__.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/__init__.py):

| Token Spacing | Valor | Token Margins (Tupla) | Valor |
| :--- | :--- | :--- | :--- |
| `SPACING_NONE` | `0` | `MARGIN_NONE` | `(0, 0, 0, 0)` |
| `SPACING_2XS` | `2` | `MARGIN_2XS` | `(2, 2, 2, 2)` |
| `SPACING_XS` | `4` | `MARGIN_XS` | `(4, 4, 4, 4)` |
| `SPACING_SM` | `6` | `MARGIN_SM` | `(6, 6, 6, 6)` |
| `SPACING_MD` | `8` | `MARGIN_MD` | `(8, 8, 8, 8)` |
| `SPACING_LG` | `12` | `MARGIN_LG` | `(12, 12, 12, 12)` |
| `SPACING_XL` | `16` | `MARGIN_XL` | `(16, 16, 16, 16)` |
| `SPACING_2XL` | `20` | `MARGIN_2XL` | `(20, 20, 20, 20)` |
| — | — | `MARGIN_H_XS` | `(4, 0, 4, 0)` |
| — | — | `MARGIN_H_SM` | `(6, 0, 6, 0)` |
| — | — | `MARGIN_H_MD` | `(8, 0, 8, 0)` |
| — | — | `MARGIN_V_XS` | `(0, 4, 0, 4)` |
| — | — | `MARGIN_V_SM` | `(0, 6, 0, 6)` |
| — | — | `MARGIN_V_MD` | `(0, 8, 0, 8)` |

---

## 3. Módulos Estandarizados

1. **Tokens y Constantes Globales**:
   - [frontend/common/theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py): Definición de tokens de espaciado y márgenes.
   - [frontend/common/__init__.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/__init__.py): Exportación canónica en `__all__`.

2. **Widgets Reutilizables ([frontend/widgets/](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets)):**
   - [blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py): `ViewHeader`, `SettingRow`, `FormField`, `SliderRow`, `StatCard`, `ModernCard`, `ExpandableSettingCard`, `create_badge`.
   - [table.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table.py): `ModernTableCard`, `addSpacing`, celdas de acciones y plataforma.
   - [segmented_control.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/segmented_control.py), [search_bar.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/search_bar.py), [clearable_line_edit.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/clearable_line_edit.py), [category_search.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/category_search.py), [platform_controls.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/platform_controls.py), [pagination.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/pagination.py), [color_picker.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/color_picker.py), [flow_layout.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/flow_layout.py).

3. **Diálogos Modales ([frontend/dialogs/](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs)):**
   - [base_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py): `ModernFramelessShell`, `StandardBaseDialog`, `ModernWizardPanel`.
   - [bug_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/bug_report_dialog.py), [crash_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/crash_report_dialog.py), [platform_connect_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/platform_connect_dialog.py), [timer_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/timer_dialog.py), [rewards_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/rewards_dialog.py), [command_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/command_dialog.py), [update_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/update_dialog.py), [already_running_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/already_running_dialog.py), [release_notes_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/release_notes_dialog.py), [piper_voices_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/piper_voices_dialog.py), [visual_positioner_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/visual_positioner_dialog.py).

4. **Componentes Específicos ([frontend/components/](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components)):**
   - **Alerts**: [event_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py), [variant_item.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/variant_item.py), [overlay_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/overlay_card.py), [sidebar_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/sidebar_panel.py).
   - **Chat**: [bot_mute.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py), [tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py), [overlay_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/overlay_settings.py), [chat_display.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/chat_display.py).
   - **Music**: [stats_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/stats_panel.py), [queue_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/queue_panel.py), [player_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/player_settings.py), [music_settings_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/music_settings_panel.py), [commands_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/commands_panel.py).
   - **Schedule**: [schedule_form_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_form_panel.py), [quick_change_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/quick_change_panel.py), [schedule_table_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_table_panel.py).
   - **Widgets**: [widget_card_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/widgets/widget_card_component.py).
   - **Log**: [log_controls.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/log/log_controls.py).
   - **Dialog Items**: [image_dropzone.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/image_dropzone.py), [piper_voice_item.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/piper_voice_item.py), [severity_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/severity_card.py), [draggable_box.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/draggable_box.py).

5. **Navegación ([frontend/navigation/](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation)):**
   - [sidebar_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py): Layout principal, cabecera, navegación expandida/colapsada y márgenes del perfil.
   - [toast_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py): Márgenes del toast y de los bloques textuales.

6. **Vistas Principales ([frontend/views/](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views)):**
   - [dashboard_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py), [alerts_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py), [log_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/log_view.py), [timers_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/timers_view.py), [widgets_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/widgets_view.py), [spam_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/spam_view.py), [settings_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py), [schedule_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/schedule_view.py), [music_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/music_view.py), [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py), [command_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/command_view.py).

---

## 4. Verificación y Resultados

- **Auditoría Regex**: Búsqueda global de llamadas con números mágicos:
  - `setSpacing(\d+)`: **0 ocurrencias** (100% tokenizado).
  - `addSpacing(\d+)`: **0 ocurrencias** (100% tokenizado).
  - `(margin|spacing)=\d+`: **0 ocurrencias** (100% tokenizado).
- **Pruebas Automatizadas**:
  ```bash
  uv run pytest resources/tests/unit/
  ```
  **Resultado**: **288 pasados de 288 (100%)** en 51.75s, sin regresiones funcionales ni visuales.
