# Walkthrough WT-1.4.7_04 - Corrección Completa de NoWheelComboBox y ModernCard

## Resumen

Tras analizar los registros de logs del usuario (`minikick.log`), se identificaron y corrigieron todas las instancias restantes de componentes desacoplados (`NoWheelComboBox`, `ModernCard`, `QWidget`) que figuraban como ventanas huérfanas durante la inicialización de Qt.

## Cambios Aplicados

1. **[frontend/common/utils.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/utils.py)**:
   - Se añadió constructor `__init__(self, parent=None)` en `NoWheelComboBox` y `NoWheelSlider`.

2. **[frontend/widgets/blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)**:
   - Se asignó `parent=self` a los desplegables de `ExpandableSettingCard`.

3. **Vistas y Componentes Secundarios**:
   - Asignación de `parent=self` en todas las instancias de `ModernCard` y `NoWheelComboBox` en `settings_view.py`, `rewards_view.py`, `dashboard_view.py`, `stats_panel.py`, `player_settings.py`, `overlay_settings.py` y `tts_settings.py`.

## Resultados

- 0 ventanas huérfanas secundarias en `QApplication.topLevelWidgets()`.
- Apertura fluida sin parpadeos.
