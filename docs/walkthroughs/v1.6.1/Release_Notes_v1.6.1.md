# Notas de la Versión — MiniKick v1.6.1

Fecha de Publicación: 26 de Septiembre de 2026

La versión 1.6.1 de MiniKick introduce mejoras sustanciales en la persistencia de métricas de transmisión, integración y limpieza del área de trabajo del chat, estabilidad de comandos interactivos, optimización en el servidor de overlays para OBS Studio y un sistema avanzado de registro de actividad estructurado de alta precisión.

---

## Novedades

A continuación se resumen las nuevas funcionalidades incorporadas en esta actualización:

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Widgets | Persistencia Diaria de Top Chatters | Almacenamiento continuo del ranking de espectadores más activos particionado por día. | Si la aplicación se cierra, se reinicia o se pierde la conexión durante el directo, el ranking de chatters del día actual no se reinicia ni se pierde, restaurándose de inmediato en la interfaz y en el overlay de OBS. |
| Dashboard | Centro de Control Ejecutivo y Tabla de Top Chatters | Rediseño integral de la pantalla principal con tabla interactiva de espectadores más participativos, filtros históricos (Hoy, Ayer, selector de fecha) y tarjetas de conexión compactas. | Permite al streamer monitorear de un vistazo la salud de todas sus plataformas y consultar en tiempo real o por fecha quiénes son los miembros más activos de su comunidad con barras de participación. |
| Comandos | Normalización Automática de Comandos | Formateo predictivo al crear o editar comandos: reemplazo automático de espacios por guiones bajos y conversión a minúsculas. | Garantiza que todos los comandos creados por el streamer se reconozcan y ejecuten siempre en el chat sin fallos por espacios o mayúsculas involuntarias. |
| Chat | Integración de Filtros Anti-Spam en el Chat | Nueva pestaña dedicada para la configuración de moderación automática dentro de la vista principal del chat. | Permite ajustar mayúsculas, enlaces, emotes excesivos y repeticiones directamente en el chat, eliminando la necesidad de cambiar a otra sección. |
| Developer | Auditoría en Vivo de Overlays en OBS | Registro transparente y estructurado de las conexiones y desconexiones de fuentes de navegador de OBS (Chat, Música, Widgets, Alertas). | Permite al streamer verificar con certeza si OBS mantiene conectadas sus fuentes de overlay o si alguna escena las suspendió o reinició. |
| Dashboard | Sistema de Bienvenida e Insignias de Novedades | Ventana interactiva al actualizar o instalar la app, complementada con insignias naranjas reactivas en la navegación. | Al ingresar tras una actualización o por primera vez, el usuario conoce de inmediato las mejoras añadidas. Las secciones con novedades se identifican con una insignia naranja que desaparece al explorarlas. |
| Dashboard | Activación y Actualización en Vivo de Top Chatters | Aviso inteligente en la tabla cuando el módulo está inactivo con botón de encendido en un clic y actualización automática de posiciones sin recargar. | Si el módulo está apagado, la aplicación te sugiere activarlo directamente desde la pantalla principal sin tener que navegar a otra pestaña. Al estar activo, las posiciones y mensajes del día se actualizan en vivo en la pantalla conforme los espectadores van participando en el chat. |
| Widgets | Conteo Opcional de Comandos en Top Chatters | Nueva casilla en la configuración del widget para decidir si los comandos de chat se contabilizan o se descartan del ranking. | Otorga al streamer la libertad de elegir si desea premiar únicamente la conversación habitual o incluir la participación interactiva por comandos y minijuegos en el podio. |
| Chat | Comando de Ayuda y Listado por Categorías | Nuevo comando nativo en el chat con desglose temático (Chat, Música, Widgets, Moderación) y partición inteligente multimensaje. | Permite a cualquier espectador conocer los comandos disponibles en el canal sin saturar el chat y sin que los mensajes se corten por límites de caracteres en Kick o Twitch. |

> [!NOTE]
> Al iniciar la aplicación, si existen comandos creados en versiones anteriores que contengan espacios, la tabla de comandos alertará amablemente al usuario indicando el formato recomendado para mantener su correcto funcionamiento.

---

## Mejoras

* **Rediseño Profesional del Hub de Conexiones:**
  Las tarjetas de estado de cada plataforma ahora cuentan con un diseño estilizado y compacto, con indicadores luminosos en vivo (En línea, Conectando, Inactivo) y contadores de mensajes por sesión, optimizando el espacio visual de la pantalla principal.

* **Descongestión de la Barra de Navegación Lateral:**
  Se reubicó la sección de filtros anti-spam dentro de las pestañas del chat, liberando espacio vertical en el menú principal para ofrecer una barra lateral más limpia y centrada en los módulos de uso continuo durante la transmisión.

* **Optimización en el Servidor de Overlays:**
  Se redujo el consumo de procesamiento al enviar eventos a múltiples fuentes de OBS abiertas en simultáneo. Los mensajes se procesan y emiten de forma unificada hacia todas las capas de overlay, eliminando tareas redundantes y reduciendo la latencia de despacho por debajo del milisegundo.

