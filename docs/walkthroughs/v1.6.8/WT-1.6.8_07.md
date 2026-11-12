# Walkthrough Técnico — MiniKick v1.6.8 (Paso 07)

La vista previa reproduce primero el video ya descargado en la caché y solo usa YouTube si no existe o no trae imagen.

---

## Novedades

- Al pulsar ▶ en el historial, la vista previa abre el archivo local `yt_<id>.mp4` de la caché, sin red y sin audio. Un clic sobre el video lo pausa o lo reanuda, y se repite en bucle.
- Si la canción no está en la caché, el archivo no se puede abrir o no tiene pista de video, se usa el embed de YouTube como antes.

## Mejoras

- **Cadena de capas:** ▶ → `MusicView.preview_video_requested(url)` → `MusicController.handle_preview_video()` → `YouTubeMusicProvider.find_cached_media()` → `MusicCacheManager.find_cached_file()` → `MusicView.show_video_preview(url, local_path)`. El backend no importa Qt.
- **Búsqueda en caché:** `find_cached_file()` usa `youtube_video_id()` y busca `yt_<id>.*` ignorando los `.part`.
- **Reproducción local:** `MusicVideoPreviewPanel` usa un `QMediaPlayer` sin salida de audio con un `QVideoWidget`; los crea la primera vez que se necesitan.
- **Destello inicial:** el rectángulo blanco al crear el `QWebEngineView` ya no aparece al reproducir desde la caché, porque no se crea ninguna vista web.
- **Calentamiento retirado:** se elimina `warm_up()` del paso 06, porque no corregía el destello (es la superficie nativa del `QWebEngineView`, no la carga de DLL) y costaba tiempo en cada sesión.

## Limitaciones conocidas

- El destello y la zona negra de ~2 s siguen apareciendo cuando se usa el embed de YouTube la primera vez de la sesión.
- La vista previa local no tiene barra de progreso ni sonido.
- Los archivos `.mp4` de la caché dependen del formato que devuelva yt-dlp; si alguno solo trae audio, se usa el embed.
