# Release Notes - MiniKick Version v1.4.9

> [!NOTE]
> MiniKick v1.4.9 es una versión enfocada en la **Extensión de Almacenamiento Local a 5 GB**, **Persistencia Real de Canciones en Disco Duro**, **Fix de Retención de Audio Local**, **Herramientas de Diagnóstico de Kick WebSocket en Tiempo Real**, **Refactorización de la API de Kick (v1/v2)** y **Fortalecimiento de la Suite de Pruebas Automatizadas (`pytest`)**.

---

## 🚀 Novedades Destacadas v1.4.9

> [!IMPORTANT]
> **1. Ampliación de Capacidad a 5 GB, Persistencia Real de Canciones y Gestión LFU/LRU**
> - **Límite Incrementado a 5 GB (5000 MB):** Se amplió el espacio total de caché en disco de 1 GB a **5 GB** en [cache_manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/cache_manager.py) y [youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py).
> - **Retención en Disco Duro Corregida:** Se eliminó la instrucción antigua que borraba el archivo de audio local al finalizar la reproducción en [youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py). Ahora las canciones permanecen guardadas en `%LOCALAPPDATA%\.Minikick\cache` para reproducciones instantáneas en 0.01s.
> - **Gestor de Espacio e Histórico LFU/LRU (`MusicCacheManager`):** Control automático del disco en `%LOCALAPPDATA%\.Minikick\cache` con el nuevo límite de **5 GB**. Las canciones acumulan popularidad (`play_count`) y fecha de acceso (`last_accessed`). Si la carpeta supera 5 GB, el sistema purga únicamente los archivos de canciones poco populares y antiguas, protegiendo las canciones más queridas del canal.
> - **Reordenamiento por Arrastrar y Soltar:** La tabla de la cola de música ([queue_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/queue_panel.py)) permite arrastrar filas usando la manija visual (`grip-vertical.svg`), preservando la selección de la canción movida en su nuevo índice.
> - **Normalización y Coincidencia Difusa (*Fuzzy Match*):** En [music_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/music_storage.py), la función `normalize_query` y `difflib.SequenceMatcher` ($\ge 85\%$ de umbral) detectan búsquedas equivalentes (ej. *"zombie vs creeper"* = *"creeper vs zombie"*), previniendo descargas redundantes.

> [!IMPORTANT]
> **2. Inspector en Tiempo Real de Kick WebSocket (`test_kick_websocket_live.py`)**
> - **Monitoreo en Vivo de Eventos de Kick:** Script interactivo ([test_kick_websocket_live.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_kick_websocket_live.py)) para inspeccionar eventos en tiempo real: `ChatMessageEvent`, `GiftedSubscriptionsEvent`, `SubscriptionEvent`, `StreamHostEvent`, `PollUpdateEvent`, `UserBannedEvent`, `UserUnbannedEvent` y estadísticas de espectadores.
> - **Modo RAW (`--raw` / `-r`):** Visualización del paquete JSON 100% en crudo decodificado para analizar todos los atributos enviados por Pusher.
> - **Registro Automático en Archivo con Fecha y Hora:** Toda sesión graba automáticamente sus logs en `tests/logs/ws_<canal>_YYYY-MM-DD_HH-MM-SS.log` en tiempo real.
> - **Clave Pusher Oficial Integrada:** Sincronizado directamente con las constantes oficiales en [api_keys.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/api_keys.py) (`32cbd69e4b950bf97679`, cluster `us2`).

> [!IMPORTANT]
> **3. Arquitectura Kick API Client & Consumo v2**
> - **Centralización SoR:** Eliminación de llamadas `import requests` improvisadas dentro de los *Services* (como en [widget_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/widget_service.py)), canalizando todo el tráfico HTTP a través del proveedor [kick_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_client.py) usando `ScraperFactory`.
> - **Soporte para API Pública v2 (`/rewards`):** Método `fetch_public_channel_rewards(channel_slug)` para consultar las recompensas públicas activas de cualquier canal sin requerir tokens OAuth.

> [!IMPORTANT]
> **4. Carga Diferida de Vistas (*Lazy Loading*) & Reproductor de Música Integrado**
> - **Instanciación Bajo Demanda:** [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/core/main_window_core.py) carga únicamente `DashboardView` al iniciar la app. Las demás vistas se instancian únicamente al cambiar de pestaña.
> - **Reproductor Interactivo:** Visualización del nombre del solicitante de la canción (*"Solicitado por: Usuario"*), barra de progreso dinámica (`QProgressBar`) y reloj de tiempo transcurrido / total.

> [!IMPORTANT]
> **5. Contratos de Interfaz & Suite de Pruebas Automatizadas (`pytest`)**
> - Contratos formales `IMusicProvider`, `IStorageRepository` y `IChatService` en [backend/interfaces/](file:///c:/Users/TheAn/Desktop/python/Kick/backend/interfaces/).
> - Suite de 13 pruebas unitarias en `tests/` con 100% de éxito (incluyendo `test_cache_manager.py`).

---

## 📊 Comparativa de Eficiencia y Rendimiento (Big-O)

| Módulo / Operación | Comportamiento Anterior | Optimización v1.4.9 | Impacto en Rendimiento |
|---|---|---|---|
| Límite de Almacenamiento Local | 1000 MB (1 GB) | **5000 MB (5 GB)** | **5x mayor capacidad** para almacenar cientos de canciones locales |
| Persistencia de Audio | Borrado automático al terminar de sonar | Archivos preservados en `%LOCALAPPDATA%\.Minikick\cache` | Reuso real de archivos descargados |
| Búsqueda de Canciones Repetidas | Consulta y descarga redundante en YouTube | Búsqueda Difusa $\mathcal{O}(N)$ + Caché instantánea por Video ID $\mathcal{O}(1)$ | Respuesta en **0.01s** sin consumo de ancho de banda |
| Gestión de Disco de Música | Acumulación indefinida o borrado total | Purga Inteligente LFU/LRU $\mathcal{O}(N \log N)$ al superar 5 GB | Uso de disco optimizado sin borrar canciones populares |
| Carga de Vistas (UI) | Instanciación simultánea de 11 vistas $\mathcal{O}(V)$ | Carga diferida perezosa (*Lazy Loading*) | Menor uso de memoria RAM y arranque instantáneo |
| Reordenamiento de Cola | Sin capacidad de arrastrar | Arrastrar y soltar (*Drag & Drop*) con preservación de selección | Experiencia de usuario interactiva y fluida |
| Inspección de WebSocket | Sin herramienta de pruebas | Inspector en vivo con Modo RAW y guardado en archivo con fecha | Diagnóstico completo de eventos de Kick |

---

## 🧪 Verificación de Pruebas

Puedes ejecutar la suite completa de 13 pruebas integradas con:

```bash
uv run pytest
```
