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
