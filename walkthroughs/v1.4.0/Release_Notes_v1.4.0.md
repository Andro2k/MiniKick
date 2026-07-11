# Release Notes | MiniKick v1.4.0
*Sistema de Overlays para OBS, Reporte Global de Fallos, Optimización en Tiempo de Inicio, Gráfica Proporcional de Sesión, Reorganización de Reproductores y Persistencia de Ajustes en Base de Datos*

En esta versión (v1.4.0), MiniKick da el salto definitivo para convertirse en el centro de control integral de transmisiones de Kick.com. Hemos desarrollado un sistema de lienzo modular y overlays de chat para codificadores como OBS, rediseñado el panel musical con un reproductor asimétrico moderno, integrado una barra de distribución de métricas para estadísticas en tiempo real y establecido un sistema de captura y reporte de fallos críticos. Asimismo, logramos una reducción drástica en la latencia de arranque gracias al cargado diferido (lazy loading) de componentes, la persistencia de perfiles y la optimización de los servicios de música e interceptores de chat.

---

## 1. Sistema de Overlay de Chat para OBS (Temas y Personalización)
Diseñamos un lienzo modular que corre en un servidor local para proyectar el chat en OBS Studio o cualquier software compatible con fuentes de navegador:
* **Carga de Estilos sin Token (Bypass)**: Corregimos un bloqueo de seguridad en `overlay_server.py` que retornaba un error 403 Forbidden para activos estáticos. Ahora las hojas de estilo externas se cargan libremente sin comprometer el token de sesión dinámico.
* **Escalamiento Proporcional Progresivo**: Migramos los tamaños fijos de tipografías a variables CSS personalizadas (`--font-size`). Al ajustar el tamaño desde la interfaz (10px a 32px), todo el texto (marcas de tiempo, nombres y mensajes) escala de forma proporcional.
* **Temas Visuales Modulares**:
  * **Glassmorphism (`glass.css`)**: Efecto de vidrio esmerilado translúcido con desenfoque de fondo.
  * **Neon Aura (`neon.css`)**: Cajas flotantes oscuras donde los bordes y las luces de brillo interno y externo adoptan el color exacto del usuario de Kick en tiempo real.
  * **Comic Speech Bubble (`card.css`)**: Estructura de bocadillo clásico con bordes negros gruesos, sombra pop-art y una cola de diálogo que apunta hacia el avatar del chat.
  * **Stream Widget (`minimal.css`)**: Texto suspendido de alta legibilidad con una línea punteada lateral izquierda que cambia de color de acuerdo con el usuario.
* **Soporte Completo de Emotes**: Añadimos un analizador asíncrono para decodificar tags de emotes personalizados de Kick y 7TV (como `[emote:ID:NOMBRE]`), escapando previamente las entradas para neutralizar inyecciones de código HTML (XSS).
* **Parámetros del Enlace OBS**: El portapapeles codifica automáticamente las variables del tema, velocidad de atenuación (auto-fade), timestamps y supresión de bots en la URL del overlay.

> [!NOTE]
> Para probar los temas y configuraciones del overlay, puedes abrir directamente el enlace generado en cualquier navegador de tu ordenador, aunque está diseñado para integrarse como Fuente de Navegador (Browser Source) dentro de OBS.

---

## 2. Pestaña de Lienzo (Overlay) y Persistencia de Preferencias
* **Estructura de Tres Pestañas en Chat**: Rediseñamos el panel de control del chat usando un componente `QTabWidget` con pestañas dedicadas para:
  1. **Ajustes de Voz**: Configuración general del sintetizador.
  2. **Silenciados**: Bloqueo y desbloqueo de usuarios problemáticos.
  3. **Lienzo (Overlay)**: Administración visual de los parámetros de transmisión en tiempo real.
* **Persistencia en SQLite y Respaldos**: Guardamos todas las preferencias del overlay (`chat_overlay_theme`, `chat_overlay_size`, `chat_overlay_fade`, `chat_overlay_show_bots` y `chat_overlay_show_time`) en el almacenamiento local. Esto asegura que al cerrar la aplicación o exportar/importar configuraciones con `BackupService` los ajustes permanezcan inalterados.

---

## 3. Captura Global de Excepciones y Diálogo de Crashes
* **Interceptor a Nivel de VM**: Registramos un hook de sistema en `sys.excepthook` en el bootstrap de `main.py`. Si ocurre un fallo crítico imprevisto en cualquier hilo de la app, el error es capturado antes de que la aplicación se apague silenciosamente.
* **Diálogo de Reporte (`CrashReportDialog`)**: Si ocurre un crash, se inicializa un entorno ligero en el idioma del usuario que muestra un modal de peligro (`danger`) con el traceback del error. El usuario puede ingresar detalles adicionales y, con un solo clic, enviar el informe junto con los registros locales de MiniKick a un webhook seguro en Discord.

