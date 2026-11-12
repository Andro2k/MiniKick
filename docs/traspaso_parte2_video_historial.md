# Traspaso — MiniKick Música, Parte 2: reproducir video

## Contexto
- Repo `Andro2k/MiniKick`, rama `release/v1.6.8`, base `d56df3b`. Antes de empezar, aplica en orden `0001-*.patch` y `0002-*.patch` (`git apply`) y haz `git pull` una sola vez.
- Ya hecho (no rehacer): overlay en `ExpandableCard` con paleta única; pestaña **Historial** (`frontend/components/music/history_panel.py`) con botón + para re-encolar; `SQLiteMusicStorage.load_history()`; `YouTubeMusicProvider.get_history()`; `MusicController.handle_requeue_history_item()`.
- Cómo suena hoy la música: `youtube_provider.py` resuelve el audio con yt-dlp y lo reproduce con `QMediaPlayer`. **No hay video en la app.** `pyside6-webengine==6.12.0.140` está en `requirements.in`, pero ningún `.py` usa `QWebEngine`.
- Cada canción del historial/cola tiene `url` (YouTube), `title`, `artist`, `duration`, `requester`, `platform`.
- Estado de pruebas tras los patches: `project_quality_suite.py --quick` 14/14 aprobadas. No hay carpeta `tests/`.

## Objetivo
Poder ver el video de una canción dentro de la app, como en la captura de referencia: un reproductor grande con "Now playing" y la siguiente canción, y poder abrir el video de cualquier fila del historial.

## Tareas
1. Decidir y anotar en una línea: **a)** vista previa de video solo para el historial (embed de YouTube en `QWebEngineView`, sin audio), o **b)** reproductor principal con video sincronizado con `QMediaPlayer`. Recomendado: a), porque b) duplica audio y obliga a sincronizar tiempos.
2. Crear `frontend/components/music/video_preview_panel.py` con `QWebEngineView` cargando `https://www.youtube-nocookie.com/embed/<id>?autoplay=1&mute=1`. Extraer el id con `classify_music_query` o un helper existente; no escribir otro regex si ya hay uno.
3. Agregar en `history_panel.py` una acción "Ver video" por fila (nueva señal `preview_requested(url)`) y mostrar el panel en la pestaña Historial (por ejemplo, encima de la tabla, colapsable con `ExpandableCard`).
4. Si el video no se puede incrustar (error 150/101 de YouTube), mostrar un mensaje y un botón para abrirlo en el navegador (`QDesktopServices.openUrl`).
5. Liberar el `QWebEngineView` al ocultar la pestaña o cerrar la app (revisar `frontend/window/shutdown.py`) para no dejar reproduciendo ni consumir memoria.
6. Claves i18n nuevas en `locales/es.json`, `locales/en.json` y `backend/config/locale_defaults.py` (mismo contenido en los tres; la suite valida la paridad).
7. Revisar `MiniKick.spec`: confirmar que el empaquetado incluye los recursos de WebEngine y anotar el aumento de tamaño del instalador.

## Reglas del proyecto
- Capas: la vista emite señales, el controlador decide, el backend no importa Qt de la vista.
- Sin colores ni textos fijos: usar `Palette`/`BrandColors` y `i18n.get(...)`.
- Paleta única en música: neutros + `BrandColors.GREEN`.
- Cambio mínimo; lo no pedido se menciona en una línea al final.
- Leer con `grep -n` y rangos, no archivos completos.

## Entrega
- Un patch (`git format-patch`) verificado con `git apply --check` sobre el HEAD remoto, más `docs/walkthroughs/v1.6.8/WT-1.6.8_04.md` con el mismo formato que `WT-1.6.8_03.md`.
- Resumen corto: archivos tocados, resultado de `project_quality_suite.py --quick`, riesgos.
- Para pruebas sin pantalla usa `QT_QPA_PLATFORM=offscreen`; `QWebEngineView` puede requerir `QTWEBENGINE_CHROMIUM_FLAGS=--no-sandbox` en un contenedor.

## Fallas conocidas (no investigar)
- El historial mezcla canciones reproducidas y quitadas de la cola (ambas usan `is_played = 2`).
- `MUSIC_ART_ACCENT` sigue en `MockupPalette` a propósito, porque lo usa `AVATAR_GRADIENTS`.
