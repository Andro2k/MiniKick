# Release Notes | MiniKick v1.4.4
*Reproducción de Música en YouTube sin Cuentas, Descarga Concurrente TTS Online, Rediseño Modular de Música, Estandarización de Estilos UI y Protección de Comandos Plugin*

En esta versión (v1.4.4), MiniKick da un salto cuantitativo en rendimiento, modularidad y facilidad de uso. Introducimos soporte nativo para reproducción de música con YouTube sin necesidad de enlazar cuentas ni credenciales externas, permitiendo encolar canciones, listas de reproducción completas y reordenar temas en tiempo real. Optimizamos radicalmente la latencia del TTS Online con descargas concurrentes en segundo plano, erradicando las pausas de 2 a 3 segundos entre mensajes de chat. Además, realizamos una refactorización modular profunda del módulo de música, estandarizamos el sistema visual de divisores en toda la interfaz y añadimos un sistema de protección y clasificación visual para comandos de plugins (`[PLUGIN_...]`).

---

## 1. Reproducción e Integración de Música en YouTube sin Cuentas
Añadimos integración completa para reproducir audio desde YouTube sin requerir vinculación de cuentas ni tokens de API externos:
* **Motor de Extracción con `yt-dlp`**: Incorporamos extracción rápida y ligera de metadatos de vídeo en [youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py), obteniendo títulos, duraciones, miniaturas e hipervínculos de forma directa.
* **Soporte de Playlists en Chat**: Espectadores y streamers pueden agregar listas de reproducción completas de YouTube mediante el comando `!sr` o `!playlist`.
* **Reordenamiento Dinámico de Cola**: Implementamos el método `move_in_queue(from_index, to_index)` en `YouTubeMusicProvider` y [music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py), permitiendo cambiar la posición de canciones en la cola de reproducción mediante arrastrar y soltar o botones de acción sin interrumpir la pista en curso.

> [!IMPORTANT]
> El reproductor de YouTube opera de forma autónoma sin depender de API Keys de Spotify o Google, facilitando el uso de peticiones de música (`!sr`) desde el primer momento en que inicias MiniKick.

---

## 2. Descargas Concurrentes y Cero Latencia en TTS Online
Optimizamos la canalización de audio del motor de voz en línea (Web TTS / Edge-TTS) para lograr una reproducción instantánea en chats de alta actividad:
* **Futures Asíncronos Non-Blocking**: Refactorizamos `WebTTSProvider.prepare` en [tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py) para retornar objetos `Future` no bloqueantes (`<1ms`) hacia el despachador de voz [tts_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/tts_service.py).
* **Loop de Eventos Persistente**: Reutilizamos un único hilo con `asyncio` event loop por proveedor, eliminando la sobrecarga de crear y destruir loops de red por cada mensaje.
* **Descarga Concurrente en Segundo Plano**: Si llegan múltiples mensajes de chat consecutivos, el sistema pre-descarga los audios en paralelo en segundo plano mientras el audio actual se reproduce, logrando aciertos inmediatos en caché (`CACHE HIT!`) y reduciendo el tiempo de espera entre mensajes a 0 milisegundos.

> [!TIP]
> Con la descarga concurrente activa, cuando varios usuarios hablan seguido en el chat, los archivos de voz se procesan por adelantado y se reproducen uno tras otro de forma fluida sin silencios intermedios.

---

## 3. Rediseño Modular y Sincronización de la Vista de Música
Estructuramos la vista de música para un rendimiento óptimo y una mantenibilidad de código limpia:
* **Submódulos Especializados en `frontend/components/music/`**: Refactorizamos [music_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/music_view.py) dividiéndolo en 4 componentes enfocados:
  * [stats_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/stats_panel.py): Métricas de cola, tiempo restante y estado del servicio con `QGridLayout` responsivo.
  * `player_settings.py`: Ajustes del reproductor, enlace de navegador, canción actual y overlay para OBS.
  * `commands_panel.py`: Conmutadores de comandos de espectadores (`!sr`, `!skip`, `!song`, `!pause`, `!resume`, `!playlist`).
  * [queue_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/queue_panel.py): Tabla de cola de reproducción con soporte para mover y eliminar canciones.
