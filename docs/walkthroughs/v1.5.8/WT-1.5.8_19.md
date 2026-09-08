# Walkthrough: WT-1.5.8_19 - Mejoras Arquitectónicas del Sistema de Música (Resiliencia, Loudness Normalization, FTS5 Trigram y 60 FPS Overlay)

## Resumen Ejecutivo

En este walkthrough se implementaron y verificaron las 4 mejoras aprobadas de la hoja de ruta del sistema de música ([MUSIC_SYSTEM_ROADMAP.md](file:///c:/Users/TheAn/Desktop/python/Kick/docs/future_updates/MUSIC_SYSTEM_ROADMAP.md)):

1. **Cola de Descargas Resiliente con Reintentos Exponenciales (Backoff Exponencial)**:
   - Reintentos con jitter y backoff exponencial ante fallos transitorios de red / HTTP 429 (`Too Many Requests`) con rotación dinámica de clientes (`['ios', 'android']`, `['web', 'mweb']`, `['tv_embedded']`) en [music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py).
   - Extracción de metadatos de sonoridad (`loudness`).
2. **Normalización Inteligente de Volumen (ReplayGain / -14 LUFS)**:
   - Cálculo del factor de ganancia acústica $gain = 10^{-\frac{loudness}{20.0}}$ limitado a $[0.2, 1.5]$ en [youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py) para eliminar disparidades de volumen entre pistas de YouTube.
   - Persistencia y conmutación en `settings_storage` (`music_loudness_normalization`).
3. **Búsqueda Difusa en Caché a Gran Escala con SQLite FTS5 / Trigramas ($\mathcal{O}(\log N)$)**:
   - Creación de tabla virtual `youtube_search_cache_fts` con tokenizador `trigram` y disparadores automáticos (`AFTER INSERT`, `AFTER UPDATE`, `AFTER DELETE`) en [manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py).
   - Búsqueda difusa aproximada por índice trigrama en tiempo $\mathcal{O}(\log N)$ dentro del motor SQLite con fallback transparente a `SequenceMatcher` en [music_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/music_storage.py).
4. **Overlay Web para OBS con Interpolación Fluida a 60 FPS**:
   - Transición de un timer discontinuo (`setInterval(1000)`) a una interpolación suave y continua de barra de progreso y reloj a 60 FPS mediante `requestAnimationFrame` en [music.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/music/music.html).

---

## 1. Modificaciones Detalladas por Componente

### A. Worker de Resolución y Descarga ([music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py))
- Se añadieron `import time` y `import random`.
- Bucle de reintentos con backoff exponencial (`max_retries = 3`, delay: $1.5^{attempt} + jitter$). Si una estrategia de cliente de YouTube falla por restricciones de red o rate-limit, el worker rota a la siguiente estrategia (`client_strategies.append(client_strategies.pop(0))`).
- Extracción de `info.get('loudness')` o `info.get('loudness_db')` almacenada en `self.loudness: float | None`.
- En `YouTubeSearchWorker`, se implementó reintento con amortiguación de 1s ante fallos antes de activar el fallback a YouTube Music.

### B. Normalización de Volumen en Reproductor ([youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py))
- Inicialización de `self.loudness_normalization_enabled` a partir de `SQLiteSettingsStorage` (`music_loudness_normalization`, por defecto `True`).
- Nuevo método `_calculate_effective_volume() -> float`:
  ```python
  def _calculate_effective_volume(self) -> float:
      base_vol = self._volume_gain
      if not getattr(self, "loudness_normalization_enabled", True):
          return base_vol

      loudness = None
      if self.current_song:
          loudness = self.current_song.get("loudness")

      if loudness is None:
          return base_vol

      try:
          gain_factor = 10.0 ** (-float(loudness) / 20.0)
          gain_factor = max(0.2, min(1.5, gain_factor))
          return max(0.0, min(1.0, base_vol * gain_factor))
      except Exception as e:
          logger.debug("[YouTubeMusicProvider] Error calculating loudness gain: %s", e)
          return base_vol
  ```
- Método público `set_loudness_normalization(enabled: bool)` para permitir al streamer alternar la normalización en caliente.
- En `_on_song_resolved`, se lee la sonoridad del worker y se asigna al diccionario `current_song`, actualizando inmediatamente el volumen efectivo del `QAudioOutput`.

### C. Base de Datos e Índice FTS5 Trigram ([manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py) & [music_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/music_storage.py))
- **Tabla Virtual y Triggers**:
  ```sql
  CREATE VIRTUAL TABLE IF NOT EXISTS youtube_search_cache_fts USING fts5(
      query_raw, title, artist, tokenize='trigram'
  );
  CREATE TRIGGER IF NOT EXISTS trg_yt_cache_insert AFTER INSERT ON youtube_search_cache BEGIN
      INSERT INTO youtube_search_cache_fts(rowid, query_raw, title, artist)
      VALUES (new.rowid, new.query_raw, new.title, new.artist);
  END;
  ```
- **Búsqueda FTS5 en `SQLiteMusicStorage.get_cached_search`**:
  - Tras verificar coincidencia exacta, se consulta `youtube_search_cache_fts MATCH ?` ordenando por `rank`.
  - Si SQLite no tiene soporte FTS5 o la consulta no arroja coincidencias, se ejecuta el fallback clásico con `SequenceMatcher`.

### D. Overlay Web para OBS a 60 FPS ([music.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/music/music.html))
- Se reemplazó el intervalo fijo de 1000ms por un bucle `requestAnimationFrame(tick)` que interpola la posición milisegundo a milisegundo basándose en `performance.now()`.
- La barra de progreso `.progress-bar-fill` ahora avanza de forma completamente fluida a 60 FPS sin tirones visuales.

---

## 2. Pruebas y Verificación

1. **Pruebas de Inicialización de Workers (`test_music_worker.py`)**:
   - Validación de atributos `query_or_url`, `expected_title` y `loudness` en `YouTubeResolveWorker`.
   - Validación de parámetros de búsqueda y fallback en `YouTubeSearchWorker`.
2. **Pruebas de Normalización de Volumen (`test_loudness_normalization.py`)**:
   - Canciones con +6 dB reducen el volumen a ~0.4009.
   - Canciones con -6 dB elevan el volumen respetando la cota máxima clamped de 1.0.
   - Conmutación dinámica `set_loudness_normalization(False / True)` validada.
3. **Pruebas de Caché FTS5 Trigram (`test_fts5_music_cache.py`)**:
   - Comprobación de inserción, búsqueda exacta y búsqueda difusa aproximada por subcadenas (`"queen bohem rhaps"` -> `"Bohemian Rhapsody"`).
4. **Suite Completa**:
   - `uv run pytest resources/tests/unit/`: **255 pruebas unitarias superadas exitosamente (100% pasando)** en 14.43s.

---

## 3. Principios Arquitectónicos y Eficiencia Big-O

- **Big-O en Caché Musical**: Reducción de $\mathcal{O}(N)$ a $\mathcal{O}(\log N)$ utilizando el índice invertido trigrama nativo en C de SQLite.
- **Eficiencia en Reproducción**: Normalización en tiempo $\mathcal{O}(1)$ al cargar pistas.
- **Rendimiento Visual**: 60 FPS continuos en OBS mediante `requestAnimationFrame`, sincronizado con el compositor de la GPU.
