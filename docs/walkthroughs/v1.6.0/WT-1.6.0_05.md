# Walkthrough WT-1.6.0_05: Integración de GIFs/Giphy en Chat Overlay, Soporte Nativo Twitch y Corrección TTS

Documento de cambios para la integración de GIFs animados (Giphy y URLs directas) en el overlay de chat (`chat.html`), soporte del tag nativo `gifs` de Twitch IRC, corrección del sintetizador de voz (TTS) para evitar la lectura de placeholders/enlaces de GIFs, y comando multiplataforma `!gif <enlace|texto>`.

---

## 1. Novedades

- **Integración de GIFs en el Chat Overlay ([chat.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/chat.html) y [chat.js](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/js/chat.js))**:
  - Soporte completo para renderizar imágenes animadas `.chat-gif` dentro de `.chat-gif-wrapper` en el overlay de chat de OBS.
  - Sincronización automática de scroll (`autoScroll()`) en el evento `onload` del elemento `<img>`, evitando saltos o desalineaciones visuales al completarse la descarga del GIF.
  - Diseño responsivo y estético con bordes redondeados (`border-radius: 8px`), elevación suave (`box-shadow`), y contención adaptada a todos los temas visuales (`neon`, `minimal`, `glass`, `cyber`, `card`).
- **Soporte Nativo de Twitch IRC (`gifs=...`)**:
  - En [twitch_ws_provider.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_ws_provider.py), se parsea el tag nativo `gifs=<indices>|<gif_id>|<url>` que emite Twitch cuando los espectadores usan el selector oficial de Giphy.
  - La URL directa del GIF se extrae en $\mathcal{O}(1)$ y se propaga en el nuevo campo `gif_url` de `ChatMessageDTO` a través de [twitch_chat_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/twitch_chat_worker.py).
- **Comando Multiplataforma `!gif <enlace|texto>` y Auto-Embed**:
  - Nuevo servicio desacoplado [giphy_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/giphy_service.py) capaz de:
    1. Resolver enlaces directos `.gif` o `.webp`.
    2. Convertir URLs de páginas de Giphy (`giphy.com/gifs/<slug>-<id>`) directamente a URLs de medios (`media.giphy.com/media/<id>/giphy.gif`).
    3. Realizar búsquedas por palabras clave contra la API de Giphy (`https://api.giphy.com/v1/gifs/search`) cuando se configura una API key, con caché LRU en memoria ($\mathcal{O}(1)$ lookups).
  - Comando de sistema `!gif` registrado automáticamente en [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) bajo el tag `[PLUGIN_CHAT_GIF]`, disponible en todas las plataformas (Kick, Twitch, YouTube, TikTok).
  - Auto-detección en mensajes normales: si un usuario envía un enlace a un GIF en el chat, el sistema lo detecta y lo proyecta automáticamente en el overlay.
- **Configuración de Giphy API Key en Interfaz Gráfica**:
  - Agregado campo de entrada seguro (`QLineEdit` con modo de eco protegido) en la pestaña del overlay de chat ([overlay_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/overlay_settings.py) y [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py)).
  - Persistencia unificada en `chat_service.py` (`giphy_api_key`).
  - Nuevas claves i18n estructuradas en [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json). Cero texto quemado en código.

---

## 2. Mejoras

- **Optimización Big-O en Detección y Resolución**:
  - Resolución de URLs directas y enlaces de Giphy en tiempo $\mathcal{O}(1)$ mediante expresiones regulares pre-compiladas a nivel de módulo (`_DIRECT_GIF_REGEX`, `_GIPHY_PAGE_REGEX`, `_GIPHY_MEDIA_REGEX`).
  - Caché de búsqueda en `GiphyService` con eviction $\mathcal{O}(1)$ para evitar peticiones HTTP redundantes a la API de Giphy.
  - Supresión de llamadas y renderizado de texto innecesario en [chat.js](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/js/chat.js): si el mensaje consta únicamente de un GIF, el contenedor de texto queda suprimido, evitando wrappers vacíos en el DOM.
- **Defensa en Recepción de Socket Twitch IRC**:
  - `_parse_privmsg` aplica `line.rstrip("\r\n")` de forma preventiva para tolerar cualquier anomalía de framing de red o cadenas crudas en pruebas.
- **Desacoplamiento y Tipado**:
  - `ChatMessageDTO` en [chat_pipeline.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/chat_pipeline.py) ampliado con `gif_url: str = ""` manteniendo total retrocompatibilidad con callbacks de 6 o 7 argumentos en `widgets_controller.py` y `overlay_manager.py`.
- **Fallback Global de GIPHY_API_KEY en Configuración**:
  - `GiphyService` ahora utiliza como fallback global la constante `GIPHY_API_KEY` configurada en [api_keys.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/api_keys.py). Esto permite que cualquier usuario pueda utilizar la búsqueda por texto `!gif <texto>` de inmediato sin necesidad de ingresar una clave manual en Ajustes, manteniendo a la vez la opción de sobreescribirla en la interfaz si así lo desea.

---

## 3. Correcciones

- **Silenciamiento de Placeholders de GIFs en TTS**:
  - **Problema corregido**: Al enviar un GIF en Twitch, el IRC transmitía el texto `[Wacky Races Lol GIF by Boomerang Official]`, provocando que el lector de voz sintetizara y leyera en voz alta la descripción del GIF.
  - **Solución implementada**: En [spam_handler.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/spam_handler.py), se introdujo `_TWITCH_GIF_REGEX = re.compile(r"\[.*? GIF by .*?\]", re.IGNORECASE)` y supresión de `gif_url` dentro de `clean_message_for_tts`.
  - Si el mensaje contiene únicamente el GIF o su placeholder, `clean_message_for_tts` devuelve una cadena vacía `""`.
  - En [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py), `_step_tts` detecta la cadena vacía y retorna de inmediato (`return`), evitando por completo cualquier emisión de voz no deseada.
  - Si el usuario acompañó el GIF con texto propio (ej. `"mira esto [Wacky Races...]"`), el TTS ahora lee de forma limpia y exclusiva el texto del usuario (`"mira esto"`).
- **Limpieza de Texto Redundante en Overlay**:
  - En `formatChatMessage` de [chat.js](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/js/chat.js), se eliminan automáticamente los corchetes de descripción de Twitch o la URL cruda del GIF cuando `gif_url` está presente, para que en el overlay aparezca únicamente la imagen animada sin texto repetitivo.