* **Sincronización Instantánea de Pestaña (`view_shown`)**: Emitimos la señal `view_shown` al activarse la vista de música y la conectamos directamente a `_poll_now_playing()`, actualizando la lista de inmediato sin esperar el temporizador de sondeo.
* **Renderizado de Tabla de Cola Optimizado**: Envolvimos la actualización de filas en `setUpdatesEnabled(False)` / `setUpdatesEnabled(True)` para eliminar parpadeos de interfaz al cargar colas numerosas.

> [!NOTE]
> Al hacer clic en la pestaña de Música, la vista ya no experimenta retardos visuales ni espera de 2 a 5 segundos; los datos del reproductor y la cola se despliegan de forma instantánea.

---

## 4. Centralización de Estilos UI y Eliminación de `setStyleSheet` Inline
Purificamos el código de la interfaz para alinearlo con el sistema global de diseño de la aplicación:
* **Eliminación de Estilos Harcodeados**: Removimos 12 llamadas manuales a `setStyleSheet` en diálogos y vistas ([tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py), [command_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/command_dialog.py), [timer_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/timer_dialog.py), [network_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/network_view.py) y [blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)).
* **Reglas CSS Globales en `theme.py`**: Centralizamos en [theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) las reglas visuales para estados de error en cuadros de texto (`QLineEdit[state="error"]`, `QTextEdit[state="error"]`) y estados tipográficos (`state="bold"`, `danger`, `success`, `info`, `warning`, `plugin`).
* **Actualización Dinámica de Qt**: Todos los componentes usan la propiedad nativa `setProperty("state", ...)` junto con llamadas controladas a `unpolish()` / `polish()`.

---

## 5. Estandarización Global de Divisores (`ModernDivider`)
Homologamos el diseño visual de las líneas separadoras en todas las tarjetas y paneles de la aplicación:
* **Componente `ModernDivider`**: Creamos la clase reutilizable `ModernDivider(QFrame)` en [blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py), configurada con grosor de `1px` y rol `role="divider"`.
* **Reemplazo de Marco Nativo 3D**: Sustituimos las líneas predeterminadas `setFrameShape(QFrame.Shape.HLine)` en [dashboard_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py), [bot_mute.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py), [overlay_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/overlay_settings.py) y [tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py), garantizando que todos los divisores se muestren como una sutil línea plana de `1px`.

---

## 6. Clasificación y Protección de Comandos Plugin (`[PLUGIN_...]`)
Protegemos la integridad de las macros de sistema y mejoramos su visibilidad en el panel de comandos:
* **Nueva Columna "Tipo" en la Tabla**: Incorporamos la columna dedicada **Tipo** (`col_type`) en [command_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/command_view.py) con ancho ajustado a `130px` y relleno interno de `8px`. Muestra insignias claras: **`[Plugin]`** (en púrpura `state="plugin"`) para comandos integrados y **`[Personalizado]`** (en verde `state="everyone"`) para comandos del streamer.
* **Bloqueo de Edición de Respuestas de Plugins**: En [command_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/command_dialog.py), al editar comandos del sistema (cuya respuesta contiene `[PLUGIN_...`), el área de respuesta se bloquea como lectura exclusiva (`setReadOnly(True)`), se tiñe de color púrpura y muestra el badge traducido `COMANDO PLUGIN`. Esto impide alterar accidentalmente las macros de backend como `[PLUGIN_SPOTIFY_SR]` o `[PLUGIN_TTS_MAIN]`, manteniendo editables el disparador, enfriamiento, permisos y alias.
* **Cumplimiento Estricto i18n**: Eliminamos todos los textos harcodeados y fallbacks en código en favor de las claves de localización registradas en [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json).

> [!WARNING]
> La respuesta de los comandos de tipo Plugin está protegida contra edición para evitar romper la sincronización con los reproductores de música y el motor TTS. Sin embargo, puedes renombrar el disparador del comando (ej. cambiar `!sr` por `!pedir`), agregar alias o modificar sus permisos en cualquier momento.
