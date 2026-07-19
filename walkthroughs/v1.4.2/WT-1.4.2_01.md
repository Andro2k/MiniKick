# WT-1.4.2_01 - Solución de Escala y Alineación de Iconos (High DPI) y Sincronización TTS

Hemos realizado e implementado todos los cambios necesarios para corregir la borrosidad, desalineación y mala escala de los iconos en sistemas con escalado DPI de Windows diferente de 100%, así como la desincronización de la selección de voces en el sistema de chat TTS.

---

## Parte 1: Escala y Alineación de Iconos (High DPI)

### Diagnóstico Completo del Problema
1. **Método heredado de Qt (`app.devicePixelRatio()`):**
   El código original y las utilidades hacían uso de `app.devicePixelRatio()`. En PySide6/Qt6, este método tiende a devolver `1.0` de forma estática antes de que las ventanas se inicialicen. Esto causaba que todos los iconos generados al inicio de la aplicación se renderizaran con escala `1.0` (100%), viéndose diminutos y borrosos en comparación con el texto que sí se escalaba.
2. **DPR prematuro durante la construcción del widget (`self.devicePixelRatio()`):**
   Cuando los widgets (como el Sidebar o las pestañas) se instancian en `__init__`, todavía no están mostrados en la pantalla ni asociados a un contexto de ventana final. Por ende, la llamada a `self.devicePixelRatio()` durante la inicialización devolvía de forma predeterminada `1.0`. Al pasar explícitamente ese valor a `get_icon_colored`, se forzaba la creación de un icono de baja resolución (DPR 1.0) que luego se pixelaba al ser estirado en una pantalla de escala 1.25.
3. **Colorización por rasterización intermedia:**
   Originalmente, `get_icon_colored` usaba `QIcon.pixmap` para rasterizar el SVG a negro, creaba otro pixmap transparente, dibujaba el icono negro encima y aplicaba un relleno de color mediante `CompositionMode_SourceIn`. Esta doble rasterización y copiado arruinaba la suavidad de los bordes vectoriales (anti-aliasing) del SVG original.

### Cambios Realizados
- **`utils.py`**:
  - **Optimización de lectura y caché**: Implementamos `_load_svg_raw` con caché (`@lru_cache`) para leer el código XML del archivo SVG una única vez desde el disco.
  - **Colorización Vectorial Nativa**: Modificamos `_get_icon_colored_impl` para que reemplace el atributo de color en el XML del SVG (`currentColor` por `color_str`) y dibuje el vector directamente en el pixmap de destino usando `QSvgRenderer`. Esto mantiene la fidelidad vectorial intacta y elimina cualquier pixelación o defecto de bordes.
  - **DPR por Defecto Robusto**: Ajustamos `_get_default_dpr` para consultar a `app.primaryScreen().devicePixelRatio()` en primer lugar, garantizando que el ratio real (`1.25`, `1.5`, etc.) esté disponible al instante desde el inicio.
- **`sidebar_component.py`**:
  - Removimos el parámetro explícito `self.devicePixelRatio()` en las llamadas a `get_icon_colored` durante el constructor. Al no pasarlo, la utilidad cae en `_get_default_dpr()` que recupera el valor correcto de la pantalla (`1.25`) en lugar del `1.0` prematuro del widget no mostrado.

---

## Parte 2: Sincronización de Selección de Voz TTS

### Diagnóstico del Problema
Cuando el usuario cambiaba el idioma en el ComboBox de la interfaz gráfica (`combo_lang`):
1. Se recalculaba la lista de voces correspondientes a ese idioma en el ComboBox de voz (`combo_voice`).
2. Para evitar eventos innecesarios mientras se borraban e insertaban ítems en la lista, la UI bloqueaba temporalmente las señales de `combo_voice` mediante `blockSignals(True)`.
3. Se seleccionaba la primera voz disponible por defecto.
4. Al estar las señales bloqueadas, el controlador nunca se enteraba de esta selección predeterminada de voz (el evento `voice_changed` no se disparaba), dejando el motor TTS del backend con la voz anterior (por ejemplo, una voz de España) mientras que la UI reflejaba visualmente una voz del nuevo idioma (por ejemplo, Argentina).

### Cambios Realizados
- **`backend/controllers/chat_controller.py`**:
  - Actualizamos el método de filtrado de idiomas `_filter_voices_by_language` para que el controlador sea el encargado de resolver la voz final que debe seleccionarse (`final_select_id`).
  - Si la voz actual no se encuentra en el nuevo idioma filtrado (o si el usuario cambia manualmente el filtro de idioma), el controlador asigna de forma proactiva y silenciosa la primera voz de la lista filtrada al motor del backend llamando a `self.service.set_voice(provider, final_select_id)` y actualizando la memoria caché de configuración.
  - Finalmente, actualiza la UI (`update_voices`) enviándole explícitamente el `final_select_id` calculado. Esto mantiene tanto la UI como el motor TTS en perfecta sincronía lógica.

---

## Verificación Realizada

- Validamos que la aplicación inicializa, compila e importa todos los módulos correctamente sin excepciones ejecutando `uv run main.py`.
