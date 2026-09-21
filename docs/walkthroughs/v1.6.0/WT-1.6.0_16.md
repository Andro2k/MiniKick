# Walkthrough WT-1.6.0_16: Rediseño Estructural y Visual Inspirado en Antigravity

## Novedades

1. **Nuevo Componente `SectionHeader` y Divisores de Tarjeta**:
   - Se introdujo el componente reusable `SectionHeader` en `frontend/widgets/block_widget.py` para encabezados de categoría de configuración con tipografía nítida y espaciado proporcional.
   - Se añadió el método `add_separator()` en `ModernCard` para separar visualmente múltiples filas de ajuste dentro de un mismo contenedor mediante líneas sutiles de 1px (`#282A32`).

2. **Categorización Estructurada en `SettingsView` (Estilo Antigravity)**:
   - Reorganización completa de la vista de ajustes en bloques temáticos discretos:
     - **Sistema y Apariencia**: Idioma, tamaño de fuente global, navegador web y ejecución en segundo plano.
     - **Dispositivos de Audio**: Salida de música (YouTube) y salida de voz (TTS).
     - **Plataformas y Conexiones**: Canales de Kick, Twitch, YouTube Live y TikTok Live con botones interactivos de conexión y desconexión rápida.
     - **Copia de Seguridad**: Exportación e importación modular de configuraciones.
     - **Actualizaciones y Soporte**: Actualizaciones automáticas, notas de versión y reporte de bugs.

3. **Botón Sólido de Acción Crítica (`action_danger_solid`) para Desconexión**:
   - Nuevo rol de botón en `theme.py` que emula el botón rojo distintivo de Antigravity (`#E03131` con hover `#EF4444` y texto blanco `#FFFFFF`).
   - Aplicado directamente al estado conectado de todas las plataformas (Kick, Twitch, YouTube, TikTok) para la acción de desconexión, eliminando la necesidad de una tarjeta redundante de peligro.

4. **Líneas Divisoras de Tarjeta de Borde a Borde (Seamless Cards)**:
   - Los divisores dentro de cada `ModernCard` ahora se extienden al 100% del ancho conectándose perfectamente de borde a borde con la tarjeta (`#282A32`).
   - Se desacopló el margen del contenedor asignando `margin=0, spacing=0` a `ModernCard` y gestionando el espaciado interior limpiamente dentro de `SettingRow` (`contents_margins=(16, 12, 16, 12)`).

5. **Cero `setStyleSheet` Sueltos (QSS Estricto y Centralizado)**:
   - Eliminación total de llamadas manuales a `setStyleSheet` en componentes y vistas.
   - Toda regla visual se rige estrictamente por roles de QSS centralizados en `frontend/common/theme.py`.

6. **Estandarización Semántica de Tokens de Margen y Espaciado (`MARGIN_*` y `SPACING_*`)**:
   - Se crearon tuplas semánticas de márgenes (`MARGIN_SETTING_ROW`, `MARGIN_SETTING_ROW_COMPACT`, `MARGIN_HERO`, `MARGIN_PLATFORMS_GRID`, `MARGIN_SECTION_HEADER`, `MARGIN_TAB_BAR`, `MARGIN_SCROLL_CONTENT`, `MARGIN_CHIP`, `MARGIN_TAG_BADGE`, `MARGIN_V_2XS`, `MARGIN_H_LG`).
   - Se reemplazaron todos los valores numéricos sueltos y el uso incorrecto de constantes de espaciado en llamadas `setContentsMargins` y `setSpacing` a lo largo de todos los componentes (`SettingRow`, `SectionHeader`, `ModernCard`, `FlowLayout`, `SearchableComboBox`, `InspectorWidgets`, `VariantsTabBar`, `BotMutePanel`, `OverlaySettingsPanel`, `PiperVoicesDialog`, `ImportBackupDialog`).

