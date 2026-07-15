# WT-1.4.1_01: Ajustes de Layout, Correcciones de Overlay y Nuevo Tema Cyberpunk

Este documento detalla los cambios implementados para corregir problemas de diseño, escala y visualización en la interfaz del chat y los overlays de OBS, además de añadir el nuevo tema Cyberpunk e integrar Tabler Icons.

---

## 1. Ajuste de Layout Flexible (Flex) en Combos de Roles

### Componentes Afectados
* [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py)

### Descripción
* Se modificaron los comboboxes de selección de voz para los roles del chat (`broadcaster`, `moderator`, `vip`, `subscriber`).
* Anteriormente, al usar nombres de voces sumamente largos, la interfaz se desbordaba por el lado derecho.
* **Solución**: Se les aplicó una política de tamaño elástica (`QSizePolicy.Policy.Expanding`), un ancho mínimo de `100px` y un ancho máximo de `300px`. Ahora los combos se encogen y truncan con puntos suspensivos (`...`) si el espacio es reducido, y se expanden de forma proporcionada en pantallas grandes sin romper la estructura de las tarjetas.

---

## 2. Correcciones en el Lienzo del Chat (Overlay)

### Componentes Afectados
* [chat.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat.html)

### Descripción
* **Solución a Diseños Cortados**: Cambiamos la propiedad `overflow` de `#chat-container` de `hidden` a `visible` e incrementamos el relleno lateral (`padding: 16px 24px;` en el `body`). Esto evita que los efectos de sombra (neón) y los rabillos de los globos de diálogo (del tema `card.css`) se recorten en los bordes de la pantalla.
* **Escala de Etiquetas de Roles (Badges)**: Se modificó la regla CSS de `.badge` para usar un tamaño calculado relativo a la fuente elegida (`font-size: calc(var(--font-size) * 0.72)`) y espaciados basados en ems (`padding: 0.2em 0.5em;`). Ahora, al agrandar la letra en la configuración, los badges de rol se escalan proporcionalmente.

---

## 3. Integración de Tabler Icons y Nuevo Tema Cyberpunk

