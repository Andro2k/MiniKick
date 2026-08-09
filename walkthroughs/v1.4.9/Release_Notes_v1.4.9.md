# Release Notes - MiniKick Version v1.4.9

> [!NOTE]
> MiniKick v1.4.9 representa una actualización integral del ecosistema. Consolida **10 avances fundamentales** desarrollados a lo largo de la versión: **Extensión del Almacenamiento Local a 5 GB (5000 MB)**, **Inspector de Kick WebSocket con Modo RAW y Registro en Tiempo Real**, **API Pública de Kick v2 (`/rewards`)**, **Widgets OBS Overlay en Vivo para Encuestas (`poll.html`) y Mensajes Fijados (`pinned.html`)**, **Chat Overlay Enriquecido (Niveles `badges_v2` & Badge `OG`)**, **Modularización del Servidor Overlay (`backend/services/overlay/`)**, **Separación de Comandos de Música (`MusicCommandHandler`)**, **Fix de Carga Diferida del Overlay de Música al Inicio**, **Encapsulamiento del Diálogo de Actualizaciones (`UpdateController`)**, **Menú Lateral con Scroll Adaptativo (`Sidebar`)**, **Protección de Foco en ComboBoxes (`NoWheelComboBox`)** y **Cumplimiento Estricto del Sistema de Temas (Cero `setStyleSheet` Inline en el Frontend)**.

---

## Novedades Destacadas v1.4.9

> [!IMPORTANT]
> **1. Almacenamiento de Música a 5 GB (5000 MB) & Reuso Instantáneo en Disco**
>
> - **Extensión de Caché a 5 GB:** En [cache_manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/cache_manager.py), el límite `DEFAULT_MAX_CACHE_MB` se incrementó a `5000` (5 GB).
> - **Persistencia de Audio:** Eliminada la instrucción de borrado automático `os.remove()` al finalizar canciones. Los archivos permanecen almacenados en `%LOCALAPPDATA%\.Minikick\cache\yt_<id>.*`.
> - **Reuso Instantáneo ($\mathcal{O}(1)$ Red):** Al volver a pedir una canción guardada, la verificación por Video ID (`yt_<video_id>.*`) se realiza en disco en 0.01 segundos con **0 descargas y 0 peticiones HTTP a YouTube**.
> - **Gestión Inteligente LFU/LRU:** Las canciones se purgan únicamente al superar los **5 GB**, eliminando en primer lugar los archivos con menor reproducción (`play_count`) y más antiguos (`last_accessed`).

> [!IMPORTANT]
> **2. Inspector en Tiempo Real de Kick WebSocket (`test_kick_websocket_live.py`)**
>
> - **Monitoreo de Eventos en Vivo:** Herramienta interactiva ([test_kick_websocket_live.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_kick_websocket_live.py)) para inspeccionar `ChatMessageEvent`, `GiftedSubscriptionsEvent`, `SubscriptionEvent`, `StreamHostEvent`, `PollUpdateEvent`, `UserBannedEvent`, `UserUnbannedEvent` y métricas de espectadores.
> - **Modo RAW (`--raw` / `-r`):** Visualización del paquete JSON 100% en crudo para auditoría de Pusher.
> - **Registro en Archivo:** Grabación en tiempo real en `tests/logs/ws_<canal>_YYYY-MM-DD_HH-MM-SS.log`.

> [!IMPORTANT]
> **3. Arquitectura Kick API Client & Consumo Público v2**
>
> - **Centralización SoR:** Eliminadas las peticiones `requests` directas en capas de servicio ([widget_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/widget_service.py)), canalizando todo el tráfico a través del cliente [kick_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_client.py) mediante `ScraperFactory`.
> - **Soporte para API Pública v2 (`/rewards`):** Método `fetch_public_channel_rewards(channel_slug)` para consultar las recompensas de canal públicas de cualquier streamer sin requerir tokens OAuth.

> [!IMPORTANT]
> **4. Captura de Encuestas en Vivo (OBS Overlay Widget `poll.html`)**
>
> - **Widget Web de Encuestas:** Creación del overlay [poll.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/poll.html) con diseño glassmorphism, barras de progreso animadas en gradiente verde, temporizador y conteo de votos en tiempo real.
> - **Eventos WebSocket de Encuestas:** Servidor [overlay_server.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/overlay/overlay_routes.py) emite `poll_update` y `poll_delete` hacia OBS en tiempo real.

> [!IMPORTANT]
> **5. Mensaje Fijado OBS Overlay & Chat Overlay Enriquecido (Niveles `badges_v2` & Badge `OG`)**
>
> - **Pinned Message Overlay (`pinned.html`):** Banner dinámico en pantalla ([pinned.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/pinned.html)) que muestra mensajes fijados en el chat de Kick en tiempo real con persistencia en OBS.
> - **Chat Overlay Enriquecido (`chat.html`):** Renderizado de niveles de usuario (`badges_v2` -> `Lvl X`), insignias `OG`, VIP, Mod, Sub y Broadcaster.

> [!IMPORTANT]
> **6. Modularización del Servidor Overlay (`backend/services/overlay/`)**
>
> - **Descomposición del Monolito:** El archivo legacy `overlay_server.py` (802 líneas) fue refactorizado y dividido en tres módulos dentro de [backend/services/overlay/](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/overlay/):
>   - [websocket_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/overlay/websocket_client.py): Trama binaria WebSocket RFC 6455 y desenmascaramiento XOR vectorizado.
>   - [overlay_routes.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/overlay/overlay_routes.py): Enrutador HTTP con tabla de despacho $\mathcal{O}(1)$ (`STATIC_ENDPOINTS_MAP`), caché RAM de activos estáticos (`_ASSET_CACHE`) y transmisiones SSE unificadas.
>   - [overlay_manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/overlay/overlay_manager.py): Gestor HTTP global, tokens de seguridad y difusión multitema thread-safe.
> - **Promoción de Dominio:** `overlay` promovido a servicio de dominio de primer nivel en `backend/services/overlay/`.

