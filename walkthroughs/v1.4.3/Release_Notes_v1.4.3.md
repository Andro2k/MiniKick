# Release Notes | MiniKick v1.4.3
*Cierre Seguro SQLite en Caliente, Rediseño de Vista de Red a Tabla, Comandos de Control de Música en Chat, Estabilización de Overlays con Keep-Alive y Optimización Masiva de UI*

En esta versión (v1.4.3), MiniKick se consolida como una aplicación extremadamente robusta, eficiente y agradable de usar. Hemos resuelto de forma definitiva el molesto bloqueo de archivos de base de datos corruptos al iniciar en Windows, garantizando una autorecuperación instantánea. La vista de red se renueva con una tabla tabular unificada y de alto rendimiento. Añadimos comandos de chat interactivos (`!pause` y `!resume`) para que tus moderadores tengan el control total del reproductor de música, y aseguramos que el overlay de OBS retenga la duración y el progreso exactos de cada canción (incluyendo consultas automáticas a la API de Spotify). Por último, implementamos políticas Keep-Alive en el servidor de overlays para erradicar las fugas de memoria por recargas en OBS y realizamos una optimización integral de la UI mediante caché de texturas e iconos vectoriales para una fluidez incomparable.

---

## 1. Autorecuperación Segura de Base de Datos (Hot Recovery)
Solucionamos el bloqueo crítico de archivos que impedía restablecer la base de datos dañada en caliente:
* **Conexión Auto-Cerrable**: Implementamos la clase `AutoCloseConnection` en [manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py), la cual hereda de `sqlite3.Connection` y garantiza que el handle de SQLite se cierre explícitamente y se libere en el sistema operativo al salir del bloque context manager.
* **Recuperación sin Errores**: En caso de detectar corrupción física de datos al arrancar, el programa ahora cierra inmediatamente la base de datos, remueve el archivo dañado sin bloqueos de permisos (`PermissionError: [WinError 32]`) y lo vuelve a generar en caliente sin interrumpir la experiencia de transmisión.

> [!IMPORTANT]
> La recuperación y regeneración de la base de datos se realiza automáticamente en caliente de forma silenciosa, eliminando la necesidad de reiniciar la aplicación de forma manual o realizar tareas de mantenimiento externo.

---

## 2. Rediseño Completo de la Vista de Red (`NetworkView`)
Reemplazamos la antigua estructura flotante de tarjetas por una interfaz en formato de tabla limpia y optimizada:
* **Tabla de Estado de Servicios**: Diseñamos el componente tabular `ModernTableCard` en [network_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/network_view.py) para unificar la visualización de los servicios de Kick y del sistema de overlays.
* **Eliminación de Búsquedas de PySide en Caliente**: Modificamos el actualizador de celdas para operar mediante referencias directas a objetos gráficos. Esto descarta por completo las costosas consultas recursivas de cadenas (`findChild`) sobre el árbol de elementos de la interfaz.
* **Diseño Limpio sin Recortes**: Deshabilitamos las barras de desplazamiento (scrollbars) de la tabla y fijamos una altura mínima de `380px`, asegurando que las filas de servicios queden perfectamente encuadradas y visibles en cualquier monitor.
* **Soporte Multilenguaje**: Añadimos las traducciones de cabeceras en español e inglés en [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json).

---

## 3. Nuevos Comandos de Chat para Control de Música
Agregamos la capacidad de pausar o reanudar el reproductor directamente desde el chat de Kick:
* **Comandos `!pause` y `!resume`**: Permiten pausar y reactivar la música en Spotify y YouTube. Cuentan con un nivel de protección por defecto configurado para **moderadores** y un cooldown de 3 segundos para evitar spam visual.
* **Autoseed en Base de Datos**: El controlador crea y registra estos comandos de forma dinámica en la base de datos durante el primer arranque de la v1.4.3.
* **Interruptores de Configuración**: Añadimos controles deslizantes en la pestaña de música del dashboard para encender o apagar estos comandos individualmente, sincronizándose de manera bidireccional con las bases de datos de comandos.

> [!TIP]
> Los comandos de pausar y reanudar música están diseñados con un tiempo de espera (cooldown) y permisos configurables en la sección de Comandos para evitar que los espectadores abusen de ellos en el chat.

---

## 4. Estabilización de Servidores de Overlays en OBS Studio (Keep-Alive)
Erradicamos las fugas de hilos de red y bloqueos del puerto `8090` causados al cambiar escenas o recargar fuentes en OBS:
* **Detección SSE en 2 Segundos**: Introdujimos un timeout en las colas de eventos SSE (`client_queue.get(timeout=2.0)`) en [overlay_server.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/rewards/overlay_server.py).
* **Keep-Alive Activo**: Al superar el tiempo límite, el servidor escribe un comentario SSE (`: keep-alive\n\n`) y ejecuta un `flush()`. Esto comprueba si la conexión sigue abierta. Si el cliente en OBS se desconectó, la escritura eleva una excepción `BrokenPipeError` de inmediato, eliminando el hilo huérfano y liberando los recursos de la máquina del streamer.
* **Operaciones Seguras en Hilos**: Inyectamos sincronización mediante `threading.Lock` para blindar las mutaciones de la lista de suscriptores y prevenir fallos de ejecución concurrente.