### Componentes Afectados
* [cyber.css](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/css/cyber.css) [NEW]
* [chat.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat.html)
* [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py)
* [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
* [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)

### Descripción
* **Nuevo Tema Cyberpunk**: Se creó la hoja de estilos `cyber.css` que provee un diseño HUD retro/cyberpunk con fuentes mono y bordes dinámicos que cambian de color según el color del usuario en el chat.
* **Integración de Tabler Icons**: Importamos Tabler Icons vía CDN en `chat.html`. Se adaptó la lógica del tema `cyber` para renderizar iconos vectoriales en lugar de caracteres emoji:
  * Streamer $\rightarrow$ `ti ti-video` (Cámara de vídeo)
  * Moderador $\rightarrow$ `ti ti-shield` (Escudo)
  * VIP $\rightarrow$ `ti ti-diamond` (Diamante)
  * Suscriptor $\rightarrow$ `ti ti-star` (Estrella)
  * Bot $\rightarrow$ `ti ti-robot` (Robot)
  * Por defecto $\rightarrow$ `ti ti-message-dots` (Mensaje)
  Los iconos vectoriales heredan dinámicamente el color del usuario (`--cyber-color`).
* **Traducciones y Opciones**: Se añadió la clave `"theme_cyber"` en las localizaciones de español e inglés, y se integró la opción "Retro Cyberpunk (Cyber)" al combobox del chat view.

---

## 4. Modularización en Pestañas de la Vista de Chat e Iconos de Sistema

### Componentes Afectados
* [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py)
* [settings_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py)
* Iconos de activos (`palette.svg`, `stopwatch.svg`, `text-size.svg`, `world.svg`)

### Descripción
* **Estructura en Pestañas**: Se reorganizó la vista del chat para agrupar todas las opciones de configuración de forma limpia mediante un widget de pestañas (`QTabWidget`). Las configuraciones se dividieron en tres áreas lógicas:
  * **Ajustes de Voz**: Selector de idioma, voz, volumen, comando de activación y prefijo.
  * **Silenciados**: El panel de usuarios silenciados (bots).
  * **Lienzo (Overlay)**: Todas las opciones del overlay de OBS (tema, tamaño de letra, temporizador de pantalla, bots y marcas de tiempo).
* **Modernización de Iconos**: Se removieron archivos obsoletos como `globe.svg` y se integraron nuevos iconos vectoriales del sistema (`world.svg`, `text-size.svg`, `stopwatch.svg`, `palette.svg`) para brindar una apariencia visual limpia y moderna en los menús de configuración general.

---

## 5. Descarte de Integración de Puntos con Música

### Nota de Arquitectura
* Se evaluó y propuso una funcionalidad para vincular un canje de puntos de canal de Kick que disparara automáticamente peticiones de canciones (`!sr`).
* **Estado**: Tras revisión, **esta característica fue descartada** para evitar sobrecomplejidad en la interacción de eventos y mantener la base de código limpia y centrada en los comandos de chat nativos. Las modificaciones correspondientes no fueron consolidadas en el producto final.

---

## 6. Unificación de Componentes de un Solo Uso (Inlining)

### Componentes Afectados
* [visual_positioner_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/visual_positioner_dialog.py)
* [log_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/log_view.py)
* [blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)
* `draggable_component.py` [DELETED]
* `log_controls_panel.py` [DELETED]
* `expandable_setting_card.py` [DELETED]

### Descripción
* Se simplificó la base de código eliminando archivos de componentes que solo tenían un único consumidor en la aplicación, integrándolos directamente en sus archivos padres para mejorar la cohesión y el mantenimiento:
  * **DraggableBox**: Integrado inline dentro de `visual_positioner_dialog.py` (su único consumidor).
  * **LogControlsPanel**: Integrado inline dentro de `log_view.py`, permitiendo adaptar dinámicamente los botones en cuadrícula responsiva al redimensionar la ventana.
  * **ExpandableSettingCard**: Integrado inline dentro de `blocks.py` debido a su naturaleza estructural de tarjeta de bloque.

---

## 7. Reorganización de Widgets Genéricos y Carpetas de Chat

### Componentes Afectados
* Directorio [widgets](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/)
* Directorio [components/chat](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/)
* `chat_components/` [DELETED]

### Descripción
* **Widgets Genéricos**: Movimos los componentes que sirven como plantillas generales y reutilizables (DRY) desde `components/` de vuelta a la carpeta `widgets/` y simplificamos sus nombres:
  * `blocks_component.py` ➔ [blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)
  * `controls_component.py` ➔ [controls.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls.py)
  * `table_component.py` ➔ [table.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table.py)
* **Subpaquete de Chat**: Se creó la carpeta `frontend/components/chat/` con su correspondiente `__init__.py` y movimos allí los subcomponentes del chat, simplificando sus nombres para eliminar el sufijo `_panel`:
  * `bot_mute_panel.py` ➔ [bot_mute.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py)
  * `chat_display_panel.py` ➔ [chat_display.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/chat_display.py)
  * `tts_settings_panel.py` ➔ [tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py)
  * `overlay_settings_panel.py` ➔ [overlay_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/overlay_settings.py)
* **Actualización de Importaciones**: Se corrigieron y unificaron todas las importaciones del proyecto en vistas, widgets y diálogos para referenciar las nuevas ubicaciones.

---

## 8. Filtro de Palabras Prohibidas (Banned Words Blacklist) en el Bot (TTS)

### Componentes Afectados
* [chat_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/chat_service.py)
* [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py)
* [bot_mute.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py)
* [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py)
* [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
* [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)
* [default_en_locale.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/default_en_locale.py)

### Descripción
* Se añadió soporte para configurar una lista negra de palabras prohibidas que no deben ser reproducidas por el bot de lectura de chat.
* **Backend y Filtro**: Añadimos el ajuste persistente `tts_banned_words` en el almacenamiento. En el controlador de chat implementamos una validación insensible a mayúsculas utilizando expresiones regulares de límite de palabra (`\b<palabra>\b`) tanto para la lectura de mensajes ordinarios (`_step_tts`) como para comandos explícitos de voz (`!tts`). Esto evita falsas coincidencias (por ejemplo, prohibir "ass" no bloquea "class").
* **Interfaz de Usuario**: Ampliamos el panel de usuarios silenciados (`BotMutePanel`) para albergar una nueva sección inferior de **Palabras Prohibidas** con su propio campo de entrada, botón de adición y listado de etiquetas dinámicas eliminables con icono de papelera roja.

---

## 9. Corrección del Crash de Mismatch de Motores de Voz (Local vs. IA)

### Componentes Afectados
* [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py)

### Descripción
* **El Problema**: Al cambiar el proveedor de voz de Local a IA Web en el chat, el controlador de chat seguía utilizando el caché de configuraciones anterior (que apuntaba a una clave de registro de voz local como `HKEY_LOCAL_MACHINE\...`). Esto provocaba un crash inmediato en el motor Web TTS al recibir un ID de voz local inválido.
* **Sincronización del Caché**: Se añadió la sincronización inmediata del caché de configuraciones (`self.sync_settings_cache()`) en cuanto el usuario modifica el proveedor de voz (`_handle_provider_change`) o la voz activa (`_handle_voice_change`).
* **Verificación de Seguridad**: Se reescribió `_resolve_voice_for_badges` para validar en tiempo constante $O(1)$ que el ID de voz configurado para un rol pertenezca al conjunto de voces actualmente disponibles y cargadas en el motor activo, previniendo cualquier cruce de voces corruptas.

---

## 10. Selección Multirregión para Roles y Agrupación de Ajustes de Voz

### Componentes Afectados
* [tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py)
* [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py)
* [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py)

### Descripción
* **Voces Multirregión para Roles**: Modificamos el envío de voces para pasar la lista de todas las voces del proveedor a los comboboxes de los roles del chat (`broadcaster`, `moderator`, etc.), agregándoles un prefijo dinámico con su región o idioma (ej. `[es-ES] Álvaro`, `[en-US] Aria`). Ahora el streamer puede elegir voces de cualquier región e idioma para los roles de su canal, independientemente del idioma seleccionado para la lectura global del chat.
* **Agrupación Visual de Configuración**: Para hacer la interfaz más ordenada y estructurada, agrupamos el conmutador del motor de voz premium, los selectores de idioma/voz y el control de volumen general dentro de una sola tarjeta secundaria (`ModernCard`) contenida en el panel principal.

---

## 11. Optimización del Controlador de Chat (ChatController)

### Componentes Afectados
* [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py)

### Descripción
* **Reemplazo Directo de URLs**: Simplificamos la limpieza de texto del chat reemplazando todas las URLs encontradas directamente por la frase `"un enlace web"`, eliminando el diccionario pesado `_URL_REPLACEMENT_KEYWORDS` y la lógica iterativa nested, reduciendo el consumo de memoria y CPU.
* **Constantes Estáticas de Clase**:
  * Movimos las prioridades de asignación de insignias (`_ROLE_PRIORITIES`) a una tupla a nivel de clase.
  * Cambiamos la búsqueda de la lista de bots predeterminados a un `frozenset` estático de clase (`_DEFAULT_BOTS`) para realizar comprobaciones rápidas en tiempo $O(1)$.
* **Eliminación de Código Duplicado (DRY)**: Centralizamos la validación de filtros de palabras prohibidas en el nuevo método auxiliar `_is_message_banned()`.
