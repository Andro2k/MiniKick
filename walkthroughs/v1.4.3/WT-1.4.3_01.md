# Walkthrough: MiniKick v1.4.3_01 - Estabilización de YouTube, Comandos y Optimización de Música, Red, Dashboard, Widgets, Navegación, Chat y Diálogos

Este documento describe detalladamente los cambios y las mejoras realizadas en la versión 1.4.3.

---

## 1. Cambios y Mejoras Realizadas

### A. Estabilización de Streaming en YouTube
*   **Problema:** Al reproducir música de YouTube, los usuarios experimentaban caídas de conexión y bloqueos de red (`HTTPSConnectionPool` o `Read timed out` en servidores `googlevideo.com`).
*   **Solución:** Modificamos [music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py) para inyectar políticas de reintento automático y límites de tiempo en `yt-dlp` a través de los workers [YouTubeResolveWorker](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py#L31) y [YouTubeSearchWorker](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py#L82):
    *   `socket_timeout: 15`: Evita que las conexiones bloqueadas se queden colgadas de forma indefinida.
    *   `retries: 5` y `fragment_retries: 5`: Fuerza reintentos automáticos en caso de microcortes o caídas de velocidad, lo cual suele reasignar un servidor de streaming estable de YouTube.

### B. Nuevos Comandos de Chat: `!pause` y `!resume` (o `!play`)
*   **Funcionalidad:** Permite controlar el reproductor activo (tanto Spotify como YouTube) enviando mensajes de control directo desde el chat de Kick.
*   **Seguridad:**
    *   Los comandos se configuran por defecto con **permiso exclusivo de moderador** (`permission="moderator"`) y cooldown de 3 segundos para evitar abusos por parte de los espectadores.
    *   Se agregan alias opcionales (como `!play` para reanudar).
*   **Registro Dinámico (Seeding):**
    *   En [music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py#L52), se implementó un autoseed para que la aplicación cree de forma transparente estas configuraciones en la tabla `chat_commands` en el primer inicio.
*   **Traducciones:**
    *   Añadidos mensajes locales de confirmación de éxito y error en inglés y español en [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) y [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json).

### C. Integración de Interruptores en la Interfaz (UI Switches)
*   **Vistas:** Agregamos interruptores visuales de alternancia en [music_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/music_view.py#L192) (`sw_pause` y `sw_resume`) bajo la sección de "Comandos de Espectadores".
*   **Control de Estado:** El controlador de música sincroniza automáticamente el estado encendido/apagado de los interruptores en la pantalla con el estado activo de los comandos en la base de datos de SQLite.

### D. Refactorización y Optimización de la Vista de Música
*   **Código Limpio en el Frontend:** Refactorizamos completamente [music_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/music_view.py) aplicando los pilares de SOLID y buenas prácticas de optimización de PySide:
    *   **DRY en Tablas:** Se creó un método de utilidad privado `_create_table_item` para simplificar la inserción de datos en la tabla de la cola de música.
    *   **Gestión de Rendimiento en Redimensión:** En el método `resizeEvent`, añadimos una variable de caché (`self._last_direction`) para evitar que el layout calcule orientaciones nuevas en cada píxel de arrastre de ventana. Ahora solo se calcula el cambio cuando se cruza el umbral de ancho de 900px.
    *   **Desacoplamiento de Celdas:** Modificamos la creación de botones de borrado (`_create_delete_button`) para aislar la memoria de layouts de widgets anidados durante las actualizaciones de cola, evitando sobrecargas de rendimiento.

### E. Refactorización y Optimización de la Vista de Red (`NetworkView`)
*   **Optimización de Renderizado en `GraphCanvas`:**
    *   **Evitar Asignaciones en Caliente en `paintEvent`:** En [network_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/network_view.py), pre-instanciamos las fuentes de letra (`self._font_small`, `self._font_bold`) y las métricas de fuentes (`self._metrics_small`) en el constructor `__init__`. Anteriormente, instanciar estos objetos gráficos en cada refresco de dibujo (dentro de `paintEvent` y el tooltip de trazado de ping) causaba consumos de CPU innecesarios y ralentizaciones del bucle de eventos de Qt a 60 FPS.
    *   **Control Inteligente de Eventos de Ratón:** Optimizamos `mouseMoveEvent` agregando una comprobación condicional para que la ventana solo llame a `self.update()` cuando el cursor realmente cruza de un nodo de datos de ping a otro, previniendo refrescos gráficos redundantes.
    *   **DRY en Configuración de Tarjetas:** Refactorizamos la inserción estática de las tarjetas de estado de red (`_add_card`) usando un bucle iterativo sobre un arreglo de datos declarativo (`card_configs`), simplificando el mantenimiento de tarjetas añadidas en el futuro.
    *   **Sincronización de Estados de Red (`set_status`):** Rediseñamos el método de asignación de latencia para unificar las claves de estado de manera limpia y prevenir errores de asignación vacía en estados intermedios.

### F. Refactorización y Optimización de la Vista del Panel (`DashboardView`)
*   **Gestión de Rendimiento en Redimensión:**
    *   **Caché de Direcciones en `resizeEvent`:** Modificamos `resizeEvent` en [dashboard_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py) para almacenar el estado de la dirección del banner (`_last_banner_dir`) y el de la fila superior (`_last_top_row_dir`). Con esto, el layout de la pantalla de bienvenida no recalcula constantemente sus restricciones ni causa invalidaciones de tamaño recursivas en Qt durante los redimensionados progresivos.
*   **Optimización de Trazado de Gráfico de Sesión:**
    *   **Caché del Clipping de Pintor (`SegmentedDistributionBar`):** Evitamos instanciar un objeto `QPainterPath` para el clip redondeado en cada llamada a `paintEvent`. Ahora la máscara de clipping se almacena en memoria y solo se reconstruye si el tamaño físico de la barra de distribución cambia.

### G. Optimización de Widgets Comunes Reutilizables (`frontend/widgets/`)
*   **Eliminación de Lecturas de Disco en Caliente (`blocks.py`):**
    *   En [blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py), modificamos la tarjeta de opciones expandible `ExpandableSettingCard`. Anteriormente, al hacer clic para expandir o contraer la tarjeta (`toggle_expand`), se invocaba `get_icon_colored` para `chevron-up.svg` y `chevron-down.svg`, forzando la lectura física y parseo del SVG desde el disco en el hilo principal de renderizado de la UI. Ahora, ambos iconos se pre-cargan en el constructor (`self._icon_up` y `self._icon_down`) y simplemente se alternan en memoria.
*   **Optimización de Asignación en Dibujo (`controls.py`):**
    *   En [controls.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls.py), optimizamos la clase `ModernSwitch`. Los objetos `QColor` (como el color verde de fondo y los colores de bordes e interruptores) ahora se inicializan una única vez en el constructor `__init__`, evitando instanciaciones de color redundantes dentro del método de pintado continuo `paintEvent`.
*   **Corrección de Importaciones en Caliente (`controls.py` y `scalable_illustration.py`):**
    *   Movimos todas las sentencias `import re` del cuerpo de métodos iterativos (`highlightBlock` en el resaltador de variables, manejadores de eventos de borrado y lectura de aspect ratio SVG en `scalable_illustration.py`) al nivel superior del módulo. Esto evita sobrecargar el cargador de módulos de Python en acciones ejecutadas a ritmo de pulsación de teclado del usuario.

### H. Optimización de Componentes de Navegación (`frontend/navigation/`)
*   **Caché de Iconos de Pestañas del Sidebar (`sidebar_component.py`):**
    *   En [sidebar_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py), modificamos `add_tab` para pre-cargar y almacenar las dos instancias de `QIcon` (el verde para estado activo y el gris para estado inactivo) como propiedades asociadas del botón (`icon_active` e `icon_inactive`). Anteriormente, al hacer clic en cualquier pestaña, el método de actualización recorría todos los botones y releía y coloreaba los archivos SVG del disco en el hilo principal. Ahora, el cambio de pestaña es inmediato ya que sólo intercambia las referencias en memoria.
    *   **Chevron Toggles:** Pre-cargamos los iconos `chevron-left-pipe.svg` y `chevron-right-pipe.svg` en `__init__` para evitar lecturas de disco al colapsar o expandir el menú lateral.
*   **Caché de Notificaciones de Alertas (`toast_component.py`):**
    *   En [toast_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py), agregamos una caché estática a nivel de clase (`_pixmap_cache`) dentro de `ModernToast`. Cuando se muestra una alerta (`success`, `danger`, `warning`, `info`), se renderiza e introduce su icono de estado y el icono de cierre (`x.svg`) en la caché. Siguientes alertas con el mismo estado se muestran instantáneamente reutilizando la textura gráfica en memoria sin realizar lecturas físicas a disco.

### I. Optimización de Componentes de Chat (`frontend/components/chat/`)
*   **Mejora de la Complejidad al Añadir Tags (`bot_mute.py`):**
    *   En [bot_mute.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py), extrajimos la lógica de tamaño e iconos de un elemento de etiqueta individual a un método privado `_configure_tag_item`. Anteriormente, al añadir una palabra baneada o un bot, la aplicación ejecutaba `recalculate_item_sizes()` sobre todos los elementos existentes en la lista, lo que causaba un coste cuadrático $O(N^2)$ al poblar listas de configuración inicial. Ahora, al añadir una nueva etiqueta, sólo se inicializa ese elemento específico en $O(1)$.
    *   **Caché de Iconos de Borrado:** Implementamos una caché en memoria para los iconos de borrado (`trash.svg`) organizados por tamaño del texto (`icon_size`), reduciendo el acceso a disco en la actualización visual de las listas.
*   **Recorte Eficiente del Visor de Chat (`chat_display.py`):**
    *   En [chat_display.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/chat_display.py), implementamos transacciones de edición alrededor del bucle de recorte de mensajes excedentes en el visor de chat (`_trim_chat_history`) utilizando `beginEditBlock()` y `endEditBlock()`. Esto reduce los costosos recálculos de repintado del documento de texto formateado en Qt a un solo ciclo, previniendo latencias o microcongelaciones al recibir chats a alta velocidad.

### J. Optimización y Desbloqueo de Diálogos (`frontend/dialogs/`)
*   **Reportes de Fallo en Segundo Plano (Asíncronos):**
    *   **Worker Dedicado (`CrashReportWorker`):** Creamos [crash_report_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/crash_report_worker.py) heredando de `QThread`. Este worker procesa la lectura de logs locales y realiza la petición HTTP `requests.post` a Discord en segundo plano.
    *   **Interfaz Responsiva:** Modificamos [crash_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/crash_report_dialog.py) para usar este worker. Al enviar el reporte de error, los botones se bloquean y se muestra el estado "Enviando...", pero el diálogo no congela la aplicación (el usuario puede mover la ventana libremente y el proceso no entra en estado "No Responde").
*   **Caché de Iconos de Diálogos:**
    *   **Caché Estática de Cierre (`base_dialog.py`):** Añadimos un campo de clase estático `_icon_close` en `ModernFramelessShell`. Todos los diálogos que heredan de este componente (los 10 diálogos personalizados) ahora comparten en memoria el icono `x.svg`, eliminando la lectura del SVG de disco en cada apertura de ventana.
    *   **Caché en Carga de Recompensas (`rewards_dialog.py`):** Pre-cargamos los iconos de actualización (`refresh.svg`) y mapa/pin (`map-pin.svg`) en el constructor de `RewardsConfigWizard`.
    *   **Caché en Edición de Mensajes de Temporizadores (`timer_dialog.py`):** Pre-cargamos los iconos de edición (`edit.svg`) y borrado (`trash.svg`) en `TimerConfigWizard.__init__`. Al cargar o configurar múltiples respuestas de temporizadores seguidas, la interfaz reutiliza las referencias en memoria en lugar de leer el disco por cada fila creada.

---

## 2. Archivos Modificados

*   `[NEW]` [crash_report_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/crash_report_worker.py)
*   `[MODIFY]` [__init__.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/__init__.py)
*   `[MODIFY]` [crash_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/crash_report_dialog.py)
*   `[MODIFY]` [base_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py)
*   `[MODIFY]` [rewards_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/rewards_dialog.py)
*   `[MODIFY]` [timer_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/timer_dialog.py)
*   `[MODIFY]` [music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py)
*   `[MODIFY]` [music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py)
*   `[MODIFY]` [music_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/music_view.py)
*   `[MODIFY]` [network_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/network_view.py)
*   `[MODIFY]` [dashboard_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py)
*   `[MODIFY]` [controls.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls.py)
*   `[MODIFY]` [blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)
*   `[MODIFY]` [scalable_illustration.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/scalable_illustration.py)
*   `[MODIFY]` [sidebar_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py)
*   `[MODIFY]` [toast_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py)
*   `[MODIFY]` [bot_mute.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py)
*   `[MODIFY]` [chat_display.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/chat_display.py)
*   `[MODIFY]` [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
*   `[MODIFY]` [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)

---

## 3. Plan de Pruebas Manuales

Para validar esta versión, sigue los siguientes pasos:

1.  **Iniciar la aplicación:**
    *   Ejecuta `uv run main.py`.
2.  **Verificar Interfaz de Música:**
    *   Entra a la pestaña de **Música**.
    *   Verifica que aparezcan los interruptores para activar/desactivar los comandos de **Pausar Música** y **Reanudar Música**.
    *   Activa o desactiva uno de ellos y confirma en la pestaña de **Comandos** que el bot refleja el cambio de estado de activación.
3.  **Probar en Chat de Kick:**
    *   Conecta un reproductor y pon música a sonar.
    *   Como emisor o moderador, escribe `!pause` en el chat. Verifica que el reproductor se pause y el bot escriba en el chat `⏸️ Música pausada con éxito.`
    *   Escribe `!resume` o `!play`. Verifica que la música continúe reproduciéndose y el bot responda `▶️ Música reanudada con éxito.`
4.  **Verificar la pestaña de Red:**
    *   Entra a la pestaña de **Red**.
    *   Comprueba que los gráficos en tiempo real fluyan sin problemas.
    *   Desplaza el cursor sobre el gráfico cartesiano y verifica que los tooltips emergentes de ping se muestren instantáneamente, con transiciones fluidas y sin parpadeos de la interfaz de usuario.
5.  **Verificar la pestaña de Panel (Dashboard):**
    *   Entra a la pestaña de **Panel**.
    *   Verifica que la transición entre el estado desconectado y conectado sea fluida.
    *   Comprueba que los gráficos de distribución de la barra de sesión se updateen de manera limpia cuando se procesen mensajes y comandos de chat simulados.
6.  **Verificar Fluidez en Expandir Tarjetas y Escribir Mensajes:**
    *   Prueba hacer clic en las tarjetas de moderación de chat para expandirlas; deben abrirse y cerrarse con total respuesta y sin retrasos de carga de disco.
    *   Escribe en los campos de edición con autocompletado y confirma que el resaltado de variables funcione sin latencias al teclear rápido.
7.  **Verificar Rapidez al Cambiar de Pestañas y Ver Notificaciones:**
    *   Haz clic consecutivamente en varias pestañas del menú lateral; el cambio debe ser completamente inmediato e instantáneo.
    *   Desencadena alertas o tocas botones de guardado para disparar notificaciones de toast; confirma que los iconos se dibujen de manera inmediata.
8.  **Verificar Adición de Tags e Historial de Chat:**
    *   Añade varios bots y palabras prohibidas de forma consecutiva y comprueba que se agreguen instantáneamente sin congelaciones.
    *   Al recibir mensajes continuos de chat, verifica que el visor maneje el límite de mensajes sin latencias.
9.  **Verificar Asincronía en Reporte de Fallos:**
    *   Dispara el diálogo de reporte de fallo (por ejemplo, forzando un error en el flujo de desarrollo) y presiona **Enviar Reporte**.
    *   Comprueba que el diálogo muestre "Enviando..." y los botones se inhabiliten, pero la ventana se pueda mover libremente y no bloquee el hilo visual de PySide.
