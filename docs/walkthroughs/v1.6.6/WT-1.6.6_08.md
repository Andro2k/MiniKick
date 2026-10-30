# Walkthrough Técnico — MiniKick v1.6.6 (Paso 08)

Unificación visual de la interfaz y corrección del chat desacoplado, a lo largo de los parches `0006` a `0012`. El panel de Configuración pasa a una columna centrada con ancho máximo y jerarquía tipográfica limpia (sin íconos junto a los títulos), ese mismo estilo se extiende a las demás pantallas con filas de ajustes y a la vista de Widgets, la ventana flotante del chat deja de depender de la ventana principal, y todas las vistas comparten ahora un ancho máximo centrado para no estirarse en monitores grandes.

Los parches `0006` a `0011` ya están integrados en `release/v1.6.6`; `0012` aplica limpio sobre `95a45db`, el HEAD con el que se validó. Cada parche trae su propio test, y se comprobó que los tests de comportamiento nuevo fallan contra el código anterior.

| Parche | Contenido |
| --- | --- |
| `0006` | Panel de Ajustes centrado, sin íconos y con jerarquía tipográfica |
| `0007` | Filas limpias en Chat → Ajustes de Voz |
| `0008` | Filas limpias en Música (Ajustes, Comandos, Reproductor) y Chat → Silenciados |
| `0009` | Banners de URL para OBS sin ícono (Chat, Alertas, Recompensas) |
| `0010` | Vista de Widgets con estilo de Configuración |
| `0011` | Ventana flotante del chat independiente de la app |
| `0012` | Ancho uniforme y centrado en todas las vistas |

---

## Novedades

- **Columna centrada con ancho máximo en `BaseView`** (`0006`, `0012`): estructura `[spacer | columna | spacer]` con `maximumWidth`, `minimumWidth` opcional y `QSizePolicy.Expanding`. Ajustes usa 880 px (`Size.CONTENT_MAX_WIDTH`, mínimo 520 px con `CONTENT_MIN_WIDTH`). Desde `0012` el valor por defecto de `BaseView` es `Size.CONTENT_WIDE_MAX_WIDTH = 1440` para vistas de datos, de modo que cualquier vista nueva queda uniforme sin tocar nada; pasar `max_content_width=None` lo desactiva.
- **Rol QSS `setting_title`** (`0006`): texto principal claro (`NEUTRAL_050`, peso 500). En el theme, `body` y `caption` son ambos grises (`NEUTRAL_400`) y solo difieren en tamaño, por lo que un título en `body` no se distinguiría de su descripción.
- **Fábricas `SettingRow.minimal` y `SliderRow.minimal`** (`0007`): filas sin ícono, con título `setting_title` y descripción `caption`. Reemplazan 15 bloques repetidos en `SettingsView` mediante el helper `_setting_row`.
- **Parámetros opt-in en componentes compartidos**: `SettingRow` y `SliderRow` aceptan `title_role` y `desc_role`; `ExpandableCard` acepta `title_role`, `desc_role` y `header_margins`. Los valores por defecto no cambian, por lo que Alertas y Anti-Spam no se ven afectadas.
- **`ChatView.close_floating_chat()`** (`0011`): cierra la ventana flotante y devuelve el panel de chat a la vista principal.
- **Tests nuevos**: `test_centered_view_layout`, `test_chat_voice_rows`, `test_setting_rows_consistency`, `test_obs_banner_rows`, `test_widgets_view_layout`, ampliación de `test_chat_detached_window` y `test_view_width_uniformity`.

## Mejoras

- **Configuración General** (`0006`): sin íconos en los 15 ajustes, categorías con `section_header`, títulos con `setting_title` y descripciones con `caption`. Se mide centrado exacto a distintos anchos (880 px con 1681 px de área visible, fluido hasta 520 px).
- **Chat → Ajustes de Voz** (`0007`): 4 `SettingRow`, 2 `SliderRow` y 6 `VoiceSettingRow` con el nuevo estilo. A `VoiceSettingRow` se le eliminan los parámetros `icon_name` e `icon_color` (solo se usaba aquí). Los toggles de plataforma conservan sus logos de marca.
- **Música y Silenciados** (`0008`): Ajustes (2 filas y 4 deslizadores), Comandos (7 filas; se quita el ícono de `_COMMANDS_CONFIG`), volumen del reproductor y 2 filas de Chat → Silenciados.
- **Banners de URL para OBS** (`0009`): la misma fila con ícono de enlace aparecía en tres pantallas; se unifican las tres.
- **Widgets** (`0010`): columna única centrada en lugar de dos columnas con `resizeEvent`; `WidgetCard` sin ícono (parámetro `icon_name` eliminado), con título `setting_title`, descripción `caption` y margen de encabezado `MRG_LRG`. Se elimina `create_two_column_container`, que quedaba sin usos.
- **Ancho uniforme** (`0012`): Logs, Música, Recompensas, Comandos, Temporizadores, Chat, Panel de Control, Alertas e Info del Stream quedan centrados en 1440 px; Ajustes y Widgets, en 880 px. La columna usa el 100% del ancho hasta llegar al tope y solo entonces los `QSpacerItem` `Expanding` (stretch 0) reparten el sobrante a partes iguales. Con la proporción anterior (1:100:1) se perdía ~2% del ancho en ventanas medianas.
- **Test de uniformidad** (`0012`): cubre las 11 vistas y falla si se añade una vista nueva sin registrarla.

## Correcciones

