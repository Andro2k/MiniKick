# Walkthrough WT-1.5.8_38: Rediseño del Sistema de Alertas Estilo Twitch Alerts Studio (5 Diseños de Disposición, Modo Sticker Transparente, Tipografía y Colores Personalizables)

## 1. Contexto y Objetivos

Previamente, las alertas de MiniKick contaban con opciones de diseño visual limitadas a un formato horizontal tipo tarjeta/píldora con contenedor oscuro (`compact`, `glass`, `minimal`). El usuario solicitó dotar a MiniKick de la flexibilidad visual y libertad de diseño que ofrece **Twitch Alerts Studio**:
1. **Diferentes Disposiciones (Layouts)**: Ofrecer 5 variantes visuales entre multimedia y texto:
   - `above`: Imagen Arriba (Centrado / Clásico de Twitch).
   - `side`: Imagen Izquierda (Horizontal clásico).
   - `side_right`: Imagen Derecha (Horizontal invertido).
   - `below`: Imagen Abajo (Vertical invertido).
   - `overlay`: Texto Superpuesto directamente sobre el fondo del banner/multimedia.
2. **Estilo "Sticker / Transparente"**: Permitir alertas 100% transparentes, sin forzar una caja o tarjeta oscura, donde el multimedia o gif flota libremente sobre el gameplay y el texto se dibuja con una sombra paralela/borde pronunciado para máxima legibilidad.
3. **Personalización Tipográfica y Cromática Completa**:
   - Selector de fuentes (`Outfit`, `Inter`, `Roboto`, `Montserrat`, `Poppins`).
   - Tamaño de fuente ajustable (`font_size` de 14 a 48 px).
   - Alineación de texto (`left`, `center`, `right`).
   - Selector de color de texto (`text_color`, defecto `#FFFFFF`).
   - Selector de color de resaltado (`highlight_color`, defecto Kick `#53FC18`, Twitch `#9146FF`).
4. **Canvas de Previsualización en Vivo de Alta Fidelidad**:
   - Actualización de [`AlertOverlayMockupWidget`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/alert_mockup.py) con cuadrícula de transparencia de ajedrez (*checkerboard*) 16x16, permitiendo apreciar el modo sticker transparente y reflejando cambios en tiempo real.
5. **Persistencia Transparente y Sin Pérdida**:
   - Migración de esquema en SQLite mediante auto-upgrade en [`DatabaseManager`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py).
6. **Cumplimiento Estricto de i18n**:
   - Cero cadenas hardcodeadas; 100% de paridad en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json).

---

## 2. Cambios Implementados

### A. Capa de Modelos & Datos
- **[`backend/models/alert_models.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/models/alert_models.py)**:
  - Se añadieron los campos tipados `text_color: str = "#FFFFFF"`, `highlight_color: str = ""`, `font_family: str = "Outfit"`, `font_size: int = 24`, `text_align: str = "center"` al dataclass con slots [`AlertConfig`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/models/alert_models.py#L32-L68) y sus métodos [`to_dict()`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/models/alert_models.py#L46) y [`from_dict()`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/models/alert_models.py#L49).
- **[`backend/database/manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py)**:
  - Se actualizaron las sentencias `CREATE TABLE IF NOT EXISTS alert_configs` y `expected_columns["alert_configs"]` para realizar migraciones no destructivas `ALTER TABLE alert_configs ADD COLUMN ...` de forma automática al iniciar la app.
