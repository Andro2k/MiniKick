# Traspaso — MiniKick Música, Parte 3: contexto de lo hecho hasta ahora

## Contexto
- Repo `Andro2k/MiniKick`, rama `release/v1.6.8`. HEAD remoto al cierre de esta sesión: `2519c29` (incluye ya tus patches 0001–0004 integrados).
- Entregados **y aún sin aplicar** en tu repo: `0005-fix-music-carga-fiable-de-la-vista-previa-de-video.patch` y `0006-feat-music-vista-previa-desde-el-video-en-cach-con-r.patch`. `0005` aplica sobre `2519c29`; `0006` aplica sobre `0005` (ambos verificados con `git apply --check` en un clon limpio).
- Antes de empezar: `git pull`, aplicar `0005` y `0006` en orden (`git apply`), y abrir la app para probar.
- Estado de pruebas: `project_quality_suite.py --quick` 14/14 aprobadas tras cada patch. No hay carpeta `tests/`.
- Stack: Python/PySide6 6.12, `pyside6-webengine==6.12.0.140`, yt-dlp para resolver y descargar audio/video a `%LOCALAPPDATA%\.Minikick\cache`.

## Qué se hizo, por patch
| Patch | Contenido |
|---|---|
| 0001 | Overlay de música en `ExpandableCard` con paleta única; vista previa del overlay |
| 0002 | Pestaña **Historial** (`history_panel.py`) con botón + para re-encolar; `SQLiteMusicStorage.load_history()`; `YouTubeMusicProvider.get_history()`; `MusicController.handle_requeue_history_item()` |
| 0003 | `video_preview_panel.py` (embed de YouTube en `QWebEngineView`, sin audio); botón ▶ por fila (`preview_requested(url)`); `youtube_video_id()` pública en `backend/utils/youtube_url.py`; liberación en `shutdown.py`; `AA_ShareOpenGLContexts` en `bootstrap/qt_setup.py`; 4 claves i18n `music.queue.preview_*`; `WT-1.6.8_04.md` |
| 0004 | Vista previa movida a la pestaña **Reproductor**; esquinas de tarjetas de Cola/Historial acordes al TAB (propiedad `tab_flush="true"` + regla QSS); sliders redondeados (`Size.SLIDER_GROOVE`, `Size.SLIDER_HANDLE`); `js.warning=false` en `QT_LOGGING_RULES` (`bootstrap/environment.py`); `WT-1.6.8_05.md` |
| 0005 | Carga fiable: señal `onReady` (título `mk-yt-ready`), reintento único tras 8 s, descarga de la vista solo si sigue oculta 300 ms (`HIDE_GRACE_MS`), logs `[MusicVideo]`; `WT-1.6.8_06.md` |
| 0006 | Vista previa **desde el video en caché** con `QMediaPlayer` + `QVideoWidget` (sin audio, clic = pausa/reanuda, bucle) y respaldo automático al embed; retira el `warm_up()` de 0005; `WT-1.6.8_07.md` |

## Arquitectura de la vista previa (estado tras 0006)
```
▶ en fila (history_panel) → MusicHistoryPanel.preview_requested(url)
  → MusicView._on_preview_requested  (cambia a la pestaña Reproductor)
  → MusicView.preview_video_requested(url)
  → MusicController.handle_preview_video(url)
  → YouTubeMusicProvider.find_cached_media(url)
  → MusicCacheManager.find_cached_file(url)      # yt_<id>.*, ignora .part
  → MusicView.show_video_preview(url, local_path)
  → MusicPlayerSettingsPanel.show_video_preview  (expande tarjeta)
  → MusicVideoPreviewPanel.load(url, local_path)
        local_path válido con pista de video → QMediaPlayer + QVideoWidget
        si no existe / no abre / sin video   → embed YouTube (QWebEngineView, lazy)
        si el embed falla (101/150/153/timeout) → mensaje + botón "Abrir en el navegador"
```
- Ciclo de vida: la vista web se crea al primer uso, se destruye al ocultar el panel, colapsar la tarjeta, cambiar de pestaña/vista, ocultar la ventana o cerrar (`MusicView.release_video_preview()` desde `MainWindowShutdown`).
- `get_history` y `find_cached_media` se consultan con `hasattr`/`getattr` en el controlador; **no** se añadieron al Protocol `IMusicProvider` (YAGNI).

