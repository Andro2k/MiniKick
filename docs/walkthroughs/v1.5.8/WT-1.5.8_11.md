# Walkthrough: WT-1.5.8_11 - Rediseño de AlertsView estilo Twitch Alerts Studio y Eliminación de Spam de Toasts

## 1. Resumen Ejecutivo
Se rediseñó por completo la interfaz de gestión de alertas en [`frontend/views/alerts_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py) adoptando una arquitectura **Master-Detail inspirada en Twitch Alerts Studio**:
1. **Problema Previo**: Cuadrícula de 2 columnas donde todos los formularios de configuración se desplegaban en paralelo, consumiendo espacio excesivo y generando escrituras a SQLite y toasts recurrentes con cada tecla pulsada o movimiento de slider (`minikick.log:L2577-L2784`).
2. **Solución Implementada**:
   - **Panel Izquierdo (Sidebar de Variantes)**: Lista interactiva de variantes de alerta (`follow`, `subscription`, `resub`, `sub_gift`, `raid`, `cheer`) filtradas por plataforma (Kick / Twitch), con iconos de marca, títulos descriptivos e indicadores visuales de estado (activo/inactivo).
   - **Panel Derecho (Editor de Ajustes)**: Editor focalizado para la variante seleccionada, dividido en tarjetas limpias ("Ajustes Generales" y "Multimedia y Audio").
   - **Barra de Acciones Controlada**: Botones superiores de **"Guardar Cambios"** y **"Descartar"** con seguimiento de estado modificado en memoria (*dirty state*), además del botón **"Probar Alerta"**.
   - **Eliminación del Spam de Toasts**: Las ediciones en memoria no emiten persistencia a la base de datos hasta que el usuario pulsa explícitamente "Guardar Cambios", generando un único registro en la base de datos y un único toast.

---

## 2. Cambios de Arquitectura y Componentes

### Componentes en `frontend/views/alerts_view.py`:
- **`AlertVariantListItem`**:
  - Item seleccionable con icono coloreado por plataforma (`COLOR_GREEN` para Kick, `COLOR_PURPLE` para Twitch).
  - Muestra título del evento, descripción concisa y dot indicador de habilitado/deshabilitado.
  - Resaltado visual moderno con borde de acento y fondo destacado al ser seleccionado.
- **`AlertEventCard`**:
  - Gestiona `_saved_config`, `_current_config` e `_is_dirty`.
  - Botón `btn_save` ("Guardar Cambios"): Habilitado solo cuando hay cambios locales pendientes; al pulsarlo persiste y emite `save_requested`.
  - Botón `btn_discard` ("Descartar"): Restaura los valores previos y restablece el estado sucio.
  - Botón `btn_test` ("Probar Alerta"): Despacha la prueba al servidor de overlay.
  - Indicador `lbl_dirty` en color ámbar avisando que hay cambios sin guardar.
- **`AlertsView`**:
  - Mantiene el card superior responsivo con la URL del overlay de OBS.
  - Organiza las páginas Master-Detail en `self.stack` para Kick y Twitch.
  - Preserva el diccionario `self.cards[(platform, alert_type)]` para compatibilidad completa con el controlador y los tests unitarios.

---

## 3. Soporte Internacional (i18n)
Nuevas claves simétricas añadidas en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json):
- `alerts.buttons.save`: "Guardar Cambios" / "Save Changes"
- `alerts.buttons.discard`: "Descartar" / "Discard"
- `alerts.sections.general`: "Ajustes Generales" / "General Settings"
- `alerts.sections.media`: "Multimedia y Audio" / "Media & Audio"
- `alerts.sidebar.title`: "Variantes de Alerta" / "Alert Variants"
- `alerts.status.unsaved`: "Cambios sin guardar" / "Unsaved changes"

---

## 4. Verificación y Resultados

1. **Pruebas de UI de Alertas (`test_alerts_ui.py`)**:
   - `test_alert_event_card_interactions`: PASSED.
   - `test_alerts_view_instantiation_and_platform_switch`: PASSED.
   - `test_alerts_controller_lifecycle`: PASSED.
   - `test_alerts_controller_attach_view_idempotency`: PASSED.
   - `test_alert_event_card_save_and_discard_flow` (Nuevo): PASSED.
2. **Auditoría de Roles y Estados QSS (`role_manager.py`)**:
   - 100% de los roles usados en la vista están definidos en `theme.py`.
3. **Integridad de i18n (`test_i18n_integrity.py`)**:
   - Paridad total entre `es.json` y `en.json`.
4. **Suite Completa de Pruebas Unitarias**:
   - `pytest resources/tests/unit`: **240 passed** en 11.90s.

---

## 5. Optimización del Comportamiento Flex y Responsivo
- **Eliminación de Anchos Rígidos**: Se agregaron envolturas de texto (`setWordWrap(True)`) en descripciones de OBS, pistas de plantillas y títulos para que `minimumSizeHint()` se reduzca de ~500px a valores flexibles.
- **Acciones Flexibles en el Editor**: `AlertEventCard` separa título y acciones en dos filas ordenadas, adaptando los botones de prueba y guardado (`actions_box`) entre horizontal y vertical si el ancho es menor a 340px.
- **Master-Detail Fluido**: La lista de variantes se mantiene como barra lateral fija (225px) y el editor ocupa el 100% restante (`stretch=1`), sin desbordamiento horizontal ni recorte de botones ("Copiar URL", "Previsualizar Overlay", "Examinar", "Guardar Cambios") a través de todas las resoluciones de ventana probadas (500px a 1400px+).
- **Regla Estricta de Código**: Cero `setStyleSheet` dispersos y un único comentario en la primera línea (`# frontend\views\alerts_view.py`).
