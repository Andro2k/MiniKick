# 🎵 MiniKick - Hoja de Ruta y Mejoras Futuras: Sistema de Música

**Módulo**: Sistema de Música (`backend/providers/music/`, `backend/database/music_storage.py`, `backend/database/cache_manager.py`, `frontend/views/music_view.py`)  
**Fecha de Creación**: 02 de Septiembre, 2026  
**Estado**: Propuestas de Diseño y Arquitectura para Versiones Posteriores

---

## 📑 Resumen Ejecutivo

El sistema de música actual de MiniKick cuenta con una base sólida: persistencia en SQLite con modo WAL, caché inteligente con matching difuso en $\mathcal{O}(1)$, algoritmo de evicción ponderada multicriterio (frecuencia, recencia y peso en MB), pre-descarga asíncrona y controles multimedia globales de teclado.

Este documento recopila las especificaciones técnicas y requerimientos arquitectónicos para futuras expansiones del módulo musical.

---

## 🚀 Propuestas de Actualización

```
docs/future_updates/
 └── MUSIC_SYSTEM_ROADMAP.md  <-- Este documento
```

---

### 1. 📂 Playlists y Listas de Reproducción Personalizadas (Local & Streamer Presets)

#### 🎯 Objetivo
Permitir al streamer crear, guardar, exportar y reproducir listas temáticas locales (ej. *"Música Chill"*, *"Gaming / Hype"*, *"Lofi Hip Hop"*, *"Rock Clásico"*) que sirvan como lista de respaldo automática cuando la cola de peticiones de los espectadores esté vacía.

#### 🏗️ Diseño de Base de Datos (SQLite)
```sql
-- Tabla de Playlists
CREATE TABLE IF NOT EXISTS music_playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Canciones por Playlist
CREATE TABLE IF NOT EXISTS music_playlist_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    url TEXT NOT NULL,
    duration TEXT DEFAULT '-',
    track_order INTEGER NOT NULL,
    FOREIGN KEY(playlist_id) REFERENCES music_playlists(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_playlist_tracks_order ON music_playlist_tracks(playlist_id, track_order);
```

#### 🧩 Integración Arquitectónica
- **Autoplay en Cola Vacía**: Cuando `self.queue` se vacíe y el modo *"Playlist de Respaldo"* esté activo en ajustes, el reproductor tomará la siguiente pista de la playlist seleccionada en orden secuencial o aleatorio (Shuffle).
- **Prioridad de Espectadores**: Cualquier comando de petición de chat (`!sr`, `!play`) mantendrá prioridad $\mathcal{O}(1)$ sobre la playlist de respaldo.

---

### 2. 🔊 Normalización Automática de Volumen (Loudness Normalization / ReplayGain)

#### 🎯 Objetivo
Eliminar variaciones drásticas de volumen entre diferentes videos y canciones de YouTube para proteger los oídos del streamer y de los espectadores.

#### 🏗️ Enfoque Técnico
1. **Extracción de Ganancia con `yt-dlp`**:
   - Analizar metadatos de volumen integrados (`volume` / `loudness` / `loudness_db`) proporcionados por los metadatos de YouTube.
2. **Ajuste Dinámico de Ganancia en `QAudioOutput`**:
   - Ajustar el multiplicador de volumen del reproductor en base al valor normalizado respecto al nivel objetivo (ej. -14 LUFS estándar de streaming).
   ```python
   # target_lufs = -14.0
   # gain_factor = 10 ** ((target_lufs - track_loudness) / 20.0)
   # final_volume = base_volume * gain_factor
   ```

---

### 3. 🔍 Búsqueda Difusa a Gran Escala con SQLite FTS5 / Trigramas

#### 🎯 Objetivo
Escalar el motor de búsqueda en caché cuando la base de datos local contenga miles de pistas consultadas, reduciendo el tiempo de coincidencia difusa de $\mathcal{O}(N)$ en Python a $\mathcal{O}(\log N)$ directamente en el motor C nativo de SQLite.

#### 🏗️ Enfoque Técnico
- Activar la tabla virtual `fts5` con tokenizador `trigram`:
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS youtube_cache_fts USING fts5(
    query_raw,
    title,
    artist,
    tokenize='trigram'
);
```
- Realizar consultas aproximadas instantáneas con soporte para errores tipográficos (`typos`) directamente en SQLite.

---

### 4. 🌐 Cola de Descargas Resiliente con Reintentos Exponenciales

#### 🎯 Objetivo
Mejorar la estabilidad del preloading en conexiones con alta latencia o pérdida de paquetes mediante reintentos con *Exponential Backoff*.

#### 🏗️ Enfoque Técnico
- Si la descarga asíncrona de `yt-dlp` falla por un `HTTP 429 (Too Many Requests)` o timeout de socket:
  - Intento 1: Reintento inmediato tras 1s.
  - Intento 2: Reintento tras 3s.
  - Intento 3: Si persiste el fallo, omitir y notificar al chat de forma no bloqueante.

---

### 5. 🎚️ Overlays Web para OBS con Barra de Progreso Fluida

#### 🎯 Objetivo
Mejorar el overlay web del navegador (`/overlay/music`) para mostrar portadas animadas en alta definición, ecualizador visual dinámico CSS y barras de tiempo sincronizadas mediante WebSockets / SSE.

---

## 📌 Historial de Versiones y Referencias
- **MiniKick Core**: `v1.5.7`
- **Autor**: Equipo de Arquitectura MiniKick
