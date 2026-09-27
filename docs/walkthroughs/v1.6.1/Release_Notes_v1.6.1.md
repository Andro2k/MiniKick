# Notas de la Versión — MiniKick v1.6.1

Fecha de Publicación: 26 de Septiembre de 2026

La versión 1.6.1 de MiniKick introduce mejoras sustanciales en la persistencia de métricas de transmisión, integración y limpieza del área de trabajo del chat, estabilidad de comandos interactivos, optimización en el servidor de overlays para OBS Studio y un sistema avanzado de registro de actividad estructurado de alta precisión.

---

## Novedades

A continuación se resumen las nuevas funcionalidades incorporadas en esta actualización:

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Widgets | Persistencia Diaria de Top Chatters | Almacenamiento continuo del ranking de espectadores más activos particionado por día. | Si la aplicación se cierra, se reinicia o se pierde la conexión durante el directo, el ranking de chatters del día actual no se reinicia ni se pierde, restaurándose de inmediato en la interfaz y en el overlay de OBS. |
| Comandos | Normalización Automática de Comandos | Formateo predictivo al crear o editar comandos: reemplazo automático de espacios por guiones bajos y conversión a minúsculas. | Garantiza que todos los comandos creados por el streamer se reconozcan y ejecuten siempre en el chat sin fallos por espacios o mayúsculas involuntarias. |
| Chat | Integración de Filtros Anti-Spam en el Chat | Nueva pestaña dedicada para la configuración de moderación automática dentro de la vista principal del chat. | Permite ajustar mayúsculas, enlaces, emotes excesivos y repeticiones directamente en el chat, eliminando la necesidad de cambiar a otra sección. |
| Developer | Auditoría en Vivo de Overlays en OBS | Registro transparente y estructurado de las conexiones y desconexiones de fuentes de navegador de OBS (Chat, Música, Widgets, Alertas). | Permite al streamer verificar con certeza si OBS mantiene conectadas sus fuentes de overlay o si alguna escena las suspendió o reinició. |
| Dashboard | Sistema de Bienvenida e Insignias de Novedades | Ventana interactiva al actualizar o instalar la app, complementada con insignias naranjas reactivas en la navegación. | Al ingresar tras una actualización o por primera vez, el usuario conoce de inmediato las mejoras añadidas. Las secciones con novedades se identifican con una insignia naranja que desaparece al explorarlas. |

> [!NOTE]
> Al iniciar la aplicación, si existen comandos creados en versiones anteriores que contengan espacios, la tabla de comandos alertará amablemente al usuario indicando el formato recomendado para mantener su correcto funcionamiento.

---

## Mejoras

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

> [!TIP]
> Para garantizar que los overlays no experimenten demoras al cambiar de escena en OBS Studio, se aconseja mantener desmarcada la opción "Apagar la fuente cuando no sea visible" en las propiedades de la fuente de navegador de OBS.

---

## Correcciones

* **Protección de Credenciales en Logs de Overlays:**
  Se eliminó la inclusión del token de seguridad en las líneas informativas de arranque del servidor de overlays, protegiendo las credenciales del streamer en caso de compartir archivos de registro para asistencia o soporte.

* **Corrección de Ejecución en Comandos con Espacios:**
  Se solventó el problema por el cual comandos que contenían espacios no podían ser interpretados por el motor de chat, asegurando que todos los disparadores sigan un patrón canónico ejecutable en cualquier plataforma.
