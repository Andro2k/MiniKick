# Walkthrough WT-1.6.0_44: Refactorización DRY de Layouts y Erradicación de Clones AST

## Novedades
- **Helpers de Layout Declarativos en `frontend/widgets/layout_helpers.py`**:
  - Incorporación de `create_box_layout(direction, spacing, margins, parent)`: inicializa layouts direccionales (`QBoxLayout`) con espaciado y márgenes configurados en una sola invocación.
  - Incorporación de `create_switch_field(switch, label_text, role, spacing, parent)`: encapsula el patrón repetitivo de empaquetar un `ModernSwitch` junto con su etiqueta `QLabel` descriptiva en un layout horizontal alineado.
  - Exportación de ambos helpers en el paquete `frontend.widgets` para su uso transversal en toda la interfaz.

## Mejoras
- **Reducción Sistemática de Duplicación AST (DRY)**:
  - **Paneles de Configuración y Diálogos**: Refactorización de la instanciación de switches de plataformas en [quick_change_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/quick_change_panel.py), [schedule_form_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_form_panel.py) y [timers_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/timers_dialog.py) utilizando `create_switch_field`.
  - **Componentes de Tarjetas y Diálogos**: Refactorización del setup repetitivo de `QVBoxLayout` y `QHBoxLayout` en [platform_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dashboard/platform_card.py), [piper_voice_item.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/piper_voice_item.py), [severity_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/severity_card.py), [tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py) y [piper_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/piper_dialog.py) mediante `create_col_layout`, `create_row_layout` y `create_box_layout`.
  - **Contenedores Principales de Vistas**: Estandarización de la estructura de contenedores flexibles en [schedule_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/schedule_view.py), [spam_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/spam_view.py) y [widgets_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/widgets_view.py) colapsando secuencias repetitivas de 5 sentencias a 2 llamadas limpias y declarativas.
  - **Impacto Métrico DRY**: Los clusters de duplicación reportados por `dry_duplication_auditor.py` descendieron de **132 clusters a 94 clusters** (a umbral estricto $\ge 5$ sentencias) y a tan solo 30 clusters al umbral estándar ($\ge 8$).

## Correcciones
- **Integridad de Filtros de Tabla en Vistas de Lista**:
  - Corrección de referencias indexadas seguras en los filtros por columna de [commands_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/commands_view.py) y [rewards_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py), previniendo `NameError` tras la consolidación de cabeceras.
- **Validación y Salud del Sistema**:
  - 82 de 82 tests pasando exitosamente en `pytest resources/tests`.
  - 11 de 11 herramientas de control de calidad aprobadas al 100% en `system_health_audit.py --all` (0 textos hardcodeados, 0 fugas de señales Qt, 0 fugas de ventanas HWND y 100% paridad i18n).