## Hallazgos importantes (verificados)
- **La caché guarda `.mp4`**: `music_worker.py` descarga con `bestaudio/best` y los archivos son `yt_<id>.mp4` (listado de `%LOCALAPPDATA%\.Minikick\cache`). Si algún mp4 no trae video, el panel cae al embed y lo registra: `[MusicVideo] Cached playback unavailable (...)`.
- **El "pantallazo"** (grabación `2026-11-12_07-08-33.mp4`, seg. ~16): rectángulo blanco al crear por primera vez el `QWebEngineView`, luego zona negra ~2 s y después carga YouTube. Es la superficie nativa del `QWebEngineView`, no la carga de DLL. Con archivo local no se crea la vista web.
- **Sliders**: `margin-top`/`margin-bottom` negativos por separado anulaban el `border-radius`; se usa `margin: -5px 0`.
- **Esquinas**: el panel del TAB tiene la esquina superior izquierda recta; las tarjetas pegadas al panel llevan `tab_flush="true"`.
- **Empaquetado** (`MiniKick.spec` sin cambios): el hook de PyInstaller recoge `QtWebEngineProcess`, `qtwebengine_resources*.pak`, `icudtl.dat` y locales. En Linux, con una app mínima, WebEngine suma ~416 MB en disco y ~160 MB comprimidos (gzip). **Falta medirlo en Windows.**

## Log (`minikick.log`)
- Resuelto: `Unrecognized feature: 'web-share'` y `Failed to create WebGPU Context Provider` (venían de la consola JS del embed; silenciados con `js.warning=false`).
- Pendiente: `QFont::setPointSize: Point size <= 0 (-1)` apareció una vez, justo después de re-encolar desde el historial; no se pudo reproducir. Si vuelve, anotar qué se estaba haciendo (hover, menú, desplegable).
- Preexistente, no tocado: `[WhatsNew] GitHub release notes unavailable ... No highlights parsed`.

## Tareas pendientes
1. Probar `0005` + `0006` en Windows: ¿desaparece el destello al previsualizar canciones en caché? ¿cae bien al embed con una canción fuera de la caché?
2. Probar un video **no incrustable** (101/150) y vigilar el error 153 de YouTube; si aparece, ajustar el origen de la página en el embed.
3. Medir el aumento de tamaño del instalador en Windows y anotarlo en el walkthrough.
4. Decisión abierta: ¿mostrar también el video de la canción **que está sonando** en el reproductor principal, sincronizado? (el `QMediaPlayer` del proveedor ya reproduce el `.mp4`; bastaría un `setVideoOutput`). No está hecho.
5. Opcional: barra de progreso en la vista previa local.

## Reglas del proyecto
- Capas: la vista emite señales, el controlador decide, el backend no importa Qt de la vista.
- Sin colores ni textos fijos: `Palette`/`BrandColors` e `i18n.get(...)`. Claves nuevas en `locales/es.json`, `locales/en.json` y `backend/config/locale_defaults.py` (la suite valida la paridad).
- Paleta única en música: neutros + `BrandColors.GREEN`.
- Cambio mínimo; lo no pedido se menciona en una línea al final.
- Leer con `grep -n` y rangos, no archivos completos.
- Entrega: patch con `git format-patch`, verificado con `git apply --check` sobre el HEAD remoto, más `docs/walkthroughs/v1.6.8/WT-1.6.8_NN.md` en el formato de `WT-1.6.8_03.md` (siguiente número libre: `08`).
- Resumen corto al final: archivos tocados, resultado de `project_quality_suite.py --quick`, riesgos.
- Pruebas sin pantalla: `QT_QPA_PLATFORM=offscreen` y, para WebEngine en contenedor, `QTWEBENGINE_CHROMIUM_FLAGS=--no-sandbox --disable-gpu`.

## Fallas conocidas (no investigar)
- El historial mezcla canciones reproducidas y quitadas de la cola (ambas usan `is_played = 2`).
- `MUSIC_ART_ACCENT` sigue en `MockupPalette` a propósito, porque lo usa `AVATAR_GRADIENTS`.
- Los avisos de Chromium sobre `dbus`/RHI/GPU en el contenedor Linux no afectan a Windows.
