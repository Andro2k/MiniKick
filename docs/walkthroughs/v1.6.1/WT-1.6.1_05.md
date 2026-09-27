# Walkthrough 1.6.1_05: Sincronización Dinámica de Release Notes y Persistencia O(1) de Insignias

## Novedades

- **Parser Dinámico de Notas de Versión (`parse_release_notes`)**:
  Se implementó un analizador sintáctico en un solo paso que extrae directamente las novedades de [Release_Notes_v1.6.1.md](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.6.1/Release_Notes_v1.6.1.md) para alimentar la ventana modal de bienvenida y las insignias del menú. Se eliminó la necesidad de declarar manualmente las mejoras versión por versión en el código fuente.

- **Estándar Canónico de 4 Columnas en Release Notes**:
  Se formalizó la columna obligatoria `Sección` en la tabla de `## Novedades` (`| Sección | Característica | Descripción | Beneficio para el Usuario |`) en las directrices de [.agents/rules/minikick.md](file:///c:/Users/TheAn/Desktop/python/Kick/.agents/rules/minikick.md). Esto mapea de forma determinista cada funcionalidad al botón correspondiente de la barra lateral (`Chat`, `Widgets`, `Comandos`, `Timers`, `Music`, `Developer`, `Dashboard`, `Settings`).

- **Soporte Dual en `WhatsNewDialog`**:
  El diálogo de bienvenida ahora puede recibir y renderizar tanto cadenas de texto directas generadas dinámicamente por el parser de notas de versión como claves del sistema de traducción `i18n` como mecanismo de respaldo.

- **Visualización Integral de Novedades con Desplazamiento Suave**:
  Se eliminó el límite artificial de 3 tarjetas, permitiendo que la ventana modal presente todas las novedades declaradas en la tabla de Release Notes mediante un `QScrollArea` estilizado y sin bordes. Esto garantiza que sin importar si una versión tiene 5, 8 o más novedades, la ventana modal conserve dimensiones estables y proporciones visuales óptimas.

- **Resolución Directa de Secciones (Zero Boilerplate)**:
  Dado que la columna `Sección` en los Release Notes contiene la denominación directa del módulo (`Widgets`, `Comandos`, `Chat`, `Developer`, `Dashboard`), se eliminó el diccionario intermedio de normalización `_CANONICAL_SECTIONS`. El parser vincula la sección directamente a las pestañas y al despachador de iconos en tiempo constante $\mathcal{O}(1)$.

- **Eliminación Definitiva de Items en i18n (Single Source of Truth Puro)**:
  Se eliminaron por completo las tarjetas e items de texto dentro de `es.json` y `en.json`. Los archivos de localización únicamente conservan las etiquetas de interfaz de la ventana modal (`dialog.btn_start`, `dialog.btn_got_it`, etc.) y el tooltip de ayuda. Las novedades, títulos y descripciones son leídos exclusivamente al vuelo desde los Release Notes oficiales.

---

## Mejoras

- **Optimización de Persistencia $\mathcal{O}(1)$ Atómica (`whats_new_state`)**:
  Se unificó todo el subsistema de bienvenida e insignias en **1 sola clave atómica** en SQLite: `whats_new_state`. Se eliminaron las claves redundantes `last_seen_app_version` y `seen_badges_vX.X.X`. El estado completo se almacena como un único objeto JSON (`{"version": "...", "modal_seen": bool, "seen": [...]}`). Con esto, la base de datos mantiene exactamente 1 fila constante $\mathcal{O}(1)$ para todo el sistema de novedades, eliminando cualquier riesgo de desincronización entre la modal y las insignias del menú.

- **Purga Automática de Migración (`delete_key_prefix`)**:
  Se incorporó el método `delete_key_prefix` en [SQLiteSettingsStorage](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/settings_storage.py), eliminando de la base de datos local cualquier clave residual de esquemas anteriores en una sola consulta indexada.

- **Asignación Contextual de Iconos**:
  El motor clasifica cada novedad asociándola a su icono oficial del sistema (`dialog-filled.svg`, `widget-add-filled.svg`, `chat-square-code-filled.svg`, `file-text-filled.svg`, etc.), con soporte heurístico para casos especiales como filtros de spam (`shield-filled.svg`) y conexiones de overlay (`globe-filled.svg`).

---

## Correcciones

- **Corrección de Duplicación de Prefijo en Título ("vvX.X.X")**:
  Se corrigió el formateo del título en [WhatsNewDialog](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/whats_new_dialog.py) aplicando `lstrip("vV")` sobre la variable de versión antes de insertarla en la plantilla `title_update`, previniendo que apareciera `"vv1.6.0"` cuando `APP_VERSION` ya incluía el prefijo `"v"`.

- **Estabilidad en el Posicionamiento de Insignias de la Barra Lateral**:
  Se corrigió el desfasaje visual observado en el arranque inicial donde las insignias circulares naranjas "N" se posicionaban sobre los iconos de la izquierda antes del primer ciclo de renderizado. Se implementó un filtro de eventos `eventFilter` (`QEvent.Type.Resize`) en los botones del sidebar, cálculo seguro de ancho con valor de respaldo `expanded_width - 16` y refresco automático en `showEvent`.

- **Prevención de Crecimiento Infinito de la Tabla `settings`**:
  Se solventó el riesgo de fragmentación y crecimiento descontrolado de claves temporales de navegación en la base de datos SQLite entre actualizaciones sucesivas.

- **Resiliencia ante Entornos sin Carpeta `docs/`**:
  Si la aplicación se ejecuta empaquetada o en un entorno donde los archivos Markdown de documentación no están presentes, [WhatsNewService](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/whats_new_service.py) conmuta de forma segura al catálogo de respaldo sin emitir excepciones ni bloquear la carga de la ventana principal.
