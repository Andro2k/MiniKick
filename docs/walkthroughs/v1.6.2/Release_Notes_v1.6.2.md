# Notas de la Versión — MiniKick v1.6.2

Fecha de Publicación: 30 de Septiembre de 2026

La versión 1.6.2 de MiniKick incorpora un sistema guardián de pulso activo para la conexión de chat de Kick, protegiendo las transmisiones contra desconexiones silenciosas en momentos de inactividad, garantizando la fluidez instantánea del widget de Top Chatters desde el primer minuto del directo, blindando el servidor de overlays ante reinicios repentinos de fuentes de OBS Studio, asegurando la presentación completa del panel de novedades tanto en instalaciones locales como en paquetes distribuidos mediante sincronización híbrida con GitHub, ofreciendo una nueva pantalla de carga minimalista que proporciona retroalimentación visual inmediata durante la inicialización del sistema, blindando la apertura de enlaces de autenticación en distribuciones Linux y perfeccionando el ajuste dinámico de altura en las notificaciones emergentes.

---

## Novedades

A continuación se resumen las principales funcionalidades incorporadas en esta actualización:

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Chat | Guardián Activo de Conexión en Kick | Sistema inteligente de mantenimiento continuo del enlace de chat en segundo plano con verificación de pulso bidireccional. | Evita que el chat de Kick y los widgets se congelen o dejen de leer mensajes durante periodos de silencio antes o durante la transmisión, garantizando que el primer mensaje de tus espectadores entre siempre al instante. |
| Dashboard | Sincronización Híbrida de Novedades | Detección automática y presentación de notas de versión incorporadas en la aplicación o consultadas directamente desde GitHub. | Garantiza que al actualizar o instalar una nueva versión siempre puedas explorar las novedades y mejoras destacadas al abrir la app, con insignias visuales en el menú lateral y sin requerir descargas manuales. |
| Dashboard | Pantalla de Carga Minimalista | Tarjeta visual de bienvenida con seguimiento en tiempo real del progreso de inicialización del sistema y carga de servicios. | Proporciona retroalimentación visual instantánea al abrir la aplicación, eliminando tiempos de espera a ciegas y mostrando de forma clara y moderna el avance de preparación de la app. |
| Settings | Apertura Resiliente de Navegador en Linux | Integración nativa multi-nivel con los portales de escritorio y sesiones desacopladas en sistemas Linux y Wayland. | Asegura que al conectar tus cuentas de Kick o Twitch, la ventana del navegador web se abra siempre al instante sin importar la distribución o gestor de ventanas en uso. |

> [!NOTE]
> Estos mecanismos operan de manera totalmente transparente en segundo plano. No requieren ninguna configuración manual por parte del usuario ni introducen demoras en el arranque de la aplicación.

---

## Mejoras

* **Mantenimiento Continuo de Conexión y Protección contra Enlaces Inactivos:**
  Se implementó un mecanismo guardián que envía señales de verificación periódicas hacia los servidores de Kick cuando no hay actividad en el canal. Si los servidores o el enrutador de red interrumpen la conexión silenciosamente, la aplicación detecta el corte en menos de treinta segundos y restablece el enlace de inmediato, evitando congelamientos prolongados.

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


