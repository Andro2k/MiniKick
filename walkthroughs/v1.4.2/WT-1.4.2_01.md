# WT-1.4.2_01 - Solución de Escala y Alineación de Iconos (High DPI), Sincronización TTS, Migración de Base de Datos, Estilo de Switch, Campo de Comando y Variantes de Música (Premium & Cyberpunk)

Hemos realizado e implementado todos los cambios necesarios para corregir la borrosidad, desalineación y mala escala de los iconos en sistemas con escalado DPI de Windows diferente de 100%, la desincronización de la selección de voces en el sistema de chat TTS, el error de base de datos en Linux, el grosor del borde del switch cuando está desactivado, el comportamiento de habilitación del cuadro de texto del comando, la reorganización de carpetas de overlays con soporte de temas dinámicos, y el rediseño premium completo de los temas de música Cyberpunk y Premium Card con soporte de barra de progreso y carátula del álbum.

---

## Parte 1: Escala y Alineación de Iconos (High DPI)

### Diagnóstico Completo del Problema
1. **Método heredado de Qt (`app.devicePixelRatio()`):**
   El código original y las utilidades hacían uso de `app.devicePixelRatio()`. En PySide6/Qt6, este método tiende a devolver `1.0` de forma estática antes de que las ventanas se inicialicen. Esto causaba que todos los iconos generados al inicio de la aplicación se renderizaran con escala `1.0` (100%), viéndose diminutos y borrosos en comparación con el texto que sí se escalaba.
2. **DPR prematuro durante la construcción del widget (`self.devicePixelRatio()`):**
   Cuando los widgets (como el Sidebar o las pestañas) se instancian en `__init__`, todavía no están mostrados en la pantalla ni asociados a un contexto de ventana final. Por ende, la llamada a `self.devicePixelRatio()` durante la inicialización devolvía de forma predeterminada `1.0`. Al pasar explícitamente ese valor a `get_icon_colored`, se forzaba la creación de un icono de baja resolución (DPR 1.0) que luego se pixelaba al ser estirado en una pantalla de escala 1.25.
3. **Colorización por rasterización intermedia:**
   Originalmente, `get_icon_colored` usaba `QIcon.pixmap` para rasterizar el SVG a negro, creaba otro pixmap transparente, dibujaba el icono negro encima y aplicaba un relleno de color mediante `CompositionMode_SourceIn`. Esta doble rasterización y copiado arruinaba la suavidad de los bordes vectoriales (anti-aliasing) del SVG original.

### Cambios Realizados
- **`utils.py`**:
  - **Optimización de lectura y caché**: Implementamos `_load_svg_raw` con caché (`@lru_cache`) para leer el código XML del archivo SVG una única vez desde el disco.
  - **Colorización Vectorial Nativa**: Modificamos `_get_icon_colored_impl` para que reemplace el atributo de color en el XML del SVG (`currentColor` por `color_str`) y dibuje el vector directamente en el pixmap de destino usando `QSvgRenderer`. Esto mantiene la fidelidad vectorial intacta y elimina cualquier pixelación o defecto de bordes.
  - **DPR por Defecto Robusto**: Ajustamos `_get_default_dpr` para consultar a `app.primaryScreen().devicePixelRatio()` en primer lugar, garantizando que el ratio real (`1.25`, `1.5`, etc.) esté disponible al instante desde el inicio.
- **`sidebar_component.py`**:
  - Removimos el parámetro explícito `self.devicePixelRatio()` en las llamadas a `get_icon_colored` durante el constructor. Al no pasarlo, la utilidad cae en `_get_default_dpr()` que recupera el valor correcto de la pantalla (`1.25`) en lugar del `1.0` prematuro del widget no mostrado.

---

## Parte 2: Sincronización de Selección de Voz TTS

### Diagnóstico del Problema
Cuando el usuario cambiaba el idioma en el ComboBox de la interfaz gráfica (`combo_lang`):
1. Se recalculaba la lista de voces correspondientes a ese idioma en el ComboBox de voz (`combo_voice`).
2. Para evitar eventos innecesarios mientras se borraban e insertaban ítems en la lista, la UI bloqueaba temporalmente las señales de `combo_voice` mediante `blockSignals(True)`.
3. Se seleccionaba la primera voz disponible por defecto.
4. Al estar las señales bloqueadas, el controlador nunca se enteraba de esta selección predeterminada de voz (el evento `voice_changed` no se disparaba), dejando el motor TTS del backend con la voz anterior (por ejemplo, una voz de España) mientras que la UI reflejaba visualmente una voz del nuevo idioma (por ejemplo, Argentina).

