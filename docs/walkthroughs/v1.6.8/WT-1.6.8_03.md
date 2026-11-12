# Walkthrough Técnico — MiniKick v1.6.8 (Paso 03)

La vista de música tiene una pestaña **Historial** junto a la cola, con acción para volver a encolar cualquier canción.

---

## Novedades

- La columna derecha ahora es un `QTabWidget` con **Cola** e **Historial**.
- El historial lista las últimas 100 canciones reproducidas o quitadas de la cola (título, autor, pedido por, duración).
- Cada fila tiene un botón **+** que vuelve a agregar la canción al final de la cola y muestra un aviso.

## Mejoras

- **Sin tabla nueva:** el historial son las filas de `music_queue` con `is_played = 2`, que el trigger `prune_music_queue` ya limita a 100. `SQLiteMusicStorage.load_history()` las devuelve de la más reciente a la más antigua.
- **Cadena de capas:** `MusicView.requeue_history_item_requested(url, requester, platform)` → `MusicController.handle_requeue_history_item()` → `YouTubeMusicProvider.add_to_queue(..., max_duration_min=0)`. Se pasa `0` para no aplicar el límite de duración del chat a una acción del streamer.
- El historial se refresca desde `refresh_now_playing()` con comparación de firma, así que no se redibuja si no cambió.
- `requester_style()` se extrajo de `queue_panel.py` y lo comparten la cola y el historial.
- Textos: `music.queue.history_*`, `music.queue.requeue_tooltip`, `music.tabs.queue`, `music.tabs.history` y `music.toast.requeued` en `es.json`, `en.json` y `locale_defaults.py`.

## Limitaciones conocidas

- El historial mezcla canciones reproducidas y quitadas de la cola (ambas quedan en estado 2). Distinguirlas requiere un estado nuevo.
- La reproducción de video dentro de la app **no** está incluida (ver prompt de traspaso).