> [!IMPORTANT]
> El webhook para el envío de reportes de fallos viene preconfigurado en el código de producción hacia el canal de soporte oficial. Asegúrate de tener una conexión de red activa al presionar el botón de enviar reporte.

---

## 4. Reestructuración y Sincronización del Reproductor de Música
* **Layout Asimétrico en Dos Columnas**:
  * **Columna Izquierda**: Concentra los controles de selección de proveedor, autenticación de cuenta, comandos autorizados y la cola de reproducción en cascada.
  * **Columna Derecha (300px)**: Contiene la tarjeta del reproductor musical cuadrado con portada redondeada de `268x268px`, barra de reproducción delgada (4px), marcas de tiempo exactas (tiempo actual y tiempo total) y controles de navegación circulares.
* **Degradados Dinámicos**: La carátula por defecto renderiza un fondo degradado basado en el servicio de música que se encuentre activo (verde para Spotify, rojo para YouTube).
* **Sincronización en Tiempo Real**: Optimizamos los clientes de API de Spotify y YouTube para reportar el progreso de la pista en milisegundos (`progress_ms`), permitiendo que el deslizador se desplace suavemente segundo a segundo.

---

## 5. Carga Perezosa (Lazy Loading) y Mejoras de Rendimiento
* **Lazy Loading en Controladores**: Modificamos los controladores principales para posponer la importación de librerías de gran tamaño (hilos de red, asistentes de configuración de diálogos y reproductores multimedia) hasta el momento preciso de su uso. Esto reduce el consumo de memoria en el inicio de la app y acelera el tiempo de arranque.
* **Optimización de YouTube resolving**: Consolidamos las llamadas del resolvedor de enlaces de YouTube en `music_worker.py`. Redujimos a la mitad las llamadas síncronas de red de `yt-dlp` al consolidar la información de metadatos y streaming en una única transacción de red.

---

## 6. Historial de Sala y Sincronización de Comandos TTS
* **Historial de Comandos**: Modificamos el pipeline de procesamiento de mensajes. Los comandos como `!sr` o `!skip` ya no detienen de forma abrupta el flujo del pipeline (`dto.is_cancelled = True`), sino que se marcan como comandos (`dto.is_command = True`). Esto permite que aparezcan en el historial de chat de la ventana principal para dar contexto al streamer, mientras que el sintetizador de voz (TTS) los ignora automáticamente.
* **Vinculación de Comando TTS**: El comando de activación del sintetizador por chat (`!tts` o personalizado) se vincula bidireccionalmente con la base de datos de comandos. Modificar el disparador desde Ajustes de Voz actualiza automáticamente el registro en la pestaña de Comandos, y viceversa.
* **Validación en Tiempo Real**: Se agregó validación visual instantánea en las entradas de texto para prefijos. Los campos que no comiencen con `!` se resaltarán con un borde rojo y los botones de confirmación en los asistentes de creación de comandos y recompensas permanecerán inhabilitados hasta que el formato sea válido.

---

## 7. Gráfica Proporcional en el Dashboard
* **Widget `SegmentedDistributionBar`**: Desarrollamos una barra de distribución de métricas segmentada y redondeada con `QPainter` en la zona de estadísticas.
* **Porcentajes de Participación**: La barra calcula y dibuja la proporción correspondiente a cada tipo de interacción (Mensajes, Comandos de Chat, Timers, Filtros de Spam). Las tarjetas de métricas del grid inferior ahora muestran la cantidad absoluta junto al porcentaje exacto de participación de la sesión.

---

## 8. Mejoras de Usabilidad y Refactorizaciones Internas
* **Botón de Salida Rápida**: Añadimos un botón de cierre superior derecho (`btn_close_shell`) en la estructura base de los modales (`ModernFramelessShell`) para facilitar la salida del usuario.
* **Filtro de Bots en Overlay**: Añadimos soporte para detectar automáticamente a bots conocidos en el canal (o usuarios con sufijo `bot`), inyectándoles la insignia de bot (`.badge-bot`) en el overlay y permitiendo filtrarlos en tiempo real si el usuario decide ocultar las cuentas automáticas.
* **Decoupling de Chat y Música**: Eliminamos la dependencia directa de `ChatController` sobre la interfaz gráfica del reproductor de música, reemplazándola por el envío asíncrono de la señal `music_plugin_triggered`, la cual es atendida directamente por el controlador de música correspondiente.

> [!TIP]
> Recuerda que puedes configurar combinaciones de teclas globales en tu panel de control o utilizar atajos del sistema para interactuar de forma rápida con el reproductor asimétrico sin tener que cambiar de pantalla durante el directo.