* **Blindaje y Protección de Sockets en OBS Studio:**
  Se añadieron controles de inactividad y desconexión segura en las conexiones de navegador. Si OBS entra en modo de reposo o congela temporalmente una fuente de navegador, la aplicación gestiona la espera sin bloquear las transmisiones de las demás fuentes ni el funcionamiento de la ventana principal.

* **Nuevo Sistema de Logs Estructurados de Alta Precisión:**
  El registro de actividad en disco ahora cuenta con marcas de tiempo con milisegundos y zona horaria local, así como nombres limpios y alineados por servicio. Esto facilita el análisis de transmisiones y la verificación de tiempos de respuesta exactos de cada plataforma de streaming.

* **Ajuste Visual Responsivo en la Tabla de Comandos:**
  La columna de comandos en la lista principal ahora se adapta dinámicamente al ancho del texto, permitiendo visualizar comandos con nombres extensos sin que se recorten o queden ilegibles.

* **Sincronización Directa de Novedades y Optimización de Almacenamiento:**
  El diálogo de bienvenida y las insignias de navegación ahora leen de forma automática el registro oficial de novedades de cada versión, manteniendo la base de datos interna limpia y ligera sin acumulación de datos residuales entre actualizaciones sucesivas.

* **Apertura Maximizada y Memoria de Posición de Ventana:**
  La aplicación ahora se inicia automáticamente en pantalla completa maximizada para una visualización inmediata y despejada. Asimismo, el sistema recuerda inteligentemente si prefieres trabajar en una ventana flotante con una posición y tamaño específicos, restaurando ese estado exacto en cada inicio o al recuperarla desde la bandeja del sistema.

* **Optimización de Carga en Formularios y Diálogos:**
  Se aceleró la apertura de ventanas secundarias y reporte de incidencias mediante la reutilización en memoria de la conexión de datos activa, eliminando comprobaciones de disco redundantes en el hilo principal.

* **Actualización en Tiempo Real de Espectadores Participativos:**
  La lista de los miembros más activos ahora reacciona de forma inmediata a los mensajes que ingresan durante la sesión. El sistema consolida y refresca los porcentajes y medallas en pantalla automáticamente, eliminando la necesidad de cambiar de fecha para consultar el estado actual.

* **Partición Multimensaje Adaptada a Plataformas:**
  El listado de comandos respeta estrictamente los límites de longitud de Kick y Twitch (máximo 380 caracteres seguros). Si la cantidad de comandos activos excede la capacidad de un solo mensaje, el sistema divide automáticamente el contenido por secciones temáticas o bloques correlativos y los envía de manera secuencial sin bloquear la transmisión.

* **Privacidad y Filtro Automático por Rangos:**
  Los comandos de moderación y control interno se ocultan automáticamente para la audiencia regular, mostrándose únicamente cuando la solicitud proviene del streamer o de sus moderadores autorizados.

> [!TIP]
> Para garantizar que los overlays no experimenten demoras al cambiar de escena en OBS Studio, se aconseja mantener desmarcada la opción "Apagar la fuente cuando no sea visible" en las propiedades de la fuente de navegador de OBS.

---

## Correcciones

* **Protección de Credenciales en Logs de Overlays:**
  Se eliminó la inclusión del token de seguridad en las líneas informativas de arranque del servidor de overlays, protegiendo las credenciales del streamer en caso de compartir archivos de registro para asistencia o soporte.

* **Corrección de Ejecución en Comandos con Espacios:**
  Se solventó el problema por el cual comandos que contenían espacios no podían ser interpretados por el motor de chat, asegurando que todos los disparadores sigan un patrón canónico ejecutable en cualquier plataforma.

* **Prevención de Doble Ajuste en Comando de Volumen:**
  Se corrigió una duplicidad en la propagación de eventos al modificar el volumen de la música desde el chat, garantizando que el reproductor y los registros de almacenamiento respondan con una única actualización instantánea.

* **Persistencia Atómica de Ventana al Cerrar:**
  Se eliminó el doble guardado de estado al salir de la aplicación, consolidando la persistencia de geometría en una única operación fluida.

* **Transparencia en el Estado de Registro de Chat:**
  Se solucionó la falta de aviso cuando el seguimiento de mensajes se encontraba pausado, ofreciendo una indicación visible y una vía rápida para encenderlo inmediatamente.

* **Prevención de Truncamiento en Respuestas de Chat:**
  Se eliminó el riesgo de que respuestas extensas de comandos sean cortadas o rechazadas silenciosamente por los servidores de Kick o Twitch, asegurando entrega completa y ordenada.

* **Eliminación de Auto-respuestas y Bucles de Bot en Kick:**
  Se solventó el problema por el cual los mensajes enviados por el bot eran interpretados por el propio sistema como mensajes de espectadores, evitando que el bot ejecute comandos sobre sus propias respuestas al listar enlaces o comandos del canal.

* **Sincronización Inmediata de Comandos en el Primer Arranque:**
  Se corrigió la falta de actualización en la tabla de comandos al iniciar la aplicación tras una actualización, garantizando que todos los comandos nuevos del sistema aparezcan reflejados de inmediato en pantalla sin requerir un reinicio posterior.
