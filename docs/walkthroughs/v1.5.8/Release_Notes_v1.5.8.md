# Release Notes - MiniKick Version 1.5.8

**02 de Septiembre, 2026**

## Optimización Extrema de Rendimiento, Sincronización Diferencial y Respuesta In-Place en Notificaciones

> [!NOTE]
> MiniKick v1.5.8 se enfoca en la optimización exhaustiva del hilo de interfaz (UI Thread) y la persistencia en base de datos SQLite. Se erradican las tormentas de sincronización masiva en widgets, se unifican las escrituras de configuración de Chat/TTS en transacciones atómicas batch por lote, se amortigua la persistencia de audio y se rediseña el ciclo de vida de los Toasts para brindar una alternancia de switches instantánea y libre de lag.

### Nuevas Funcionalidades (1)

- **[NEW FEATURE] [ALERTS] Interfaz de Configuración de Alertas Multiplataforma en Tiempo Real:** Nueva pestaña *Alertas* en la barra lateral con soporte dedicado para Kick y Twitch. Permite personalizar sonidos (.mp3, .wav, .ogg), imágenes/videos (.gif, .mp4, .webm), plantillas de texto interactivo (`{user}`, `{amount}`, `{tier}`), duración, volumen, lectura TTS y botón de prueba instantánea hacia OBS con copiado de URL en un clic.

---

- **[IMPROVEMENT] [REWARDS] Canjes de Puntos de Canal en Kick en Tiempo Real vía WebSocket (0 ms):** Migración del procesamiento de canjes de recompensas de Kick hacia eventos nativos WebSocket Pusher (`RewardRedeemedEvent` en el canal `chatroom_{chatroom_id}`). Erradica la latencia de 10 segundos del sondeo HTTP REST anterior, disparando de forma instantánea el overlay, chat y toast con deduplicación en $\mathcal{O}(1)$.
- **[IMPROVEMENT] [ARCHITECTURE] Separación y Nomenclatura Simétrica Kick vs Twitch:** Se extrajo `TwitchRewardWorker` a su propio archivo independiente (`backend/workers/twitch_reward_worker.py`), y se estandarizaron los componentes de Kick con nombres unívocos (`KickWebSocketManager`, `KickAuthManager`, `kick_chat_worker`, `kick_auth_manager`) equilibrando simétricamente la arquitectura con Twitch y preservando 100% de compatibilidad hacia atrás mediante alias.
- **[IMPROVEMENT] [ALERTS] Detección Instantánea de Seguidores en Kick:** Monitoreo activo de `GoalProgressUpdateEvent` y extracción de nombres de usuario mediante regex sobre saludos de bots en chat (`@Kicklet`, `BotRix`, `KickBot`), garantizando la activación inmediata de alertas visuales y de audio al recibir nuevos follows en Kick.
- **[IMPROVEMENT] [ALERTS] Arquitectura Backend de Alertas Multiplataforma (Kick y Twitch) y Plantilla Base de Overlays:** Sistema completo de detección de Follows, Subs, Resubs, Regalos de Subs, Raids y Bits en tiempo real para Kick y Twitch. Incluye persistencia SQLite con cache $\mathcal{O}(1)$, cola FIFO con consolidación de regalos masivos (sub bombs), canal WebSocket dedicado (`/ws?topic=alerts`) y plantilla base en `/alerts` con Glassmorphism, Google Fonts, audio y video.
- **[IMPROVEMENT] [WIDGETS] Sincronización Diferencial de Comandos en $\mathcal{O}(1)$:** Desacoplamiento de la sincronización masiva al guardar widgets. Ahora solo se evalúa y sincroniza el comando asociado al widget modificado, omitiendo la escritura en base de datos y la emisión de señales si los atributos no sufrieron cambios.
- **[IMPROVEMENT] [CHAT] Transacción Atómica Batch en Persistencia de Chat/TTS:** Reducción de 19 transacciones SQLite individuales e independientes a una única transacción atómica por lote con `save_all` (`executemany`), eliminando los bloqueos síncronos en disco en el hilo principal.
- **[IMPROVEMENT] [AUDIO] Persistencia Amortiguada (Debounced) en Parámetros de Audio:** Arrastrar los sliders de volumen y velocidad ahora aplica los cambios en el motor de audio a 60 FPS en memoria de forma instantánea, consolidando la persistencia a SQLite tras 300 ms de inactividad para evitar congelamientos de interfaz.
- **[IMPROVEMENT] [ARCHITECTURE] Auditoría y Modernización Integral de Fachadas de Importación:** Estandarización de toda la capa de `frontend/` (`frontend.common`, `frontend.widgets`, `frontend.views`, `frontend.navigation`, `frontend.dialogs`, `frontend.components`) y módulos de arranque (`main.py`, `app_container_core.py`, `main_window_core.py`) bajo el patrón de fachadas unificadas con `__all__`. Erradicación al 100% de importaciones profundas hacia submódulos internos y desacoplamiento total de proveedores de backend (`kick_websocket.py`) respecto a dependencias de interfaz de usuario. Resoluciones de módulos en $\mathcal{O}(1)$ y certificación con 239 pruebas unitarias superadas al 100%.
- **[IMPROVEMENT] [TOAST] Actualización en Caliente (*In-Place*) de Notificaciones de Estado:** El sistema de Toasts ahora detecta alternancias rápidas de un mismo switch (ej. encender/apagar repetidamente), actualizando el texto, icono y borde visual sobre el mismo widget visible sin destruirlo, sin acumular colas y sin generar colisiones de animación.

---

### Correcciones (3)

- **[FIX] [MUSIC] Eliminación de Conexión Redundante a `commands_changed`:** Se suprimió la suscripción duplicada en el constructor de `MusicController` y se implementó protección de idempotencia en `_connect_signals()`, evitando que los slots de sincronización de switches se ejecuten por duplicado ante cada evento de comandos.
- **[FIX] [ALERTS] Audio de Video, Streaming HTTP 206 y Layout Flex Responsivo:** Se corrigió el atributo `video.muted = true` incondicional en el overlay de alertas permitiendo que los videos con pista de audio suenen correctamente a menos que se configure un sonido dedicado. Se implementó soporte de solicitudes parciales `Range` con HTTP `206 Partial Content` en el servidor de overlays erradicando el retardo de 1-2s por buffering de medios en Chromium/OBS. Se rediseñó la card de URL OBS en `AlertsView` con un `QBoxLayout` responsivo que se adapta dinámicamente en anchos estrechos (< 760px).
- **[FIX] [PLATFORM] Compatibilidad Multiplataforma y Corrección de Inicio en Ubuntu/Linux:** Se aisló la importación y definición de estructuras Win32 (`ctypes.wintypes`, `ctypes.WINFUNCTYPE`, `KBDLLHOOKSTRUCT`) en `GlobalMediaWorker` tras una barrera condicional `sys.platform == 'win32'`, resolviendo el fallo de arranque por `AttributeError: module 'ctypes' has no attribute 'WINFUNCTYPE'`. Se añadió fallback seguro a `tempfile.gettempdir()` en `UpdaterService` y detección de librerías `.so` para silenciamiento de logs nativos de FFmpeg en Linux.

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.8 mantiene total compatibilidad con configuraciones, bases de datos y tokens existentes.