> [!WARNING]
> La recarga repetitiva de fuentes de navegador en OBS o el cambio rápido de escenas generaba hilos huérfanos en versiones previas. El nuevo sistema Keep-Alive se encarga de monitorear y purgar estas conexiones inactivas cada 2 segundos.

---

## 5. Duración y Sincronización Predictiva de Música (Spotify y YouTube)
Garantizamos que la barra de progreso y la duración de las canciones persistan y se sincronicen perfectamente en tus overlays:
* **Persistencia en SQLite**: Añadimos la columna `duration TEXT DEFAULT '-'` en la cola de base de datos y programamos la migración silenciosa para bases de datos previas.
* **Resolución Automatizada de Spotify**: Al agregar canciones a través de enlaces directos o URIs de Spotify, el bot consulta asíncronamente los metadatos de la pista en su API REST, recuperando los milisegundos reales (`duration_ms`), traduciéndolos al formato estándar `m:ss` y grabándolos en la base de datos para que el overlay OBS represente el progreso desde el primer segundo.
* **Carga de Pendientes en Arranque**: Corregimos el cargador inicial en [youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py) para que restablezca la duración original del tema almacenado al reanudar la cola de reproducción del directo anterior.

> [!IMPORTANT]
> Si utilizas Spotify, el bot requiere realizar una consulta al endpoint de metadatos de su API REST en segundo plano. Asegúrate de tener tu cuenta vinculada correctamente para que la duración de las canciones se actualice de inmediato en tu overlay.

---

## 6. Unificación y Rediseño Visual de Ajustes TTS
Optimizamos los menús de configuración de la síntesis de voz (Text-To-Speech) en el chat:
* **Selector por Combobox**: Sustituimos el interruptor clásico de motor de voz por un combobox simplificado con opciones transparentes: "Neural IA (Nube Edge)" y "SAPI5 / OS (Local)".
* **Tarjeta Centralizada "Voces por Rol"**: Trasladamos la selección del motor de voz y el selector general de voz de seguidores directamente al módulo unificado de **Voces por Rol** (`voices_card`).
* **Visualización Regional Consistente**: Removimos el combobox secundario de región lingüística. Ahora, el selector de voz de seguidores carga todo el catálogo disponible etiquetado con su país de origen (ej. `[es-ES] AlvaroNeural`), adaptándose al estándar de los selectores de roles y agilizando la configuración.

---

## 7. Optimización Masiva de UI y Caché de Gráficos (Rendimiento)
Realizamos más de una decena de optimizaciones orientadas a eliminar el acceso repetitivo a disco y suavizar las animaciones de la UI:
* **Caché en Sidebar e Iconos de Diálogos**: Las pestañas laterales y los botones de cierre del sistema de diálogos frameless pre-cargan los iconos vectoriales SVG en memoria al instanciarse. Esto previene microcongelaciones al navegar, ya que el sistema no vuelve a leer archivos físicos de iconos de disco.
* **Caché Estática de Pixmaps en Toasts**: El componente `ModernToast` almacena las texturas de iconos pintados en una caché estática. Al lanzar alertas múltiples, el sistema reutiliza los recursos gráficos evitando el re-dibujado de texturas.
* **Recorte de Chat sin Congelamiento**: Implementamos bloques de transacciones de repintado de documentos (`beginEditBlock`/`endEditBlock`) en [chat_display.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/chat_display.py). Esto consolida todas las modificaciones de recorte del chat a un único ciclo de renderizado, manteniendo la UI veloz durante picos de chat intensos.
* **Asignaciones Gráficas Únicas**: Pre-asignamos los colores, pinceles, fuentes y métricas de textos en los constructores de widgets (como `ModernSwitch` y `GraphCanvas`) en lugar de crearlos miles de veces por segundo en el método gráfico `paintEvent`.
* **Inserción de Tags en $O(1)$**: Optimizamos el calculador de tamaño de elementos en las listas de moderación y bots baneados, actualizando solo el elemento insertado en lugar de re-evaluar la colección completa, bajando la complejidad algorítmica de $O(N^2)$ a $O(1)$.
* **Reporte de Errores Asíncrono**: Rediseñamos el diálogo de envío de logs a Discord para operar sobre un hilo de red dedicado (`CrashReportWorker`). Así, la aplicación permanece interactiva y responde en todo momento durante el envío de reportes de fallos.

---

## 8. Solución de Fallos de Streaming y Error HTTP 416 (YouTube)
* **Eliminación de Descargas Parciales Corruptas**: Al intentar reanudar descargas de vídeos con firmas temporales vencidas de YouTube, `yt-dlp` arrojaba fallos HTTP 416. En esta versión deshabilitamos la reanudación asíncrona de archivos parciales (`'continuedl': False`). Si un archivo temporal `.part` está dañado, se elimina de inmediato y el reproductor realiza una redirección automática y fluida a la URL directa de streaming para evitar cortes de audio en tus directos.

> [!CAUTION]
> Si notas microcortes en la reproducción de YouTube debido a bloqueos de Google Video, el sistema se encargará de purgar los fragmentos parciales huérfanos y reconectar la transmisión automáticamente en segundo plano de forma transparente.
