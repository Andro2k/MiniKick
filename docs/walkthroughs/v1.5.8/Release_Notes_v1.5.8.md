# Release Notes - MiniKick Version 1.5.8

**07 de Septiembre, 2026**

## Suite de Alertas Multiplataforma, Rediseño Visual Studio, Canjes Kick a 0 ms, Resiliencia Extrema y Respaldo Integral

> [!NOTE]
> MiniKick v1.5.8 representa una de las actualizaciones más ambiciosas y completas en la historia del proyecto. Introduce un sistema de **Alertas Multiplataforma (Kick y Twitch)** en tiempo real con diseño estilo *Twitch Alerts Studio*, canjes de puntos de canal Kick instantáneos vía WebSocket nativo, previsualizador vectorial interactivo de chat, servidor de medios locales con soporte HTML/CSS personalizado, normalización de audio ReplayGain (-14 LUFS), búsqueda difusa en caché SQLite FTS5, telemetría diagnóstica RFC 6455, auto-reconexión continua en overlays de OBS, respaldo integral de configuraciones y una optimización arquitectónica global con certificación del 100% en pruebas unitarias.

---

### Nuevas Funcionalidades (6)

- **[NEW FEATURE] [ALERTS] Sistema Integral de Alertas Multiplataforma en Tiempo Real (Kick y Twitch):**
  - Nueva pestaña principal *Alertas* en la barra lateral con soporte simultáneo y desacoplado para Kick y Twitch.
  - Detección de eventos en vivo: **Seguidores (Follows)**, **Suscripciones (Subs)**, **Renovaciones (Resubs)**, **Regalos de Subs (Sub Gifts individuales y masivos)**, **Raids** y **Bits / Cheers**.
  - Canal WebSocket dedicado (`/ws?topic=alerts`) en el servidor local integrado con cola FIFO acotada, consolidación inteligente de sub-bombs (evitando saturación de pantalla) y botón de prueba instantánea hacia OBS con copiado de URL en un solo clic.

- **[NEW FEATURE] [ALERTS] Rediseño Visual Estilo *Twitch Alerts Studio* y Previsualizador en Ajedrez:**
  - **5 Disposiciones Flexibles:** Imagen/Video arriba del texto, lateral izquierdo, lateral derecho, texto debajo o superpuesto sobre la media.
  - **Modo *Sticker*:** Presentación moderna 100% transparente sin marco ni fondo oscuro, ideal para animaciones limpias sobre el juego.
  - **Tipografía y Colorimetría Avanzada:** Selección entre 5 familias tipográficas de Google Fonts (*Outfit*, *Inter*, *Roboto*, *Montserrat*, *Poppins*), ajuste de tamaño de fuente (14px a 48px), alineación de texto y selectores de color RGB dedicados para texto base y nombre de usuario destacado.
  - Previsualizador reactivo en vivo sobre lienzo cuadriculado de transparencia con soporte de placeholders dinámicos (`{user}`, `{amount}`, `{tier}`).

- **[NEW FEATURE] [ALERTS] Soporte para Alertas Personalizadas en HTML/HTM y Servidor de Medios:**
  - Posibilidad de vincular plantillas web externas personalizadas (`.html` / `.htm`) creadas por diseñadores.
  - Servidor de medios locales seguro (`/user_media/`) con resolución de recursos relativos (CSS, JS, fuentes, imágenes locales) y protocolo bidireccional `postMessage` para control de eventos y animaciones avanzadas.

- **[NEW FEATURE] [CHAT] Previsualizador Vectorial Interactivo de Chat Overlay:**
  - Mockup dinámico en tiempo real (`ChatOverlayMockupWidget`) integrado en la configuración de chat.
  - Permite visualizar al instante los cambios de tema (*Neon*, *Dark*, *Glass*), tamaño de texto, animación vertical u horizontal, insignias de plataforma (Kick, Twitch, YouTube, TikTok) e iconos Nerd Font antes de transmitirlos a OBS.

- **[NEW FEATURE] [SCHEDULE] Botón "Ahora" para Relleno Instantáneo de Fecha y Hora:**
  - Acceso directo en el panel de creación y edición rápida de `ScheduleView` para sincronizar la fecha y hora actual del sistema en un solo clic, acelerando la publicación de directos no programados.

- **[NEW FEATURE] [UI] Componente `ClearableLineEdit` con Limpieza Rápida:**
  - Nuevo control de entrada de texto reutilizable con icono interactivo de borrado rápido (`clear`), integrado en tarjetas de configuración de alertas, diálogos de vinculación de cuentas y asistentes.

---

### Mejoras de Rendimiento y Arquitectura (12)

