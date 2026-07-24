# Walkthrough: MiniKick v1.4.3_02 - Cierre Automático SQLite, Rediseño de Vista de Red, Estabilización de Overlay Server, Ajustes de TTS y Persistencia de Duración de Música

Este documento detalla exhaustivamente todos los cambios, correcciones y optimizaciones aplicados en la segunda fase de estabilización de la versión 1.4.3.

---

## 1. Cambios y Mejoras Realizadas

### A. Cierre Automático de SQLite (Solución a Disk Image Malformed en Caliente)
*   **Problema:** En Windows, cuando la base de datos se corrompía y la aplicación intentaba eliminar el archivo `.db` dañado para reconstruirlo en caliente, se producía un fallo de permisos `PermissionError: [WinError 32]` porque el recolector de basura de Python mantenía bloqueados los handles de la conexión a pesar de haber salido del bloque `with`.
*   **Solución:** Modificamos [manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py) implementando la clase `AutoCloseConnection`, la cual hereda de `sqlite3.Connection` y sobrescribe `__exit__` para garantizar la ejecución explícita de `self.close()` en un bloque `finally`. Configuramos la conexión para inyectar este factory por defecto.

### B. Rediseño de Vista de Red (`NetworkView`) a Formato de Tabla
*   **Problema:** La visualización del estado de los servicios dependía de un flujo de tarjetas individuales que sobrecargaban visualmente la UI y realizaban lecturas recursivas de componentes en PySide por nombre de cadena (`findChild`), comprometiendo el rendimiento y la mantenibilidad.
*   **Solución:** Reemplazamos las tarjetas por el componente `ModernTableCard` en [network_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/network_view.py):
    *   Sustituimos el layout por una cuadrícula tabular con columnas fijas de Estado, Latencia, Servicio y Descripción.
    *   Agregamos soporte multilenguaje completo en [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) para las cabeceras.
    *   Refactorizamos `_create_service_cell` para retornar el contenedor y el componente del icono directamente, eliminando el uso de `findChild`.
    *   Definimos un alto mínimo de `380px` en `table_card` y desactivamos las barras de desplazamiento horizontal/vertical de la tabla para conservar un aspecto limpio y premium.

### C. Prevención de Fugas de Recursos en el Servidor de Overlays (Keep-Alive SSE)
*   **Problema:** Al actualizar fuentes de navegador en OBS Studio o al ocultar y volver a mostrar los overlays, el hilo de la conexión HTTP del backend quedaba bloqueado en la consulta de cola (`client_queue.get()`) de manera indefinida. Esto provocaba fugas masivas de hilos del servidor y descriptores de sockets abiertos, bloqueando eventualmente el puerto `8090` e impidiendo que los overlays respondieran.
*   **Solución:** Modificamos [overlay_server.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/rewards/overlay_server.py):
    *   Introdujimos un tiempo límite de lectura (`timeout=2.0`) en todas las consultas de colas SSE (`/events`, `/chat_events` y `/music_events`).
    *   En caso de agotarse el tiempo de espera, enviamos un comentario de mantenimiento de canal SSE (`: keep-alive\n\n`) y realizamos `flush()`. Esto permite detectar la desconexión del cliente mediante un error de tubería rota (`BrokenPipeError`) y cerrar el hilo del backend inmediatamente.
    *   Protegimos las inserciones y extracciones de la lista compartida de clientes con un cerrojo mutuo `threading.Lock` para evitar errores de concurrencia.

### D. Rediseño del Panel de Ajustes de TTS (Voz del Chat)
*   **Problema:** La configuración del sintetizador de voz estaba dispersa. El motor de voz (Local vs. Web) dependía de un interruptor genérico y se obligaba al usuario a seleccionar una región lingüística de forma previa en un combobox secundario.
*   **Solución:** Refactorizamos [tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py) y [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py):
    *   Reemplazamos el switch del motor por un `NoWheelComboBox` moderno que ofrece explícitamente "Neural IA (Nube Edge)" y "SAPI5 / OS (Local)".
    *   Integramos la selección de motor de voz y la voz de seguidores directamente en la tarjeta de **Voces por Rol** (`voices_card`).
    *   Eliminamos visualmente el combobox regional (`combo_lang`). Ahora el combobox de voz general (`combo_voice`) muestra de forma directa la totalidad de las voces de la nube e instaladas con sus prefijos de región (ej. `[es-ES] AlvaroNeural`).
    *   Ubicamos el control de volumen general en la parte superior junto al resto de interruptores globales de TTS.

### E. Duración y Progreso de Música en Base de Datos y Overlays
*   **Problema:** Al reproducir canciones almacenadas en el reproductor de música o al recargar la cola de reproducción en el arranque de la aplicación, el overlay de música no recibía la duración real de la pista, impidiendo la visualización del progreso del tema.
*   **Solución:** Modificamos e interconectamos múltiples componentes:
    *   **Base de datos:** Añadimos la columna `duration TEXT DEFAULT '-'` a la tabla `music_queue` en [manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py) junto con una migración automática (`ALTER TABLE`). Actualizamos `add_song_to_queue` y `load_pending_songs`.
    *   **YouTube:** En [youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py), configuramos el guardado de la duración en la cola de la BD y la recuperación del valor real al cargar temas pendientes en el arranque.
    *   **Spotify:** En [spotify_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/spotify_client.py), implementamos llamadas adicionales a la API REST de Spotify para resolver los metadatos y duraciones (`duration_ms`) de canciones agregadas mediante URIs directas, y convertimos la duración a formato `m:ss` antes de guardarla.

---

## 2. Archivos Modificados

*   `[MODIFY]` [manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py) (Base de Datos, Migración, Cierre SQLite)
*   `[MODIFY]` [network_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/network_view.py) (Vista de Red, ModernTableCard)
*   `[MODIFY]` [overlay_server.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/rewards/overlay_server.py) (Fuga de Hilos, Lock de Concurrencia, Keep-Alive SSE)
*   `[MODIFY]` [tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py) (Ajustes TTS, Unificación de Voces, Eliminación de Region Combo)
*   `[MODIFY]` [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py) (Vinculación de is_web_provider a Combo)
*   `[MODIFY]` [youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py) (Persistencia de Duración y Carga en Arranque)
*   `[MODIFY]` [spotify_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/spotify_client.py) (Recuperación de Duración de URI y Formateo a Base de Datos)
*   `[MODIFY]` [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) (Localizaciones de Tabla de Red e Idioma General de TTS)
