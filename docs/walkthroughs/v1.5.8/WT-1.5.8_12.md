# Walkthrough: WT-1.5.8_12 - Modularización de AlertsView y Corrección de sidebar_card

## Resumen Ejecutivo

Siguiendo el patrón arquitectónico de [music_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/music_view.py) y [frontend/components/music/](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music), se modularizó completamente `AlertsView`, extrayendo sus componentes visuales hacia un nuevo paquete desacoplado en `frontend/components/alerts/`. Asimismo, se eliminó de raíz el problema visual donde el `sidebar_card` se cortaba en el borde inferior.

---

## 1. Componentes Extraídos (`frontend/components/alerts/`)

Se crearon 6 módulos cohesivos con responsabilidad única (SRP), sin comentarios internos (únicamente la ruta en la línea 1) y con estricto cumplimiento de roles de diseño:

1. **[responsive_stack.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/responsive_stack.py)**:
   - `ResponsiveStackedWidget(QStackedWidget)`: Gestiona dinámicamente el `minimumSizeHint()` y `sizeHint()` delegando al widget actualmente visible para evitar saltos o desbordamientos.
2. **[variant_item.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/variant_item.py)**:
   - `AlertVariantListItem(QFrame)`: Componente de ítem individual de lista para cada variante de alerta (Kick y Twitch) con icono temático, título `role="body"`, descripción `role="caption"` autoajustable y punto indicador de estado activo.
3. **[sidebar_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/sidebar_panel.py)**:
   - `AlertsSidebarPanel(ModernCard)`: Panel lateral desacoplado ("Variantes de Alerta").
   - **Solución al corte visual**: Se eliminó la `QScrollArea` interna anidada que limitaba artificialmente la altura de la tarjeta a ~190px y provocaba que el 5º ítem ("Raid / Host") y el 6º ítem ("Bits / Cheer") quedaran cortados o invisibles.
   - Cuenta con ancho fijo de `240px` y `QSizePolicy.Policy.Expanding` vertical.
4. **[event_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py)**:
   - `AlertEventCard(QWidget)`: Panel editor detallado para la variante activa. Incluye cabecera en 2 filas (título + botón probar; estado de cambios sin guardar + descartar + guardar), sección de ajustes generales y sección multimedia/audio.
5. **[overlay_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/overlay_card.py)**:
   - `AlertsOverlayCard(ModernCard)`: Tarjeta superior de URL de OBS con botones de copiar y previsualizar, con soporte de orientación responsiva horizontal/vertical.
6. **[__init__.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/__init__.py)**:
   - Exportaciones limpias de todos los componentes del paquete.

---

## 2. Refactorización de AlertsView (`frontend/views/alerts_view.py`)

- **Reducción masiva de líneas**: De 764 líneas monolíticas a ~190 líneas de orquestación de alto nivel (idéntico a `music_view.py`).
- **Separación de Responsabilidades (SoR)**: La vista ya no construye ni dibuja componentes internos manualmente; simplemente los ensambla y conecta sus señales con el controlador.
- **Sin comentarios sueltos**: Únicamente `# frontend\views\alerts_view.py` en la línea 1.
- **Cero hardcoding y cero `setStyleSheet` suelto**: 100% de los textos e interfaces usan `i18n.get(...)` y roles de `theme.py`.