- **[`backend/database/alert_storage.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/alert_storage.py)**:
  - Se extendieron las consultas SQL en [`load_all()`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/alert_storage.py#L24), [`get_config()`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/alert_storage.py#L59) y [`save_all()`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/alert_storage.py#L87) para persistir y cargar los 5 nuevos campos visuales con cláusula `ON CONFLICT(platform, alert_type) DO UPDATE SET`.
- **[`backend/services/alerts/alert_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/alerts/alert_service.py)**:
  - En [`process_event()`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/alerts/alert_service.py#L28-L68), se incluyeron en el payload del evento despachado hacia el websocket del overlay OBS: `text_color`, `highlight_color`, `font_family`, `font_size` y `text_align`.

### B. Overlay Web para OBS ([`assets/overlays/alerts/alerts.html`](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/alerts/alerts.html))
- **Fuentes de Google**: Se agregaron fuentes Google modernas para streams (`Outfit`, `Inter`, `Roboto`, `Montserrat`, `Poppins`).
- **Reglas CSS para Nuevas Disposiciones**:
  - `.layout-below`: `flex-direction: column-reverse`, multimedia debajo del texto.
  - `.layout-side_right`: `flex-direction: row-reverse`, multimedia a la derecha y texto a la izquierda.
- **Reglas CSS para Modo Sticker**:
  - `.style-sticker .alert-card`: `background: transparent !important; border: none !important; box-shadow: none !important; backdrop-filter: none !important;`.
  - Sombra paralela en texto para visibilidad en pantalla: `text-shadow: 0 2px 10px rgba(0, 0, 0, 0.95), 0 0 4px #000000, 0 0 2px #000000;`.
  - Ocultación de barra de progreso en sticker.
- **Lógica de Renderizado Dinámico en JavaScript**:
  - Inyección dinámica de variables CSS `--accent-color` (color de resaltado del usuario o de plataforma) y `--text-main` (color del texto).
  - Aplicación de `fontFamily`, `fontSize`, `color` y `textAlign` al contenedor y títulos de la alerta.
  - Resaltado automático del nombre del usuario con etiqueta `<span class="highlight">` si la plantilla incluye `{user}`.

### C. Frontend Qt / PySide6
- **[`frontend/components/alerts/alert_mockup.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/alert_mockup.py)**:
  - Rediseño de [`AlertOverlayMockupWidget`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/alert_mockup.py#L9):
    - Lienzo de relación de aspecto cuadrada perfecta 1:1 (`side = min(w, h) - 4`, centrado dinámico `(cx, cy)`), con fondo de cuadrícula de transparencia de ajedrez (baldosas de 16x16px con `#11141C` y `#0B0D13`).
    - Tamaño adaptable (`minimumSize: 240x240`, `sizeHint: 360x360`), garantizando que se mantenga perfectamente cuadrado sin importar el ancho o escalado de pantalla.
    - Métodos especializados para los 5 layouts centrados en el lienzo cuadrado: `_draw_above_layout`, `_draw_below_layout`, `_draw_side_layout`, `_draw_side_right_layout`, `_draw_overlay_layout`.
    - Detección de `style_mode == "sticker"` para renderizar sin bordes ni cajas oscuras y con sombra de texto de contraste.
- **[`frontend/components/alerts/event_card.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py)**:
  - Reorganización de la sección "Diseño y Apariencia" en un diseño de dos columnas paralelas balanceado:
    - **Columna Izquierda (`col_controls`, flex-stretch 1)**:
      1. **Disposición**: [`ModernSegmentedControl`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/segmented_control.py) con 5 opciones e iconos direccionales (`arrow-up-filled.svg`, `arrow-left-filled.svg`, `arrow-right-filled.svg`, `arrow-down-filled.svg`, `box-multiple-2.svg`).
      2. **Estilos**: ComboBox con opciones `compact`, `glass`, `minimal` y `sticker`.
      3. **Tipografía**: ComboBox con las 5 fuentes Google (`Outfit`, `Inter`, `Roboto`, `Montserrat`, `Poppins`) con texto descriptivo explicativo.
      4. **Tamaño de Fuente**: Fila independiente con [`SettingRow`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py) con icono `text-size.svg`, título, texto descriptivo y spinbox (`spin_font_size`).
      5. **Alineación del Texto**: Fila independiente con [`SettingRow`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py) con icono `align-left-2.svg`, título, texto descriptivo y desplegable (`combo_align`).
      6. **Colores en 2 Columnas Verticales**:
         - Formato por columna: **Título** (con icono) -> **Descripción** -> **Controles** ([`ModernColorPicker`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/color_picker.py) con swatch, input hex y presets).
         - Columna izquierda: **Color del Texto**.
         - Columna derecha: **Color de Resaltado (`{user}`)**.
    - **Columna Derecha (`col_preview`, tamaño ajustado 380x380)**:
      - Título de vista previa centrado sobre el lienzo cuadrado [`AlertOverlayMockupWidget`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/alert_mockup.py), llenando uniformemente la altura total de la sección sin márgenes vacíos a los lados.
  - Eliminación de la tarjeta secundaria `card_typography`, unificando toda la configuración de apariencia visual junto a su previsualización en vivo.
  - Conexión reactiva completa con estado sucio (`_is_dirty`), autoguardado en botón de prueba y previsualización en vivo.

### D. Internacionalización (i18n)
- Se incorporaron las siguientes claves sincronizadas en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json):
  - `alerts.align`: `left`, `center`, `right`.
  - `alerts.layout`: `above`, `below`, `overlay`, `side`, `side_right`.
  - `alerts.style`: `compact`, `glass`, `minimal`, `sticker`.
  - `alerts.sections.typography`.
  - `alerts.fields`: `font_family`, `font_size`, `highlight_color`, `text_align`, `text_color`.

---

## 3. Análisis Big-O y Principios de Diseño

* **Separación de Responsabilidades (SoR)**: La capa de persistencia en SQLite (`alert_storage.py`) opera de forma puramente transaccional sin saber de rendering de UI ni OBS; el servicio de alertas (`alert_service.py`) procesa y encola eventos desacoplado del servidor websocket; el overlay web renderiza autónomamente en el navegador.
* **Eficiencia Algorítmica**:
  - Lectura y escritura en base de datos: Clave primaria compuesta `PRIMARY KEY (platform, alert_type)` con índice único en SQLite garantizando operaciones en $\mathcal{O}(1)$.
  - Caché en memoria en [`SQLiteAlertStorage`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/alert_storage.py): Diccionario con tupla `(platform, alert_type)` con tiempo de acceso en $\mathcal{O}(1)$.
  - Dibujado del lienzo de previsualización: Baldosas de ajedrez calculadas en un bucle simple de coordenadas fijas con complejidad $\mathcal{O}(W \cdot H / 256) \approx \mathcal{O}(1)$ acotado.
* **Open/Closed Principle (OCP)**: Se admiten nuevos estilos o disposiciones sin alterar la lógica de transporte de eventos del backend.

---

## 4. Verificación y Resultados

Se ejecutó la suite completa de pruebas unitarias cubriendo modelos, persistencia, UI e integridad i18n:
```bash
uv run pytest resources/tests/unit/services/test_alert_models.py resources/tests/unit/services/test_alert_storage.py resources/tests/unit/services/test_alert_service.py resources/tests/unit/ui/test_i18n_integrity.py resources/tests/unit/ui/test_alerts_ui.py
```
**Resultado:**
```text
============================= 26 passed in 1.66s ==============================
```
- Validación de integridad y paridad de claves i18n: 100% aprobado.
- Serialización y deserialización de modelos de alerta: 100% aprobado.
- Persistencia de 5 layouts y 4 estilos en SQLite: 100% aprobado.
- Ciclo de vida y reactividad en la interfaz gráfica (Qt): 100% aprobado.
