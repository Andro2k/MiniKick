# Walkthrough WT-1.5.8_22: Modelos de Disposición, Estilos Visuales y Previsualización Dinámica de Alertas

## 1. Resumen de la Implementación
Se implementó un sistema integral y configurable individualmente por evento para las alertas de stream (Kick y Twitch) compuesto por:
1. **3 Modelos de Disposición Espacial (Layouts):**
   - `above` (Arriba / Abajo): Composición vertical clásica con animación/imagen en la parte superior y tarjeta con datos debajo.
   - `side` (Al Lado / Compacto): Tarjeta horizontal compacta con insignia circular de neón a la izquierda y datos del usuario a la derecha (estilo neon card de referencia).
   - `overlay` (Superpuesto / Banner): Banner cinematográfico de ancho extendido con el elemento multimedia en segundo plano como telón y texto centrado en primer plano.
2. **3 Estilos Visuales (Themes):**
   - `compact` (Neón): Borde de acento vibrante y resplandor dinámico según plataforma/evento.
   - `glass` (Glassmorphism): Cristal esmerilado con desenfoque de fondo y borde sutil.
   - `minimal` (Minimalista): Tarjeta pulida con sombreado flotante sobrio.
3. **Previsualizador en Tiempo Real Vectorial ([alert_mockup.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/alert_mockup.py)):**
   - Widget nativo `AlertOverlayMockupWidget` de alto rendimiento ($\mathcal{O}(1)$ en QPainter sin el costo de inicializar WebEngine), integrado dentro de la tarjeta de configuración de cada evento en [event_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py).
   - Simula con precisión milimétrica la tipografía, insignias circulares, glifos Nerd Font (`\uf004` seguidor, `\uf005` suscripción, `\uf06b` regalo, `\udb80\udf90` cheer, `\udb81\udf5f` raid), bordes de neón y texto formateado interactivo.
4. **Persistencia y Migración Automática de Esquema SQLite:**
   - Columnas `layout TEXT DEFAULT 'above'` y `style TEXT DEFAULT 'compact'` añadidas a `alert_configs` con migración transparente en [manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py) y persistencia en [alert_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/alert_storage.py).
5. **Soporte Completo en Overlay OBS ([alerts.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/alerts/alerts.html)):**
   - Clases `.layout-above`, `.layout-side`, `.layout-overlay` y estilos `.style-compact`, `.style-glass`, `.style-minimal` con renderizado dinámico e icono SVG automático en modo lateral cuando no se define archivo multimedia personalizado.

---

## 2. Cambios por Módulo

### A. Modelos y Capa de Datos
- **[backend/models/alert_models.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/models/alert_models.py):**
  - Se añadieron `layout: str = "above"` y `style: str = "compact"` al dataclass `AlertConfig`.
  - Se actualizaron `from_dict()` y serialización.
- **[backend/database/manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py):**
  - Se añadieron columnas por defecto y se registraron en `expected_columns` de `alert_configs` para auto-migración SQLite sin pérdida de datos existentes.
- **[backend/database/alert_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/alert_storage.py):**
  - Métodos `load_all()`, `get_config()`, `save_config()` y `save_all()` actualizados para leer y escribir `layout` y `style`.

### B. Servicio de Alertas y Despacho
- **[backend/services/alerts/alert_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/alerts/alert_service.py):**
  - En `process_event()`, se incluyeron `"layout"` y `"style"` dentro del `payload` que se despacha vía WebSocket al navegador de OBS.

### C. Previsualizador en Vivo y UI de Alertas
- **[frontend/components/alerts/alert_mockup.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/alert_mockup.py):**
  - Componente vectorial `AlertOverlayMockupWidget` que dibuja en canvas QPainter con antialiasing los 3 layouts y estilos.
  - Insignia con glifo Nerd Font centrado y barra de progreso inferior de acento.
- **[frontend/components/alerts/event_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py):**
  - Tarjeta `card_appearance` distribuida en **2 columnas equilibradas**:
    - **Columna izquierda:** Control segmentado (`ModernSegmentedControl`) de disposición y selector desplegable (`NoWheelComboBox`) de estilo con sus descripciones.
    - **Columna derecha:** Título de previsualización y el widget `AlertOverlayMockupWidget` que responde inmediatamente a cada interacción.
  - Vinculación completa del flujo de guardado, descarte y comprobación de estado sucio (`_is_dirty`).

### D. Overlay HTML/CSS de Alertas ([assets/overlays/alerts/alerts.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/alerts/alerts.html))
- Estilos CSS para `.layout-above`, `.layout-side` y `.layout-overlay`.
- Estilos temáticos `.style-compact`, `.style-glass` y `.style-minimal`.
- En `showAlert(data)`, se asignan las clases dinámicas `layout-${layout} style-${style}` y se genera un icono estelar estilizado en modo lateral si no hay imagen personalizada.

### E. Internacionalización Estricta (i18n)
- **[locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) & [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json):**
  - Añadidas claves bajo `alerts`: `layout.title`, `layout.desc`, `layout.above`, `layout.side`, `layout.overlay`, `style.title`, `style.desc`, `style.compact`, `style.glass`, `style.minimal`, `sections.appearance`, `preview.*`.

---

## 3. Pruebas y Certificación
- Nuevas pruebas añadidas en:
  - `test_alert_event_card_layout_and_style_customization` en [resources/tests/unit/ui/test_alerts_ui.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_alerts_ui.py).
  - `test_alert_storage_layout_and_style_persistence` en [resources/tests/unit/services/test_alert_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/services/test_alert_storage.py).
- Ejecución completa de la suite de pruebas unitarias verificada sin regresiones.