> [!IMPORTANT]
> **7. Refactorización de Controlador y Delegación de Comandos (`MusicCommandHandler`)**
>
> - **Separación de Responsabilidades (SRP):** Lógica de comandos de chat bot (`!sr`, `!skip`, `!song`, `!pause`, `!resume`, `!playlist`, `!vol`) extraída a [music_command_handler.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/music_command_handler.py).
> - **Reducción de Controlador:** [music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py) reducido de 584 a ~380 líneas.
> - **Despacho $\mathcal{O}(1)$ & Paginación:** Dispatch Table en tiempo constante $\mathcal{O}(1)$ y paginación de playlist por espectador (`MAX_PER_MSG = 8`).

> [!IMPORTANT]
> **8. Corrección del Inicio del Overlay de Música con Carga Diferida**
>
> - **Sondeo en Segundo Plano al Iniciar:** Inicialización de `_init_youtube_provider()` ejecutada en el constructor `__init__` de `MusicController`.
> - **Broadcasting Instantáneo:** El reproductor y el sondeo inician al arrancar la app (`view=None`). El overlay `/music` en navegador recibe eventos `song_changed` al instante sin requerir abrir la pestaña "Music".

> [!IMPORTANT]
> **9. Encapsulamiento de Diálogos de Actualización & Simplificación de `MainWindowCore`**
>
> - **Centralización en `UpdateController`:** Método `show_update_dialog(...)` en [update_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/update_controller.py) que gestiona `UpdateDialog`, callbacks y reinicio.
> - **Reducción de `MainWindowCore`:** Reducido [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/core/main_window_core.py) de 782 a ~730 líneas.

> [!IMPORTANT]
> **10. Mejoras en la Interfaz de Usuario & Sistema de Diseño Centralizado**
>
> - **Sidebar con Scroll Adaptativo:** [sidebar_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py) con `QScrollArea` transparente para albergar módulos ilimitados.
> - **Control de Foco en ComboBoxes (`NoWheelComboBox`):** `FocusPolicy.StrongFocus` en [utils.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/utils.py) previniendo cambios de selección involuntarios al desplazar la rueda del ratón.
> - **Limpieza de Filtro Redundante:** Removido `combo_filter` del panel de [log_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/log_view.py), usando exclusivamente el filtro de encabezado de `ModernTableWidget`.
> - **Cero `setStyleSheet` Inline:** Creado el rol `QPushButton[role="filter_chip"]` en [theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) y migrado [network_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/network_view.py). 0 estilos CSS inline en todo el frontend.

---

## Comparativa de Eficiencia y Rendimiento (Big-O)

| Módulo / Operación            | Comportamiento Anterior                          | Optimización v1.4.9                                                       | Impacto en Rendimiento                                        |
| ----------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Límite de Caché de Música     | Límite restringido a 1 GB                        | Extensión a **5 GB (5000 MB)** en `MusicCacheManager`                     | Mayor almacenamiento de canciones locales en disco            |
| Reuso de Canciones Repetidas  | Peticiones HTTP repetidas                        | Verificación por ID en disco $\mathcal{O}(1)$                             | Reproducción instantánea en **0.01s** sin uso de red          |
| Encuestas de Kick en OBS      | Sin widget dinámico                              | Overlay Web `poll.html` en tiempo real vía WebSocket                      | Visualización interactiva de encuestas en transmisión         |
| Mensajes Fijados de Kick      | Sin widget dinámico                              | Overlay Web `pinned.html` en tiempo real vía WebSocket                    | Banner dinámico en pantalla para destacar mensajes            |
| Chat Overlay                  | Solo badges básicas                              | Niveles `badges_v2` (`Lvl X`) + Badge `OG`                                | Identidad visual enriquecida para los viewers                 |
| Servidor Overlay HTTP/WS      | Monolito de 802 líneas                           | Paquete `backend/services/overlay/` con mapa $\mathcal{O}(1)$ y RAM Cache | Despacho de rutas en **$\mathcal{O}(1)$** y código modular    |
| Controlador de Música         | 584 líneas con comandos mezclados                | Delegación en `MusicCommandHandler` con Dispatch Table $\mathcal{O}(1)$   | Código limpio (SRP) y paginación eficiente de playlist        |
| Transmisión Overlay de Música | Inactiva hasta abrir la vista                    | Invocación en `__init__` del controlador                                  | Difusión instantánea a `/music` al iniciar la app             |
| Diálogo de Actualizaciones    | ~50 líneas anidadas en MainWindowCore            | Métodos encapsulados en `UpdateController`                                | Reducción de complejidad en la clase principal                |
| Menú Lateral (`Sidebar`)      | Layout rígido con desbordamiento                 | `QScrollArea` transparente integrado                                      | Escala adaptable a cualquier cantidad de módulos              |
| Desplazamiento por Rueda      | Alteraba opciones de ComboBox al pasar el cursor | `FocusPolicy.StrongFocus` en `NoWheelComboBox`                            | Desplazamiento de página sin modificar selecciones            |
| Sistema de Estilos QSS        | Estilos CSS inline dispersos                     | Rol `filter_chip` en `theme.py`                                           | Cero CSS inline en todo el frontend y 100% adherencia al tema |

---