- **Ventana flotante del chat dependiente de la app** (`0011`): se creaba con `parent=self.window()`, por lo que Windows la trataba como ventana *owned*: se minimizaba, ocultaba y restauraba junto con la principal. Además, su `changeEvent` re-acoplaba el chat al detectar el minimizado, así que al minimizar la app el chat volvía solo a la vista principal. Ahora `_FloatingChatWindow` es una ventana de nivel superior sin dueño (se verifica sin `parentWidget` ni `transientParent`), con su propio botón en la barra de tareas, y minimizarla ya no la re-acopla.
- **Cierre ordenado en el apagado** (`0011`): sin padre, la ventana flotante ya no se destruye sola con la principal; `MainWindowCore._cleanup` la cierra al iniciar el apagado.
- **Editor de Alertas apilado con 1280 px** (`0012`, detectado durante el desarrollo): `AlertEventCard` apila sus 3 columnas con un umbral de `width < 1280` sobre su propio ancho. Con una columna de 1280 px la tarjeta mide ~1256 y dejaba de verse completa. El tope se fijó en 1440 px y un test de comportamiento protege ese caso.
- **`alerts_view`** (`0012`): el `invalidate` del layout apunta a `content_column` en lugar de `scroll_content`, coherente con la columna centrada.
- **Tests alineados con la nueva estructura**: `test_dashboard_profile_cards` y `test_antigravity_ui_theme` usan `content_column`; `test_antigravity_ui_theme` también adapta la firma de `WidgetCard` y el atributo `cards_layout`; `test_centered_view_layout` reemplaza la aserción "por defecto sin límite".

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `test_centered_view_layout` | 7 pasan |
| `test_view_width_uniformity` | 13 pasan (11 vistas, cobertura de vistas nuevas y editor de Alertas en 3 columnas) |
| `test_chat_voice_rows` / `test_setting_rows_consistency` / `test_obs_banner_rows` | 5, 4 y 3 pasan |
| `test_widgets_view_layout` | 6 pasan |
| `test_chat_detached_window` | 8 pasan (6 nuevos; 5 fallan contra el código anterior) |
| Suite completa sobre `95a45db`, antes y después de `0012` | Solo cambian los tests de `0012`; sin regresiones |
| Auditor de tokens de diseño | Sin hallazgos |

**Fallos preexistentes, sin relación con estos parches:**

- `test_antigravity_ui_theme.py::test_combobox_and_segmented_action_outlined_style` y `::test_dark_palette_and_popup_translucency_standards` fallan igual sin `0012`; son aserciones de QSS desactualizadas.
- `test_giphy_and_tts_filter.py` (3 pruebas) depende de la API key y la red de Giphy.
- `test_antigravity_ui_theme.py::test_settings_view_antigravity_structure`, `test_auto_update_setting.py` y `test_window_state_persistence.py` hacen *segmentation fault* en el entorno de validación (Qt Multimedia sin audio). Conviene correrlos en la máquina de desarrollo.

**No verificado:** el comportamiento real de minimizado y de `Win+D` en Windows (el entorno de validación es sin pantalla; se comprobó la causa, es decir, que la ventana ya no tiene dueño), y el aspecto con datos reales y la fuente Google Sans (las capturas de validación tienen tablas vacías y otra tipografía).

## Decisiones y salvedades

- **Dos anchos, uniformes por defecto**: 880 px para formularios y 1440 px para vistas de datos. Ajustar el segundo es cambiar `Size.CONTENT_WIDE_MAX_WIDTH`; por debajo de 1360 px el editor de Alertas deja de mostrar sus 3 columnas.
- **Escalado de Windows**: el tope se nota cuando el ancho lógico supera 1440 px (1920 px al 100%, o 2560 px). Un monitor de 1920 px al 125% equivale a 1536 px lógicos y apenas cambia.
- **Info del Stream**: con 1440 px su panel izquierdo mide ~617 px y las tarjetas Kick y Twitch se apilan por el umbral propio `< 680` de `quick_change_panel`; es el mismo comportamiento que ya tenía cualquier ventana de 1440 px.
- **Se quitó el re-acople automático al minimizar la ventana flotante**: ahora se vuelve a la vista principal con el botón de reacoplar o cerrando la ventana. Con la ventana independiente ese hook habría hecho que `Win+D` re-acoplara el chat. Con "Ejecución en segundo plano" activo, el chat flotante sigue visible aunque la app quede en la bandeja.
- **Compatibilidad**: los parámetros nuevos son opt-in con los valores por defecto anteriores. `0012` cambia el valor por defecto de `BaseView`, por lo que las vistas que no deban centrarse deben pasar `max_content_width=None`.

## Pendiente (no incluido)

- **Tarjetas expandibles de Anti-Spam y de eventos de Alertas**: usan el mismo `ExpandableCard`; llevar el estilo limpio ahí es pasar `title_role`, `desc_role` y `header_margins`, pero conviene decidir antes si se quitan los íconos que ayudan a identificar cada filtro.
- **Diálogo de recompensas (paso 2)**: su fila de volumen convive con filas `h3` en un formulario; cambiar solo una quedaría desparejo.
- **Botones anchos dentro de tarjetas expandidas** de Widgets (por cómo `FlowLayout` reparte el espacio): ya ocurría antes; se arregla con un ancho máximo en esos botones.
- **Título "Historial del Chat" cortado** visto en `chat_overlay_preview.png`: no se investigó si es un artefacto de la captura o un truncado real al angostarse el panel.
- **Tests de QSS desactualizados** en `test_antigravity_ui_theme.py`: revisar las dos aserciones que ya fallaban.