### Cambios Realizados
- **`backend/controllers/chat_controller.py`**:
  - Actualizamos el método de filtrado de idiomas `_filter_voices_by_language` para que el controlador sea el encargado de resolver la voz final que debe seleccionarse (`final_select_id`).
  - Si la voz actual no se encuentra en el nuevo idioma filtrado (o si el usuario cambia manualmente el filtro de idioma), el controlador asigna de forma proactiva y silenciosa la primera voz de la lista filtrada al motor del backend llamando a `self.service.set_voice(provider, final_select_id)` y actualizando la memoria caché de configuración.
  - Finalmente, actualiza la UI (`update_voices`) enviándole explícitamente el `final_select_id` calculado. Esto mantiene tanto la UI como el motor TTS en perfecta sincronía lógica.

---

## Parte 3: Migración Automática de Base de Datos (Error: `no such column`)

### Diagnóstico del Problema
Al ejecutar la aplicación en Linux (Ubuntu), si el usuario ya tenía una base de datos antigua (`minikick.db`), la aplicación fallaba críticamente con:
`sqlite3.OperationalError: no such column: allowlist`
Esto se debe a que la sentencia `CREATE TABLE IF NOT EXISTS spam_filters` no altera tablas que ya existen. Como la columna `allowlist` fue agregada en actualizaciones de código posteriores a la creación original de la tabla en Linux, la base de datos local quedó desactualizada.

### Cambios Realizados
- **`backend/database/manager.py`**:
  - Implementamos una función de migración inteligente de esquema llamada `_upgrade_schema()`.
  - Esta función se ejecuta automáticamente durante la inicialización de la base de datos, revisa la estructura existente de cada tabla (`PRAGMA table_info`) y añade dinámicamente cualquier columna faltante (como `allowlist` en `spam_filters`, campos agregados a `obs_rewards`, `chat_timers`, etc.) mediante comandos `ALTER TABLE ... ADD COLUMN ...`.
  - Esto previene cualquier error de inconsistencia de base de datos sin obligar al usuario a borrar sus datos locales.

---

## Parte 4: Estilo del Conmutador (ModernSwitch)

### Cambios Realizados
- **`frontend/widgets/controls.py`**:
  - Importamos `QPen` y configuramos el grosor del borde en `1.5` píxeles cuando el conmutador se encuentra desactivado (`not self.isChecked()`), y `1.0` cuando está activado.
  - Ajustamos dinámicamente las coordenadas del rectángulo de dibujo (`QRectF`) reduciendo sus márgenes por la mitad del grosor del bolígrafo (`pen_width / 2`). Esto evita que el borde del switch se recorte por los límites físicos del widget, resultando en un renderizado perfectamente suave y sin artefactos en los bordes.

---

## Parte 5: Habilitación Dinámica del Campo de Comando TTS

### Cambios Realizados
- **`frontend/components/chat/tts_settings.py`**:
  - Conectamos la señal `toggled` de `chk_command` (el switch de usar comando) directamente al slot `setEnabled` de `txt_command` (el cuadro de texto).
  - Inicializamos el estado habilitado del cuadro de texto usando el valor de `chk_command.isChecked()` en la creación del widget y lo actualizamos durante la carga de configuraciones en `set_settings_ui()`.
- **`backend/controllers/chat_controller.py`**:
  - Actualizamos `_sync_tts_command_from_db` para asegurar la sincronización del estado habilitado/deshabilitado del cuadro de texto al recargar la configuración desde la base de datos.

---

## Parte 6: Reorganización de Overlays y Variantes de Música (Premium & Cyberpunk)

### Cambios Realizados
- **Restructuración de Directorios**:
  - Movimos `chat.html` y la carpeta `css` a `assets/overlays/chat/` y `assets/overlays/chat/css/`.
  - Movimos `rewards.html` a `assets/overlays/rewards/rewards.html`.
  - Creamos el subdirectorio `assets/overlays/music/` y movimos allí `music.html`.