7. **Conexión Continua de Divisores y Compactación en `DashboardView`**:
   - `hub_card` (Hub de Plataformas) y `card_channel_profile` (Perfil del Canal) ahora operan con `margin=MARGIN_NONE, spacing=SPACING_NONE` y divisores generados por `add_separator()`, permitiendo que la línea divisora conecte al 100% de borde a borde con el card.
   - Eliminación del doble padding en la fila de autoinicio usando `MARGIN_SETTING_ROW_COMPACT`.
   - Empaquetado compacto de `platforms_container` (`MARGIN_PLATFORMS_GRID`) y `PlatformStatusCard` (`MARGIN_MD` y `SPACING_SM`).
   - Sección de analíticas y tarjetas inferiores (`top_commands_card`, `modules_card`, `bar_card`, `disconnected_container`) compactadas con `MARGIN_MD` y `SPACING_SM`, optimizando el espacio vertical y eliminando áreas muertas.

8. **Estandarización Estructural y Compactación en `ChatView` y Subpaneles**:
   - `ChatView`: Reducción del espaciado entre el panel lateral de pestañas y el visor de chat en vivo de `SPACING_XL` (24px) a `SPACING_MD` (12px), optimizando la distribución horizontal sin huecos desproporcionados.
   - `ChatTtsSettingsPanel`: Modularizado en 3 tarjetas estándar `ModernCard(margin=MARGIN_NONE, spacing=SPACING_NONE)` con `SectionHeader` y divisores `add_separator()` continuos de borde a borde:
     1. Configuración General de TTS (activación, lectura de apodo, comandos, prefijo, volumen y velocidad).
     2. Filtro de Plataformas (Kick, Twitch, YouTube, TikTok).
     3. Roles y Voces (Proveedor, voz general y asignación específica por roles: Broadcaster, Moderador, VIP, Suscriptor).
   - `BotMutePanel`: Organizado con `SectionHeader` claros y tarjetas desacopladas: comandos de moderación con `add_separator()`, lista compacta de bots silenciados y lista de palabras prohibidas con `MARGIN_MD` y `SPACING_SM`.
   - `ChatOverlaySettingsPanel`: Estandarizado con `role="tab_panel"`, y tarjetas de Estilo, Distribución, Visibilidad y Vista Previa calibradas con `MARGIN_MD` y `SPACING_SM`.
   - `ChatDisplayPanel`: Ajustado a márgenes limpios `MARGIN_MD` y espaciado `SPACING_SM`.

---

## Mejoras

1. **Paleta de Colores y Superficies Refinadas**:
   - Migración de gradientes densos hacia superficies mate elegantes idénticas a Antigravity:
     - Superficie base (Root): `#111215` (obsidiana profunda).
     - Superficie lateral (Sidebar): `#141519`.
     - Superficie de tarjetas (Cards): `#18191E` con bordes sutiles de 1px (`#282A32`).
     - Elementos activos (Pill selection): `#26282E` con micro-borde `rgba(255, 255, 255, 0.08)`.
     - Texto de alta legibilidad: `#F4F4F6` para títulos y `#9CA3AF` para subtítulos descriptivos.

2. **Pestañas de Navegación Lateral (Sidebar Pill Navigation)**:
   - Pestañas con esquinas redondeadas tipo píldora (`border-radius: 8px`).
   - Estado activo con fondo sólido `#26282E`, texto blanco e icono blanco brillante para máxima claridad visual.
   - Encabezados de sección del sidebar en mayúsculas discretas (`#6E7382`, 11px, `letter-spacing: 0.5px`).
   - Tarjeta de perfil inferior estilizada con nombre en blanco negrita y subtítulo muted.

3. **Controles de Formulario y Desplegables Modernizados**:
   - `QComboBox` rediseñado con fondo `#202228`, bordes `#343741`, chevron sutil y menú desplegable oscuro flotante con selección pill.
   - Barras de desplazamiento (`QScrollBar`) ultra-delgadas de 8px, transparentes y no invasivas.

4. **Internacionalización y Cero Hardcoded Strings**:
   - Todas las etiquetas de secciones, títulos de advertencia y botones de la zona de peligro fueron integrados en `locales/es.json` y `locales/en.json` bajo `settings.sections.*` y `settings.danger.*`.

