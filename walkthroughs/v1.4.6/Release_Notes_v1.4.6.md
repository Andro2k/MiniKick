# Release Notes | MiniKick v1.4.6

_Soporte masivo de Overlays en OBS, Visibilidad en Tiempo Real, Interfaz Ultra Fluida a 60 FPS, Comando !systts y Mayor Estabilidad_

¡Bienvenidos a la versión **v1.4.6** de MiniKick!
Esta actualización trae mejoras masivas en el rendimiento de los overlays de OBS, eliminación de lag en la aplicación, nuevas herramientas de moderación para el chat y corrección de errores para que tu transmisión sea más fluida y estable que nunca.

---

## Múltiples Overlays Simultáneos en OBS (WebSockets)

> [!IMPORTANT]
> **Ahora puedes agregar todos los overlays que quieras en OBS sin que se congelen.**

- **Tecnología WebSocket de Alta Velocidad**: Migramos las conexiones de los overlays a WebSockets. Ahora puedes tener el chat, la música, las recompensas, el contador de muertes y el marcador de partidas en la misma escena de OBS sin límite de conexiones.
- **Reconexión Automática**: Si reinicias la aplicación o se interrumpe la conexión por un segundo, los overlays en OBS se reconectarán automáticamente en segundo plano sin que tengas que refrescar las fuentes manualmente.

---

## Visibilidad Dinámica de Widgets (Muertes y Score)

> [!TIP]
> **Los widgets se ocultan o muestran en OBS al instante según los enciendas o apagues.**

- **Sincronización en Tiempo Real**: Al activar o desactivar los interruptores de _Contador de Muertes_ o _Récord V/D_ en la aplicación, el widget en OBS se mostrará u ocultará de inmediato sin dejar recuadros en blanco.
- **Estado Guardado**: Al abrir OBS, los widgets recordarán exactamente si estaban activos o inactivos.

---

## Interfaz Ultra Fluida y Chat Overlay a 60 FPS

> [!NOTE]
> **Respuesta instantánea de los controles y animaciones ultra suaves.**

- **Cero Lag al Hacer Clics**: Al modificar contadores, guardar comandos o encender opciones en la app, la respuesta de la pantalla es inmediata ($0\text{ ms}$) y sin pausas.
- **Overlays de Chat a 60 FPS**: Se optimizaron todos los temas visuales del chat (`Neon`, `Glass`, `Minimal`, `Cyber`, `Card`) usando aceleración por tarjeta gráfica (GPU) para que los mensajes fluyan de forma limpia y transparente.
- **Escalado Proporcional de Texto**: Al cambiar el tamaño de letra del chat desde la aplicación, todo el diseño (iconos, márgenes, bordes y sombras) se adapta automáticamente.
- **Vista de Temporizadores**: Al pasar el mouse sobre un temporizador, se muestra un cuadro flotante con la lista completa de mensajes configurados.

---

## Nuevo Comando `!systts` para Moderadores

- **Control del Bot de Voz desde el Chat**: Los moderadores y el streamer ahora pueden activar o desactivar la lectura de voz del chat usando el comando `!systts` directamente desde Kick:
  - `!systts on`: Activa la lectura de voz.
  - `!systts off`: Pausa la lectura de voz.
  - `!systts status`: Muestra si la voz está encendida o apagada.
- **Comandos Regex y Voz**: Los comandos automáticos por palabras clave (ej: `!hola`) responderán en el chat y al mismo tiempo permitirán que la voz lea el mensaje del usuario.

---

## Mejoras en la Lista de Música (`!playlist` / `!queue`)

- **Paginación Inteligente**: Si un usuario solicita muchas canciones en la cola de música, el bot responderá con mensajes paginados (`pt. 1/2`, `pt. 2/2`) para evitar sobrepasar el límite de caracteres de Kick y garantizar que siempre se vean todas las posiciones.

---

## Corrección de Errores y Mayor Estabilidad

> [!WARNING]
> **Protección contra caídas de la aplicación y descargas de música.**

- **Protección Anti-Crash**: Se implementó una pantalla de reporte de errores para evitar que la aplicación se cierre sin aviso en caso de fallos inesperados.
- **Descarga de Canciones Estable**: Se solucionaron los errores de permisos (`Acceso denegado`) en Windows al descargar canciones de YouTube para reproducirlas en el stream.
- **Lectura de Voz Limpia**: El motor de voz omite automáticamente mensajes que contengan solo símbolos, emojis repetidos o caracteres invisibles.
