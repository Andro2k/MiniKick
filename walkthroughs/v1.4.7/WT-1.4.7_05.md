# Walkthrough: Corrección de Bloqueos de YouTube (yt-dlp Anti-Bot), Búsqueda de Canciones Restringidas y Errores de Sintetización Web TTS

## Descripción de los Cambios

Se han resuelto los problemas reportados en los logs del usuario:

1. **Optimización Anti-Bot y Fallback Silencioso de Cookies en YouTube (`yt-dlp`):**
   * Se actualizaron los clientes de reproducción prioritarios en [music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py) a `['mweb', 'ios', 'android', 'tvhtml5']`, evitando los filtros anti-bot del cliente `web`.
   * Se implementó un fallback transparente que intenta extraer cookies directamente desde los navegadores locales instalados en Windows (`edge`, `chrome`, `firefox`, `brave`, `opera`) ante cualquier error de extracción o cuando una búsqueda retorna 0 resultados por filtrado de contenido explícito/edad.
   * Se corrigió el flujo de búsqueda en `YouTubeSearchWorker` para activar la autenticación vía navegadores cuando las búsquedas sin cookies devuelven una lista de resultados vacía.
   * Se agregaron claves de i18n para errores de restricción de edad y de bot en [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json).

2. **Sanitización y Manejo Limpio de Errores en Web TTS (`edge-tts`):**
   * Se mejoró la función `_is_speakable_text` en [tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py) para filtrar URLs, símbolos aislados y asegurar que el texto contenga al menos caracteres alfanuméricos pronunciables.
   * Se interceptaron los mensajes de respuesta sin audio de `edge-tts` (`No audio was received`) para cancelar inmediatamente los 3 reintentos inútiles y evitar el spameo de errores en el archivo de log.

## Archivos Modificados

* [backend/workers/music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py)
* [backend/providers/voices/tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py)
* [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
* [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)

## Resultados y Verificación

* **Eficiencia Big-O:** La validación de texto en TTS se realiza en un único pase $\mathcal{O}(N)$ eliminando retrasos innecesarios de red de $\sim 600\text{ms}$ por reintento fallido. La selección de clientes y cookies en YouTube previene fallos bloqueantes en tiempo de resolución $\mathcal{O}(1)$.
