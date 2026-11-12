# Walkthrough Técnico — MiniKick v1.6.8 (Paso 04)

El historial de música permite ver el video de cualquier canción en una vista previa, sin audio, dentro de la pestaña **Reproductor**.

---

## Novedades

- Cada fila del historial tiene un botón **▶** (Ver video) que lleva a la pestaña **Reproductor** y abre ahí la vista previa, dentro de un `ExpandableCard` colapsable.
- El video se carga como embed de YouTube (`youtube-nocookie.com`, `autoplay=1&mute=1`). El audio sigue saliendo solo por el reproductor de la app.
- Si el video no se puede incrustar (códigos 101/150 de YouTube) o el enlace no es de YouTube, se muestra un mensaje y el botón **Abrir en el navegador**.

## Mejoras

- **Decisión:** opción a), vista previa solo para canciones del historial. La opción b) (video sincronizado con `QMediaPlayer`) duplicaría el audio y obligaría a sincronizar tiempos.
- **Cadena de capas:** botón de fila → `MusicHistoryPanel.preview_requested(url)` → `MusicView._on_preview_requested()` (cambia a la pestaña Reproductor) → `MusicPlayerSettingsPanel.show_video_preview()` → `MusicVideoPreviewPanel.load(url)`. Es presentación pura, no pasa por controlador ni backend.
- **Id de YouTube:** `youtube_video_id()` en `backend/utils/youtube_url.py` (antes `_youtube_video_id`, ahora público). No se agregó ninguna regex nueva.
- **Detección de error:** el reproductor usa la IFrame API de YouTube y su `onError` escribe el código en `document.title`; el panel lo lee con `QWebEngineView.titleChanged`, sin subclase ni `QWebChannel`. También cubre que el script de YouTube no cargue (`mk-yt-error:load`).
- **Liberación de recursos:** el `QWebEngineView` se crea en el primer uso (el import de WebEngine ocurre dentro del método, sin costo en el arranque) y se destruye (`about:blank` + `deleteLater`) al ocultarse el panel, colapsar la tarjeta, cambiar de pestaña o vista, ocultar la ventana o cerrar la app (`MusicPlayerSettingsPanel.release_video_preview()`). El cierre llama a `MusicView.release_video_preview()` desde `MainWindowShutdown`.
- **Arranque:** `bootstrap/qt_setup.py` activa `AA_ShareOpenGLContexts` antes de crear `QApplication`, como pide Qt WebEngine Widgets cuando se importa después de la app.
- **Textos:** `music.queue.preview_title`, `preview_tooltip`, `preview_error` y `preview_open_browser` en `es.json`, `en.json` y `locale_defaults.py`.
- **Empaquetado:** `MiniKick.spec` no cambia. El hook de PyInstaller para PySide6 incluye `QtWebEngineProcess`, `qtwebengine_resources*.pak`, `icudtl.dat` y los locales al detectar el import. En una compilación mínima en Linux, WebEngine suma unos 416 MB en disco y unos 160 MB comprimidos (gzip) frente a una app solo con QtWidgets; falta medirlo en el instalador de Windows.

## Limitaciones conocidas

- La reproducción real contra YouTube no se pudo probar en el entorno de desarrollo (sin acceso de red). Falta comprobar a mano un video normal, uno no incrustable (150/101) y que no aparezca el error 153 de YouTube.
- Al ocultar la ventana (por ejemplo, a la bandeja) la vista previa se cierra y no se reanuda sola.
- El historial sigue mezclando canciones reproducidas y quitadas de la cola.