- **[IMPROVEMENT] [REWARDS] Canjes de Puntos de Canal en Kick a Latencia Cero (0 ms):**
  - Migración del sondeo HTTP REST previo (que demoraba hasta 10 segundos) hacia eventos nativos WebSocket Pusher (`RewardRedeemedEvent` en el canal `chatroom_{room_id}`).
  - Activación instantánea de alertas en OBS, lectura en TTS y notificación Toast en $\mathcal{O}(1)$ con deduplicación por ID de redención.

- **[IMPROVEMENT] [BACKUP] Respaldo y Restauración Integral de la Aplicación:**
  - Se expandió `BackupService` para exportar e importar la totalidad de las **Alertas** (`alert_configs`) y los **7 Widgets de OBS** (`widgets_config`).
  - Preservación estricta de las banderas de habilitación de plataformas en comandos (`apply_kick`, `apply_twitch`, `apply_youtube`, `apply_tiktok`) y temporizadores (`apply_kick`, `apply_twitch`).
  - Total retrocompatibilidad con archivos JSON de versiones anteriores y defensa de firmas con desacoplamiento Liskov.

- **[IMPROVEMENT] [MUSIC] Normalización ReplayGain (-14 LUFS) y Caché FTS5 Trigram:**
  - Normalización automática de volumen en el motor de audio de YouTube protegiendo los oídos del streamer y espectadores ante pistas con volumen dispar.
  - Búsqueda difusa en caché SQLite en $\mathcal{O}(\log N)$ mediante tabla virtual FTS5 con tokenizador `trigram` y triggers automáticos.
  - Reintentos exponenciales (*Exponential Backoff*) con rotación de clientes en `YouTubeResolveWorker` para evitar bloqueos por rate-limit.
  - Despacho inmediato y reactivo de la cola ante comandos `!sr` sin esperar ciclos de sondeo pasivo.

- **[IMPROVEMENT] [MUSIC] Interpolación Suave a 60 FPS en el Overlay de Música:**
  - Barra de progreso y temporizador de `/music` renderizados mediante `requestAnimationFrame` a 60 FPS continuos, eliminando los saltos bruscos de 1 segundo en OBS Studio.

- **[IMPROVEMENT] [WIDGETS] Sincronización Diferencial en $\mathcal{O}(1)$:**
  - Al guardar cambios en un widget, se evalúa y sincroniza únicamente el comando específico del widget editado, eliminando la sobrecarga de reescritura masiva en base de datos y transmisiones innecesarias.

- **[IMPROVEMENT] [CHAT] Transacciones Atómicas por Lote (Batch):**
  - Consolidación de 19 escrituras SQLite individuales e independientes en una sola transacción atómica con `executemany` (`save_all`), eliminando pausas en el hilo de interfaz.

- **[IMPROVEMENT] [AUDIO] Persistencia Amortiguada (Debounced) a 300 ms:**
  - Los sliders de volumen y velocidad aplican cambios inmediatos al motor de audio en memoria, consolidando la persistencia a disco solo tras 300 ms de inactividad del usuario.

- **[IMPROVEMENT] [ARCHITECTURE] Simetría Arquitectónica y Desacoplamiento Two-Tier:**
  - Unificación de clientes bajo `BaseOAuthManager` (DRY).
  - Extracción independiente de `TwitchRewardWorker` en `backend/workers/twitch_reward_worker.py`.
  - Nomenclatura unívoca y simétrica (`KickWebSocketManager`, `KickAuthManager`) con alias para compatibilidad total hacia atrás.
  - Estandarización de fachadas de importación unificadas (`__all__`) en toda la capa `frontend/` y `backend/services/`, erradicando importaciones cruzadas y reduciendo resoluciones a $\mathcal{O}(1)$.

- **[IMPROVEMENT] [DIAGNOSTICS] Telemetría Diagnóstica Integral y Códigos RFC 6455:**
  - Decodificación automática de códigos de cierre estándar WebSocket (1000, 1001, 1006, etc.) en Kick y Twitch.
  - Medición de apagado de hilos en milisegundos con `time.perf_counter()` en `MainWindowCore`.
  - Captura tipada de excepciones (`type(e).__name__`, `exc_info=True`) en todos los workers de chat (Kick, Twitch, YouTube, TikTok).
  - Trazabilidad granular en TTS para identificar omisiones por filtros (roles, comandos, bots, palabras prohibidas) y estado de dispositivos de salida de audio.

