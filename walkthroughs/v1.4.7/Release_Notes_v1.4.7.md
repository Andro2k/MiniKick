# Release Notes - MiniKick Version v1.4.7

> [!NOTE]
> MiniKick v1.4.7 introduce una gran actualización enfocada en rendimiento visual de alta velocidad, estabilidad en reproducciones de audio y video, nuevos widgets interactivos acelerados por hardware y monitoreo detallado de la infraestructura de red.

---

## Novedades Destacadas

> [!IMPORTANT]
> **Motor Canvas 2D Acelerado por GPU para Widgets Overlay**
> - **Ráfagas de Emotes a 60 FPS sin Lag:** Reescritura completa del widget de explosión de emotes migrando de nodos del DOM a un lienzo HTML5 Canvas 2D. Permite renderizar ráfagas masivas de 50, 100 o más partículas a 60 FPS estables sin provocar tirones ni reflows en OBS.
> - **Rango de Partículas Configurable:** Se amplió la capacidad en la configuración del widget para permitir ráfagas de 5 a 100 emoticones.
> - **Barra de Combo Fluida:** Animación del temporizador del combo de emotes migrada a requestAnimationFrame eliminando saltos de fotogramas.

---

## Rediseño Integral de Overlays (Chat y Música)

- **Chat Overlay Responsivo:** Soporte para modo Vertical y modo Marquesina Ticker Horizontal con insignias inline (STREAMER, BOT, MODERATOR) y colores pastel personalizados por usuario.
- **5 Diseños de Reproductor de Música:**
  1. Vinyl: Tocadiscos retro con disco de vinilo en rotación 360 grados continua.
  2. Banner: Tarjeta vertical tipo poster con portada extendida.
  3. Pill: Cápsula minimalista horizontal con ecualizador animado.
  4. Compact: Tarjeta apilada compacta.
  5. Standard: Barra de reproducción clásica extendida.
- **Legibilidad y Sincronización:** Tipografía de alto contraste con text-shadow profundo y sincronización en tiempo real del progreso de la canción tras recargas de OBS.

---

## Monitoreo de Red Multitrama en Tiempo Real

> [!TIP]
> **Soporte para 6 Servicios Clave**
> Seguimiento dinámico continuado (50 muestras) para Internet, Kick API, Chat WebSocket, Overlay Local, Spotify API y YouTube.

- **Barra de Filtros (Pills):** Permite aislar servicios individuales o visualizar la gráfica global con un solo clic.
- **Métricas de Estabilidad:** Cálculo en O(N) de Ping Actual, Promedio, Mínimo, Máximo, Jitter (variación en ms) e Indicador de Estabilidad (Óptima, Buena, Regular, Deficiente).

---

## Motor TTS Ultra Estabilizado y Soporte de Emojis y Emotes

- **Instancias de Audio Aisladas:** Eliminada la interrupción de audio mid-sentence mediante instancias dedicadas de reproducción de audio.
- **Pronunciación de Emotes y Emojis:** Los emotes de Kick dicen su nombre nativo en lugar de descartarse. Microsoft Edge TTS pronuncia emojis Unicode.
- **Resiliencia en Red:** Sanitización de textos para evitar solicitudes vacías y mecanismo de reintentos con backoff exponencial.

---

## Filtro Anti-Spam Inteligente sin Falsos Positivos

- **Descuento de Emotes de Kick:** La protección de símbolos y caracteres extraños elimina las etiquetas de emotes antes del cálculo, evitando sanciones injustas a usuarios legítimos.
- **Límite de Caracteres por Mensaje:** Filtro de bloques de texto refinado con rangos de 50 a 2000 caracteres e inspección de saltos de línea.
- **Interfaz Dinámica:** Desactivación automática del selector de tiempo cuando la sanción elegida no requiere timeout.

---

## Seguridad en Respaldos y Bypass Anti-Bot de YouTube

> [!WARNING]
> **Bypass de Detección de Bot en YouTube**
> Estrategia cascada prioritaria en yt-dlp eliminando bloqueos anti-bot y log-spamming.

- **Salto Automático de Canciones:** Avance inmediato en menos de 1.5s ante videos con restricción de edad, notificando amigablemente en el chat de Kick.
- **Seguridad en Respaldos:** Aislamiento de fichas de sesión de overlay en exportaciones JSON y derivación dinámica de metadata usando la versión de la aplicación.

---

## Comparativa de Eficiencia y Rendimiento (Big-O)

| Módulo / Operación | Comportamiento Anterior | Optimización v1.4.7 | Impacto en Rendimiento |
|---|---|---|---|
| Renderizado de Explosión de Emotes | Nodos DOM por fotograma | Lienzo HTML5 Canvas 2D GPU | 60 FPS estables con 100+ partículas sin DOM reflows |
| Monitoreo de Red | 2 servicios fijos | 6 servicios con matriz O(N) | Monitoreo en tiempo real de toda la infraestructura |
| Sanitización de Errores YouTube | Retraso de 15s en lectura de cookies | Fallo rápido O(1) en menos de 1.5s | Salto automático inmediato sin congelar la lista |
| Procesamiento de Filtros Anti-Spam | Falsos positivos con emotes | Regex O(N) con strip previo de emotes | 0 sanciones erróneas por emoticones de Kick |
| Reproductor TTS | Instancia compartida (interrupción) | Instancias aisladas con borrado diferido | Reproducción continua e ininterrumpida de chat |

---

> [!CAUTION]
> **Notas de Actualización:**
> Si utilizas el widget de Explosión de Emotes en OBS, puedes aumentar libremente el límite de partículas a 50 o 100 desde la sección de Widgets para disfrutar de ráfagas ultra fluidas a 60 FPS.
