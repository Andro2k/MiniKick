# Notas de la Versión — MiniKick v1.6.2

Fecha de Publicación: 30 de Septiembre de 2026

La versión 1.6.2 de MiniKick incorpora un sistema guardián de pulso activo para la conexión de chat de Kick y Twitch, protegiendo las transmisiones contra desconexiones silenciosas en momentos de inactividad, garantizando la fluidez instantánea del widget de Top Chatters desde el primer minuto del directo, blindando el servidor de overlays ante reinicios repentinos de fuentes de OBS Studio, asegurando la presentación completa del panel de novedades tanto en instalaciones locales como en paquetes distribuidos mediante sincronización híbrida con GitHub, ofreciendo una nueva pantalla de carga minimalista que proporciona retroalimentación visual inmediata durante la inicialización del sistema, blindando la apertura de enlaces de autenticación en distribuciones Linux, perfeccionando el ajuste dinámico de altura en las notificaciones emergentes y optimizando de forma integral la arquitectura de conexiones en tiempo real con reconexión adaptativa inteligente y procesamiento no bloqueante de alertas en Twitch.

---

## Novedades

A continuación se resumen las principales funcionalidades incorporadas en esta actualización:

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Chat | Guardián Activo de Conexión en Kick y Twitch | Sistema inteligente de mantenimiento continuo del enlace de chat en segundo plano con verificación de pulso bidireccional. | Evita que el chat y los widgets se congelen o dejen de leer mensajes durante periodos de silencio antes o durante la transmisión, garantizando que el primer mensaje de tus espectadores entre siempre al instante. |
| Chat | Reconexión Adaptativa Inteligente | Algoritmo de reintento suave y adaptativo con variación aleatoria para recuperar enlaces caídos tras cortes de red. | Permite recuperar el chat en solo uno o dos segundos ante micro-cortes efímeros de internet y previene la saturación de tu conexión durante fallos prolongados de los servidores. |
| Chat | Aislamiento Asíncrono de Alertas en Twitch | Procesamiento independiente y no bloqueante para la sincronización de alertas de directos y puntos de canal. | Asegura que la activación de alertas de seguidores, suscriptores, donaciones de bits y raids no cause retrasos ni demoras en la lectura fluida del chat en vivo. |
| Dashboard | Sincronización Híbrida de Novedades | Detección automática y presentación de notas de versión incorporadas en la aplicación o consultadas directamente desde GitHub. | Garantiza que al actualizar o instalar una nueva versión siempre puedas explorar las novedades y mejoras destacadas al abrir la app, con insignias visuales en el menú lateral y sin requerir descargas manuales. |
| Dashboard | Pantalla de Carga Minimalista | Tarjeta visual de bienvenida con seguimiento en tiempo real del progreso de inicialización del sistema y carga de servicios. | Proporciona retroalimentación visual instantánea al abrir la aplicación, eliminando tiempos de espera a ciegas y mostrando de forma clara y moderna el avance de preparación de la app. |
| Settings | Apertura Resiliente de Navegador en Linux | Integración nativa multi-nivel con los portales de escritorio y sesiones desacopladas en sistemas Linux y Wayland. | Asegura que al conectar tus cuentas de Kick o Twitch, la ventana del navegador web se abra siempre al instante sin importar la distribución o gestor de ventanas en uso. |

> [!NOTE]
> Estos mecanismos operan de manera totalmente transparente en segundo plano. No requieren ninguna configuración manual por parte del usuario ni introducen demoras en el arranque de la aplicación.

---

## Mejoras

* **Mantenimiento Continuo de Conexión y Protección contra Enlaces Inactivos:**
  Se implementó un mecanismo guardián que envía señales de verificación periódicas hacia los servidores de Kick y Twitch cuando no hay actividad en el canal. Si los servidores o el enrutador de red interrumpen la conexión silenciosamente, la aplicación detecta el corte en menos de treinta segundos y restablece el enlace de inmediato, evitando congelamientos prolongados.

* **Reconexión Automática con Retroceso Adaptativo:**
  En lugar de reintentar con pausas estáticas que pueden saturar la red, la aplicación ahora aplica un retroceso progresivo con variación temporal, intentando reconectar de inmediato tras caídas momentáneas y espaciando los intentos si el servicio tarda en responder.