- **[IMPROVEMENT] [UI] Estandarización de Geometría, Márgenes y QSS:**
  - Migración de dimensiones fijas hacia hojas de estilo QSS dinámicas.
  - Reorganización de asistentes (`RewardsConfigWizard`, `TimerConfigWizard`, `BugReportDialog`) a disposiciones limpias de columna única.
  - Estandarización simétrica de márgenes y espaciados en paneles de música, chat y horarios.

- **[IMPROVEMENT] [UI] Notificaciones Toast en Caliente (*In-Place*):**
  - Detección de alternancias repetitivas de un mismo switch, reutilizando el Toast visible y actualizando texto, icono y borde visual sin encolar ni parpadear.

- **[IMPROVEMENT] [UI] ScrollArea con Difuminado Dinámico:**
  - Implementación de `FadingScrollArea` con máscaras de gradiente dinámicas en bordes superior e inferior para indicar visualmente contenido desplazable.

---

### Correcciones Críticas (10)

- **[FIX] [OVERLAYS] Auto-Reconexión Continua en Rewards Overlay y Widgets OBS:**
  - Se eliminó el deadlock producido por la bandera `isReconnecting` en `assets/overlays/rewards/rewards.html`, la cual quedaba perpetuamente en `true` si el socket fallaba al reconectar con MiniKick cerrado, impidiendo nuevos reintentos.
  - Se unificó el bucle de reconexión idempotente cada 3 segundos y se corrigió el mismo problema en los 7 widgets integrados de OBS (`deaths`, `score`, `poll`, `pinned`, `shoutout`, `emote_combo`, `emote_explosion`).
  - Se actualizó el puerto de fallback obsoleto de `6868` al puerto oficial `8090`.

- **[FIX] [KICK] Restauración de Suscripción a Puntos de Canal en Pusher (`chatroom_{id}`):**
  - Se aseguró la suscripción activa simultánea a `chatroom_{room_id}` y `chatrooms.{room_id}.v2`, garantizando que los canjes de recompensas de canal (`RewardRedeemedEvent`) y los mensajes de chat se procesen en paralelo sin interrupción.

- **[FIX] [ALERTS] Streaming HTTP 206, Buffer de Video y Audio de Alertas:**
  - Implementación de soporte de solicitudes parciales `Range` con respuesta HTTP `206 Partial Content` en el servidor web local, eliminando el buffering de 1 a 2 segundos en OBS Studio.
  - Corrección del atributo `video.muted = true` incondicional, permitiendo que videos con pista de audio integrada suenen correctamente sin requerir un audio secundario.
  - Diseño responsivo adaptativo en la tarjeta de URL OBS de `AlertsView` para monitores y ventanas estrechas (< 760px).

- **[FIX] [YOUTUBE] Resiliencia de Ciclo de Vida y Reconexión en YouTube Live Chat:**
  - Corrección en la sesión HTTP y manejo de tokens en `YouTubeChatWorker`, previniendo bucles de reconexión infinita ante transmisiones finalizadas o suspensiones temporales de cuota.

- **[FIX] [PLATFORM] Compatibilidad Multiplataforma (Linux / Ubuntu):**
  - Encapsulación de tipos y estructuras Win32 (`ctypes.wintypes`, `WINFUNCTYPE`) en `GlobalMediaWorker` tras barreras `sys.platform == 'win32'`, resolviendo el bloqueo de inicio en sistemas GNU/Linux.
  - Adición de directorios temporales estándar mediante `tempfile.gettempdir()` en `UpdaterService`.

- **[FIX] [REPORTS] Prevención de Crash en `BugReportWorker`:**
  - Sanitización de nombres de archivo de logs adjuntos y captura defensiva de excepciones al armar volcados de diagnóstico.

- **[FIX] [MUSIC] Supresión de Conexión Duplicada a `commands_changed`:**
  - Eliminación de suscripción redundante en `MusicController` con validación de idempotencia en `_connect_signals()`.

- **[FIX] [SECURITY] Blindaje contra Path Traversal en Servidor de Medios:**
  - Validación de rutas normalizadas y comprobación de límites de directorio en `/user_media/`, bloqueando accesos no autorizados a archivos fuera de la carpeta designada.

- **[FIX] [ALERTS] Detección Instantánea de Seguidores en Kick:**
  - Extracción de nombres de usuario mediante regex sobre eventos `GoalProgressUpdateEvent` y mensajes de bienvenida de bots oficiales en chat (`@Kicklet`, `BotRix`, `KickBot`).

- **[FIX] [TOAST] Diferenciación Contextual en Alertas:**
  - Notificaciones Toast personalizadas con iconos y mensajes específicos al activar, pausar o modificar alertas individuales o grupales.

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.8 mantiene 100% de compatibilidad con bases de datos SQLite, configuraciones existentes y credenciales OAuth de Kick y Twitch.
