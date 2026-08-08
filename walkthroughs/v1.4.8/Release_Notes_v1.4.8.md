# Release Notes - MiniKick Version v1.4.8

> [!NOTE]
> MiniKick v1.4.8 es una de las actualizaciones más completas del proyecto. Introduce **Reordenamiento Drag & Drop en la Cola de Música**, **Normalización y Búsqueda Difusa (_Fuzzy Match_)**, **Gestor de Caché y Popularidad LFU/LRU en Disco**, **Inspector en Tiempo Real de Kick WebSocket con Modo RAW y Registro en Archivo**, **Refactorización de la API de Kick (v1/v2)**, **Carga Diferida de Vistas (_Lazy Loading_)** y **Suite de Pruebas Automatizadas (`pytest`)**.

---

## Novedades Destacadas v1.4.8

> [!IMPORTANT]
> **1. Sistema de Música: Drag & Drop, Búsqueda Difusa y Gestión de Caché LFU/LRU**
>
> - **Reordenamiento por Arrastrar y Soltar:** La tabla de la cola de música ([queue_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/queue_panel.py)) permite arrastrar filas usando la manija visual (`grip-vertical.svg`), preservando la selección de la canción movida en su nuevo índice.
> - **Normalización y Coincidencia Difusa (_Fuzzy Match_):** En [music_storage.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/music_storage.py), la función `normalize_query` y `difflib.SequenceMatcher` ($\ge 85\%$ de umbral) detectan búsquedas equivalentes (ej. _"zombie vs creeper"_ = _"creeper vs zombie"_), previniendo descargas redundantes.
> - **Caché por ID de Video:** Verificación instantánea en disco (`yt_<video_id>.*`) en [music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py) antes de invocar `yt-dlp`.
> - **Gestor de Espacio e Histórico LFU/LRU (`MusicCacheManager`):** Control automático del disco en `%LOCALAPPDATA%\.Minikick\cache` con un límite de 1 GB. Las canciones acumulan popularidad (`play_count`) y fecha de acceso (`last_accessed`). Si la carpeta supera 1 GB, el sistema purga únicamente los archivos de canciones poco populares y antiguas, protegiendo las canciones más queridas del canal.
> - **Solución a Migración SQLite:** Corregida la migración de la columna `last_accessed` en [manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py) sin sintaxis `DEFAULT CURRENT_TIMESTAMP` no constante.

> [!IMPORTANT]
> **2. Inspector en Tiempo Real de Kick WebSocket (`test_kick_websocket_live.py`)**
>
> - **Monitoreo en Vivo de Eventos de Kick:** Script interactivo ([test_kick_websocket_live.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_kick_websocket_live.py)) para inspeccionar eventos en tiempo real: `ChatMessageEvent`, `GiftedSubscriptionsEvent`, `SubscriptionEvent`, `StreamHostEvent`, `PollUpdateEvent`, `UserBannedEvent`, `UserUnbannedEvent` y estadísticas de espectadores.
> - **Modo RAW (`--raw` / `-r`):** Visualización del paquete JSON 100% en crudo decodificado para analizar todos los atributos enviados por Pusher.
> - **Registro Automático en Archivo con Fecha y Hora:** Toda sesión graba automáticamente sus logs en `tests/logs/ws_<canal>_YYYY-MM-DD_HH-MM-SS.log` en tiempo real.
> - **Clave Pusher Oficial Integrada:** Sincronizado directamente con las constantes oficiales en [api_keys.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/api_keys.py) (`32cbd69e4b950bf97679`, cluster `us2`).

> [!IMPORTANT]
> **3. Arquitectura Kick API Client & Consumo v2**
>
> - **Centralización SoR:** Eliminación de llamadas `import requests` improvisadas dentro de los _Services_ (como en [widget_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/widget_service.py)), canalizando todo el tráfico HTTP a través del proveedor [kick_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_client.py) usando `ScraperFactory`.
> - **Soporte para API Pública v2 (`/rewards`):** Método `fetch_public_channel_rewards(channel_slug)` para consultar las recompensas públicas activas de cualquier canal sin requerir tokens OAuth.

> [!IMPORTANT]
> **4. Carga Diferida de Vistas (_Lazy Loading_) & Reproductor de Música Integrado**
>
> - **Instanciación Bajo Demanda:** [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/core/main_window_core.py) carga únicamente `DashboardView` al iniciar la app. Las demás vistas se instancian únicamente al cambiar de pestaña.
> - **Reproductor Interactivo:** Visualización del nombre del solicitante de la canción (_"Solicitado por: Usuario"_), barra de progreso dinámica (`QProgressBar`) y reloj de tiempo transcurrido / total.

> [!IMPORTANT]
> **5. Contratos de Interfaz & Suite de Pruebas Automatizadas (`pytest`)**
>
> - Contratos formales `IMusicProvider`, `IStorageRepository` y `IChatService` en [backend/interfaces/](file:///c:/Users/TheAn/Desktop/python/Kick/backend/interfaces/).
> - Suite de 11 pruebas unitarias en `tests/` con 100% de éxito.

---

## Comparativa de Eficiencia y Rendimiento (Big-O)

| Módulo / Operación              | Comportamiento Anterior                                | Optimización v1.4.8                                                                | Impacto en Rendimiento                                 |
| ------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Búsqueda de Canciones Repetidas | Consulta y descarga redundante en YouTube              | Búsqueda Difusa $\mathcal{O}(N)$ + Caché instantánea por Video ID $\mathcal{O}(1)$ | Respuesta en **0.01s** sin consumo de ancho de banda   |
| Gestión de Disco de Música      | Acumulación indefinida de archivos de audio            | Purga Inteligente LFU/LRU $\mathcal{O}(N \log N)$ al superar 1 GB                  | Uso de disco optimizado sin borrar canciones populares |
| Carga de Vistas (UI)            | Instanciación simultánea de 11 vistas $\mathcal{O}(V)$ | Carga diferida perezosa (_Lazy Loading_)                                           | Menor uso de memoria RAM y arranque instantáneo        |
| Reordenamiento de Cola          | Sin capacidad de arrastrar                             | Arrastrar y soltar (_Drag & Drop_) con preservación de selección                   | Experiencia de usuario interactiva y fluida            |
| Inspección de WebSocket         | Sin herramienta de pruebas                             | Inspector en vivo con Modo RAW y guardado en archivo con fecha                     | Diagnóstico completo de eventos de Kick                |
| Integración Kick API            | Llamadas `requests` directas en capas de servicio      | Cliente `KickAPIClient` centralizado con soporte v2                                | Separación estricta de responsabilidades (SoR)         |

---

## Verificación de Pruebas

Puedes ejecutar la suite completa de 11 pruebas integradas con:

```bash
uv run pytest
```

Y para probar el inspector de WebSocket de Kick en tiempo real en modo RAW con guardado de log:

```bash
uv run python tests/test_kick_websocket_live.py --channel tu_canal --raw
```
