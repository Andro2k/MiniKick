# Walkthrough WT-1.5.9_24: Remodelación y Personalización Granular de Alertas

## Resumen del Cambio
Se remodeló integralmente el sistema de personalización de alertas en MiniKick y el overlay web de OBS (`assets/overlays/alerts/alerts.html`), eliminando los estilos rígidos predefinidos (`compact`, `glass`, `minimal`, `sticker`) para ofrecer un control granular y directo inspirado en la interfaz de referencia de Twitch:
- Configuración de animaciones de entrada y salida con selección de tipo y duración independiente en segundos.
- Control visual del contenedor: color de fondo, porcentaje de opacidad, radio de esquinas redondeadas, espacio de relleno interior (padding), separación entre elementos (gap/spacing) y sombra de caja (box-shadow).
- Tipografía avanzada: familia de fuente, grosor/peso (normal, seminegrita, negrita, extra negrita), tamaño en píxeles, alineación de texto (izquierda, centro, derecha, justificado), color de texto principal, color de detalle/resaltado y sombra de texto.
- Persistencia y migración automática en base de datos SQLite sin roturas de esquema.

---

## 1. Novedades

- **Biblioteca de Animaciones de Entrada y Salida en Overlay OBS ([`assets/overlays/alerts/alerts.html`](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/alerts/alerts.html)):**
  - **Animaciones de Entrada**: `fade_in` (mostrar gradualmente), `slide_up` (deslizar hacia arriba), `slide_down` (deslizar hacia abajo), `slide_left` (deslizar desde derecha), `slide_right` (deslizar desde izquierda), `zoom_in` (acercar), `bounce_in` (rebotar con aceleración elástica).
  - **Animaciones de Salida**: `fade_out` (desvanecer), `slide_down` (deslizar hacia abajo), `slide_up` (deslizar hacia arriba), `slide_left` (deslizar a la izquierda), `slide_right` (deslizar a la derecha), `zoom_out` (alejar), `bounce_out` (rebotar salida).
  - Duraciones personalizables en segundos para la animación de inicio y la animación de cierre de forma independiente.
  - Sincronización precisa con el cierre de la alerta y el ACK por WebSocket (`minikick:finish_alert` y `alert_finished`).

- **Control Granular del Contenedor de Alerta ([`frontend/components/alerts/event_card.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py)):**
  - Selector de color de fondo (`picker_bg_color`) y slider de opacidad (0 a 100%).
  - Control de radio de esquinas redondeadas en píxeles (`border_radius`, 0 a 60 px).
  - Controles de espacio de relleno interior (`padding_px`) y espacio entre elementos (`spacing_px`) con spinboxes dedicados.
  - Interruptor directo para activar/desactivar la sombra profunda del contenedor (`box_shadow`).

- **Diseño de Texto y Tipografía Avanzada:**
  - Selector de peso/grosor tipográfico (`font_weight`): Normal (400), Seminegrita (600), Negrita (700) y Extra negrita (800).
  - Selector de alineación de texto con control segmentado de 4 modos: Izquierda, Centro, Derecha y Justificado.
  - Interruptor dedicado de sombra de texto (`text_shadow`) para garantizar contraste sobre fondos de videojuegos y directos.
  - Paleta de color de texto y color de detalle/resaltado para usuarios, cantidades y tokens dinámicos.

- **Previsualización en Vivo Adaptada ([`frontend/components/alerts/alert_mockup.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/alert_mockup.py)):**
  - El canvas de mockup ahora refleja en tiempo real el color de fondo con el canal alfa exacto (`bg_opacity`), curvatura de esquinas redondeadas (`border_radius`), sombra de caja (`box_shadow`), grosor tipográfico (`font_weight`) y sombra de texto (`text_shadow`).

---

## 2. Mejoras

- **Eliminación de Estilos Estáticos Rígidos en favor de SoR y Composición:**
  - Se suprimió la dependencia restrictiva del selector `style` (`compact`, `glass`, `minimal`, `sticker`), sustituyéndolo por composición directa de propiedades CSS en el overlay y atributos tipados en el modelo de datos.
- **Modelo de Dominio Tipado y Escalable ([`backend/models/alerts_models.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/models/alerts_models.py)):**
  - Dataclass `AlertConfig` y DTO `AlertConfigData` con slots y valores predeterminados seguros para todos los nuevos campos: `animation_in`, `animation_in_duration`, `animation_out`, `animation_out_duration`, `bg_color`, `bg_opacity`, `border_radius`, `padding_px`, `spacing_px`, `box_shadow`, `font_weight`, `text_shadow`.
- **Evolución de Esquema y Persistencia SQLite $\mathcal{O}(1)$ ([`backend/database/database_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/database_manager.py) & [`alerts_storage.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/alerts_storage.py)):**
  - Agregadas las 12 nuevas columnas al `CREATE TABLE IF NOT EXISTS alert_configs` y al diccionario de migración automática `expected_columns["alert_configs"]`.
  - Mecanismo de auto-actualización sin pérdida de datos en bases de datos ya existentes mediante `ALTER TABLE ADD COLUMN`.
  - Persistencia de configuraciones indexadas por clave primaria compuesta `(platform, alert_type)`.
- **Estandarización Estricta de Internacionalización (i18n):**
  - 100% de los nuevos textos, etiquetas de sección, opciones de animaciones, pesos tipográficos y descripciones fueron integrados en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json). Cero cadenas de texto hardcodeadas en código.

---

## 3. Correcciones

- **Compatibilidad Hacia Atrás en Carga de Configuraciones:**
  - Se corrigió el riesgo de excepción por desempaquetado o campos ausentes en `AlertConfig.from_dict` y `load_all()` proveyendo valores por defecto de fábrica en caso de configuraciones generadas en versiones previas.
- **Sincronización de Dismissal en Overlay Web:**
  - Se corrigió el tiempo de remoción del contenedor en `alerts.html`, el cual anteriormente usaba un tiempo fijo de 350ms, calculando ahora dinámicamente `outDurationSec * 1000` ms para respetar animaciones de salida largas o cortas sin cortes abruptos.
