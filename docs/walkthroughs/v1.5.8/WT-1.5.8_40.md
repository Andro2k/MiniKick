# Walkthrough WT-1.5.8_40: Reorganización de Controles de Alertas y Switch de Activación en la Barra Lateral

## 1. Contexto y Objetivos

Para maximizar la ergonomía, velocidad de configuración y claridad visual del módulo de alertas, el usuario solicitó tres mejoras específicas:
1. **Switch de Alerta Activa en la barra lateral**: En [`sidebar_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/sidebar_panel.py) y [`variant_item.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/variant_item.py), reemplazar el punto indicador pasivo (`●`) por un interruptor interactivo [`ModernSwitch`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls.py), permitiendo habilitar o deshabilitar cualquier alerta en tiempo real directamente desde el listado lateral sin tener que navegar individualmente a cada una.
2. **"Leer TTS" junto a "Plantilla de Texto"**: En [`event_card.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py), ubicar el control de síntesis de voz (TTS) al lado del campo de plantilla de texto dentro de *Ajustes Generales*.
3. **"Duración" dentro de "Diseño y Apariencia"**: En [`event_card.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py), mover el control de duración como una fila uniforme [`SettingRow`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py) (icono `clock.svg`, título, descripción y spinbox) dentro de la tarjeta de *Diseño y Apariencia*.
4. **Eliminación de la franja superior (`quick_strip`)**: Al redistribuir los tres controles, se eliminó la fila superior redundante en *Ajustes Generales*.

---

## 2. Cambios Implementados

### A. Barra Lateral de Variantes ([`variant_item.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/variant_item.py) & [`sidebar_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/sidebar_panel.py))
- Se sustituyó `self.status_lbl = QLabel("●")` por `self.sw_enabled = ModernSwitch(parent=self)`.
- Se introdujo la señal `toggled = Signal(str, bool)` en `AlertVariantListItem`, la cual es propagada por `AlertsSidebarPanel` mediante `variant_enabled_changed = Signal(str, bool)`.
- `set_enabled_state(self, enabled: bool)` bloquea señales temporalmente (`blockSignals`) para evitar bucles recursivos al sincronizarse desde el estado del modelo o la tarjeta.

### B. Vista Principal de Alertas ([`alerts_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py))
- Se conectó `sidebar_panel.variant_enabled_changed` al método `_on_sidebar_variant_enabled_changed(self, platform, alert_type, enabled)`.
- Al alternar el interruptor en la lista lateral, se actualiza la tarjeta correspondiente y se persiste el cambio inmediatamente a través de `card.save_enabled_change(enabled)`, propagando la actualización hacia OBS y la base de datos sin fricción.

### C. Tarjeta de Configuración de Alerta ([`event_card.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py))
- **Duración en Diseño y Apariencia**:
  - Se añadió `self.spin_duration` (con sufijo `" s"`, rango 1 a 60, ancho de 142px) emparejado con un `SettingRow` con icono `"clock.svg"`, título `"alerts.fields.duration"` y nueva descripción `"alerts.fields.duration_desc"`.
  - Ubicado justamente debajo de "Alineación del Texto" y antes de los selectores de color.
- **TTS junto a Plantilla de Texto**:
  - En *Ajustes Generales*, se estructuró `template_row = QHBoxLayout()`:
    - Columna izquierda (`col_template`, `stretch=1`): Título de plantilla, campo de texto [`ClearableLineEdit`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/line_edit.py) y texto de ayuda de variables.
    - Columna derecha (`col_tts`, `stretch=0`): Título `"Leer alerta con voz (TTS)"` y el switch [`ModernSwitch`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls.py).
- **Sincronización de Estado**:
  - Se conservó `self.sw_enabled` interno oculto para garantizar retrocompatibilidad total con las lecturas y escrituras de configuración.
  - Se añadieron `set_enabled(self, enabled: bool)` y `save_enabled_change(self, enabled: bool)`.

### D. Diccionarios de Traducción ([`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) & [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json))
- Se incorporó la clave con paridad exacta:
  - `alerts.fields.duration_desc`: `"Tiempo en segundos que se muestra la alerta en pantalla."` / `"Time in seconds the alert is displayed on screen."`

---

## 3. Verificación de Pruebas

```bash
uv run pytest resources/tests/unit/ui/test_alerts_ui.py resources/tests/unit/ui/test_i18n_integrity.py
```
**Resultado:** 13/13 pruebas pasadas con 100% de éxito, incluyendo la nueva prueba `test_alert_sidebar_switch_and_reorganized_controls`.
