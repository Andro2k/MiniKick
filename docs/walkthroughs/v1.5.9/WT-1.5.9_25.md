# Walkthrough WT-1.5.9_25: Personalización de Dimensiones de Alertas y Contención Interna de Multimedia

## Novedades

- **Control de Dimensiones del Contenedor (`card_width` y `card_height`)**:
  - Se añadieron campos de personalización en la sección de diseño de cada alerta (`AlertEventCard`):
    - `spin_card_width`: control numérico con rango de `200` a `1920 px` (por defecto `560 px`).
    - `spin_card_height`: control numérico con rango de `0` a `1080 px` donde `0` representa valor especial `"Auto"`.
  - Persistencia de ambos campos en la base de datos SQLite (`database_manager.py` con migración automática y `alerts_storage.py`).
  - Modelos de datos (`AlertConfig`, `AlertConfigData`) actualizados para incorporar `card_width` y `card_height` en su ciclo de vida y serialización.

- **Contención Integral del Multimedia Dentro de la Tarjeta**:
  - En `assets/overlays/alerts/alerts.html`, el elemento `.media-box` fue reubicado **dentro** de `.alert-card` en lugar de flotar externamente.
  - La tarjeta (`.alert-card`) contiene tanto el elemento multimedia (imagen, vídeo, iframe) como el texto (`.alert-content-box`) y la barra de progreso, garantizando un marco unificado.

## Mejoras

- **Eliminación de Formas Circulares en Diseños Laterales (`side` y `side_right`)**:
  - Se eliminó el estilo forzado `border-radius: 50%` en los layouts laterales.
  - El contenedor multimedia en layouts laterales ahora utiliza bordes rectangulares redondeados elegantes (`border-radius: 12px` - `14px`), adaptándose orgánicamente al contenido visual del streamer.
  
- **Sincronización en Tiempo Real del Mockup Preview**:
  - Se actualizó el widget `AlertOverlayMockupWidget` (`alert_mockup.py`) para reflejar en tiempo real las dimensiones configuradas (`card_width` y `card_height`) mediante la función geométrica proporcional `_get_card_geometry`.
  - Los layouts `above`, `below`, `side` y `side_right` dibujan ahora el contenedor multimedia y sus glifos estrictamente dentro de los límites de la tarjeta con esquinas redondeadas.

- **Internacionalización (i18n) Estricta**:
  - Se añadieron las claves `card_width`, `card_width_desc`, `card_height`, `card_height_desc` y `auto` en `locales/es.json` y `locales/en.json`, evitando textos duros o fallbacks en el código.

## Correcciones

- **Corrección de Desbordamiento y Desalineación en el Overlay**:
  - Corregido el problema donde imágenes o vídeos de gran tamaño o vídeos desfasados en margen sobresalían del marco de fondo de la alerta.
  - Ajuste dinámico de los márgenes entre multimedia y textos dentro del contenedor según la propiedad `spacing_px`.
- **Compatibilidad con Altura Automática**:
  - Cuando `card_height` es `0` (`Auto`), el contenedor de la alerta se adapta dinámicamente al contenido textual y multimedia sin cortes (`height: auto`).