- **Soporte de Hojas de Estilo Dinámicas en Música**:
  - Separamos el CSS de `music.html` e implementamos 5 temas de estilo independientes bajo `assets/overlays/music/css/`: `glass.css`, `minimal.css`, `neon.css`, `cyber.css` y `card.css`.
  - Actualizamos `music.html` para enlazar la hoja de estilo correspondiente según el parámetro de URL `theme` recibido (ej. `/music/css/neon.css`).
- **Servidor de Overlays (Backend)**:
  - Modificamos `overlay_server.py` para que resuelva las nuevas ubicaciones de los archivos `.html` y añadimos un servidor de archivos estáticos genérico al final del método `do_GET` para permitir la carga correcta de recursos como `/chat/css/...` y `/music/css/...`.
  - **Autorización de CSS (Fondo transparente corregido)**: Ajustamos el middleware de validación del token de sesión para que permita que las solicitudes de archivos de hoja de estilo `.css` (que contienen `/css/` o terminan en `.css`) pasen sin token. Esto soluciona la desconfiguración visual (los widgets se veían sin fondo) provocada por el bloqueo HTTP 403 que sufrían las hojas de estilo anidadas.
- **Panel de Configuración de Música (Frontend)**:
  - Actualizamos `music_view.py` para añadir un dropdown (`combo_music_theme`) que permite elegir el tema del reproductor.
  - Modificamos la acción del botón de copiado de URL para que adjunte de forma automática el parámetro `&theme=valor` al portapapeles.

---

## Parte 7: Recuperación de Carátulas, Tiempos y Barra de Progreso

### Diagnóstico del Problema
Anteriormente, el payload enviado por el backend al overlay de música solo contenía `title`, `artist`, `url` y el estado `is_playing`. Esto impedía a los desarrolladores de temas mostrar la barra de progreso, la carátula del álbum o la duración de la canción, elementos clave para lograr los acabados de alta fidelidad solicitados por el usuario.

### Cambios Realizados
1. **Extracción en YouTube y Spotify (`spotify_client.py`, `music_worker.py`)**:
   - En el resolvedor de YouTube, guardamos la URL de la miniatura de la canción (`thumbnail`) obtenida directamente de `yt-dlp`.
   - En Spotify, extraemos `album.images[0].url` del endpoint `/me/player/currently-playing` para la carátula del álbum, así como el tiempo de progreso (`progress_ms`) y duración total (`duration_ms`).
2. **Cálculo de Tiempos en YouTube (`youtube_client.py`)**:
   - Para el reproductor de YouTube, leemos el progreso en tiempo real consultando `self.player.position()`.
   - Para la duración, implementamos un intérprete de cadenas de respaldo (`parse_duration_str_to_ms`) que convierte formatos de texto de duración como `"04:25"` a milisegundos cuando el reproductor local de Qt aún no ha terminado de cargar el flujo de audio.
3. **Predicción Suave del Lado del Cliente (`music.html`)**:
   - Estructuramos el overlay HTML para incorporar contenedores de barra de progreso y carátula del álbum.
   - En Javascript, añadimos una función matemática de formateo de tiempo (`formatTime`) y una rutina de ticker inteligente (`startProgressTicker`). Cada vez que se recibe un evento SSE con el estado del reproductor, el cliente sincroniza su progreso y, si la pista está reproduciéndose, incrementa la barra de forma predictiva y ultra-suave cada segundo, reduciendo la carga del CPU en el backend.
4. **Rediseño Estilo Cyberpunk y Premium Card (`cyber.css` y `card.css`)**:
   - **`cyber.css`**: Configura un fondo con cuadrícula de neón púrpura (`linear-gradient`), borde luminoso, tipografía de terminal de ciencia ficción (`Orbitron`), nombre del artista en cian fosforescente, título en magenta, barra de progreso con gradiente cian-a-magenta brillante, y badge "NOW PLAYING" en una caja de neón delineada.
   - **`card.css`**: Configura una tarjeta con degradado oscuro de tono bronce y dorado premium, bordes redondeados pronunciados, badge estilizado con un punto verde de reproducción en vivo (`• NOW PLAYING`), títulos blancos, artistas en tono oro cepillado y barra de progreso y ecualizadores de color bronce.

---

## Verificación Realizada

- Validamos que la aplicación inicializa, compila e importa todos los módulos correctamente sin excepciones ejecutando `uv run main.py`.