* **Procesamiento de Emotes de Alto Rendimiento en Twitch:**
  Se rediseñó el algoritmo de limpieza y extracción de emoticonos para procesar los mensajes en un único recorrido lineal de alta velocidad, garantizando un rendimiento óptimo incluso en transmisiones con alta afluencia de espectadores y mensajes saturados de emotes.

* **Protección contra Mensajes y Eventos Duplicados:**
  Se incorporó un filtro de memoria ultrarrápido en las conexiones de chat y alertas que descarta retransmisiones duplicadas de forma instantánea durante el proceso de reconexión.

* **Arranque con Retroalimentación Visual Inmediata:**
  Al iniciar MiniKick, se despliega al instante una pantalla de carga estilizada en tono oscuro con una barra de progreso ultrafina e indicadores textuales que detallan el avance de la inicialización de módulos, servicios y entorno gráfico, ofreciendo una experiencia fluida y profesional desde el primer segundo.

* **Adaptación Geométrica Dinámica en Notificaciones Emergentes:**
  Las alertas visuales en pantalla ahora calculan de forma dinámica y exacta su altura en función de la longitud del texto, expandiéndose suavemente para acomodar mensajes de múltiples líneas con márgenes equilibrados y eliminando cualquier recorte visual en el borde inferior.

* **Caché Instantánea de Notas de Versión en Arranque:**
  Las novedades y funciones destacadas se almacenan localmente tras su primera lectura exitosa, permitiendo que en los siguientes inicios de MiniKick la ventana informativa y las insignias del menú lateral carguen al instante sin consumir datos de red ni generar esperas visuales.

* **Blindaje contra Desconexiones Repentinas de OBS:**
  Se perfeccionó el gestor de recursos de overlay para tolerar desconexiones instantáneas de fuentes de navegador de OBS al alternar escenas, eliminando advertencias y registros innecesarios en el historial de eventos.

* **Resiliencia y Fluidez Continua en Overlays:**
  Al prevenir desconexiones no detectadas en salas con baja concurrencia o previas al inicio de la emisión, el podio en pantalla de espectadores más participativos (Top Chatters) y el sintetizador de voz reaccionan al instante ante la llegada de nuevos mensajes.

---

## Correcciones

* **Corrección de Bloqueos Potenciales en la Conexión de Alertas de Twitch:**
  Se eliminó el riesgo de desconexión por tiempo de espera al vincular alertas de Twitch, despachando la suscripción de eventos de forma asíncrona para que la recepción de datos y la comprobación de estado de la conexión continúen activas sin interrupciones.

* **Corrección de Congelamiento Inicial en Chat y Top Chatters en Kick:**
  Se solucionó la anomalía por la cual la aplicación dejaba de leer mensajes y mantenía estático el ranking de Top Chatters durante los primeros minutos de transmisión debido al cierre silencioso de la conexión por inactividad previa, asegurando respuesta inmediata desde el primer mensaje enviado al canal.

* **Corrección de Ausencia de Novedades en Versiones Empaquetadas:**
  Se resolvió el problema por el cual la ventana de bienvenida y novedades no se desplegaba al exportar el ejecutable distribuible de la aplicación, empaquetando la documentación necesaria de forma nativa e incorporando consulta automática a las publicaciones oficiales en GitHub como mecanismo de respaldo.

* **Corrección de Cierre Abrupto al Fallar Autenticación en Linux:**
  Se subsanó la excepción interna que provocaba el cierre repentino de la aplicación si se producía una demora o fallo en la vinculación de cuentas en sistemas Linux, asegurando que la interfaz maneje los estados de error de forma segura e informe adecuadamente al usuario.

* **Corrección de Recorte en Mensajes de Notificación:**
  Se eliminó el defecto por el cual avisos con mensajes extensos (como el recordatorio de autenticación en curso) mostraban la última línea de texto cortada por la mitad, garantizando una lectura nítida y completa de todas las alertas.

* **Corrección de Espera a Ciegas en el Arranque Inicial:**
  Se solucionó la carencia de retroalimentación gráfica al iniciar la aplicación, donde en equipos con alta demanda de recursos la ventana principal tardaba unos segundos en desplegarse sin ningún aviso en pantalla, garantizando un arranque transparente y controlado.