5. **Tokenización 100% Completa en Constructores QSS**:
   - Erradicación del 100% de los códigos hexadecimales embebidos ("hardcoded") en las funciones generadoras de QSS (`_build_button_qss`, `_build_input_qss`, `_build_surface_qss`, `_build_complex_qss`).
   - Se definieron tokens semánticos reutilizables para estados hover/active/focus de superficies, bordes de plataformas (Twitch, YouTube, TikTok), brillo superior (`COLOR_BORDER_TOP_SHINE`) y acciones sutiles de peligro/acento.

6. **Soporte de Márgenes Semánticos en `SliderRow`**:
   - Se extendió el constructor de `SliderRow` en `frontend/widgets/block_widget.py` para aceptar el parámetro `contents_margins: tuple = MARGIN_SETTING_ROW`, permitiendo alineación pixel-perfect idéntica a `SettingRow`.

8. **Calibración de Altura de `SectionHeader` y Soporte `first=True`**:
   - Eliminado el `padding-top: 14px` rígido de QSS en `QLabel[role="section_header"]`, centralizando el control de espaciado en tokens de margen semánticos.
   - Implementado `MARGIN_SECTION_HEADER_FIRST = (2, 0, 2, 4)` y parámetro `first: bool = False` en `SectionHeader`, eliminando el espacio vertical vacío desproporcionado en el primer encabezado de las pestañas ("Comandos de Moderación en Chat", "Sistema y Apariencia").

10. **Unificación Arquitectural de Tarjetas Desplegables (`ExpandableCard`)**:
   - Se introdujo la clase base modular `ExpandableCard` en `frontend/widgets/block_widget.py`, unificando la cabecera interactiva, interruptor maestro, icono, botón chevron y contenedor desplegable.
   - `ExpandableSettingCard` (en `SpamView`) y `WidgetCard` (en `WidgetsView`) ahora heredan directamente de `ExpandableCard`, eliminando más de 120 líneas de código repetido y garantizando consistencia total.

11. **Línea Divisora Continua de Borde a Borde en Tarjetas Desplegables**:
   - `ExpandableCard` implementa un `ModernDivider` a nivel de `main_layout` posicionado entre la cabecera y el cuerpo.
   - Al expandirse la tarjeta, la línea divisora de 1px (`#282A32`) se une de borde a borde con el marco exterior de la tarjeta sin los espacios flotantes que existían previamente en `WidgetCard`. Al colapsarse, el divisor se oculta automáticamente.

12. **Compactación y Estandarización de Márgenes en `WidgetsView` y `SpamView`**:
   - Se redujo el espaciado de `body_layout`, `columns_layout` y `col1_layout`/`col2_layout` de `SPACING_XL` (24px) a `SPACING_MD` (12px), eliminando huecos vacíos y alineando ambas vistas a la estética compacta de Antigravity.

---

## Correcciones

- Se corrigió la regla QSS para contenedores dentro de pestañas (`QTabWidget QFrame[role="tab_panel"]`) en `frontend/common/theme.py`, evitando que afectara a las tarjetas hijas `ModernCard[role="card"]`, permitiendo que éstas mantengan su fondo mate y bordes bien definidos.
- Se corrigió `SliderRow` en `frontend/widgets/block_widget.py` que carecía del parámetro `contents_margins`, evitando fallos de inicialización con configuraciones de espaciado compacto.
- Se corrigió el alto excesivo y desalineación vertical del primer `SectionHeader` mediante `MARGIN_SECTION_HEADER_FIRST` y `first=True`.
- Se corrigió la asimetría del scrollbar en pestañas removiendo el padding interno de `QTabWidget::pane` e implementando `MARGIN_TAB_PANEL`.
- Se eliminó el divisor flotante con márgenes internos en `WidgetCard`, reemplazándolo por el divisor continuo conectado de `ExpandableCard`.
- Se resolvieron inconsistencias en componentes donde se utilizaban tokens de espaciado (`SPACING_*`) en lugar de márgenes (`MARGIN_*`) para llamadas de `setContentsMargins`.
- Cero regresiones o excepciones en toda la suite de pruebas (38 tests pasando exitosamente).
