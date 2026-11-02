# Notas de la Versión — MiniKick v1.6.6

Fecha de Publicación: 1 de noviembre de 2026

MiniKick 1.6.6 reúne mejoras de estabilidad, rendimiento y presentación para que puedas gestionar tus plataformas y herramientas de streaming con menos interrupciones. La actualización agiliza la navegación y el registro de actividad, facilita la configuración, mejora el chat flotante y unifica la apariencia de las distintas secciones.

---

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Chat | Ventana flotante independiente | Mantén el chat en una ventana separada, con su propio botón en la barra de tareas. Puedes minimizarla sin que vuelva automáticamente a la ventana principal. | Consulta el chat mientras organizas otras ventanas y conserva el espacio de trabajo que prefieras. |
| Settings | Configuración general editable | Los ajustes generales se guardan en un archivo legible y se trasladan automáticamente desde la configuración anterior cuando corresponde. | Facilita revisar y respaldar las preferencias sin tener que volver a configurar la aplicación. |
| Settings | Estado de plataformas más claro | Kick, Twitch, YouTube y TikTok comparten una presentación de conexión coherente; las conexiones automáticas ya no interrumpen el inicio con avisos de éxito. | Revisa tus integraciones con menos ruido y conserva los avisos al conectar manualmente. |
| Widgets | Vista reorganizada | La sección presenta sus opciones en una columna centrada con un estilo más claro y coherente con el resto de la aplicación. | Es más sencillo revisar y configurar los widgets. |

> [!IMPORTANT]
> El archivo de configuración puede contener el acceso del overlay. Protégelo como información privada. Las credenciales de las plataformas conservan su protección actual.

## Mejoras

- **Navegación más ágil:** se redujeron operaciones repetidas al abrir Ajustes y otras secciones, y las vistas se preparan progresivamente cuando la aplicación está disponible.
- **Menos pausas al registrar actividad:** el historial se guarda en lotes en segundo plano, reduciendo el trabajo que acompaña a cada mensaje o evento.
- **Ajustes más rápidos de consultar:** las lecturas repetidas de preferencias evitan accesos redundantes al almacenamiento.
- **Inicio y cierre más confiables:** las conexiones, búsquedas y tareas en segundo plano responden mejor a la cancelación y se detienen de manera ordenada al cerrar MiniKick.
- **Apariencia más consistente:** se armonizaron tamaños de iconos, controles, botones, espacios, tarjetas y anchos de contenido entre las secciones.
- **Diálogos más nítidos:** los iconos vectoriales conservan mejor sus bordes y definición en pantallas con distintas escalas.
- **Menos notificaciones invasivas:** se eliminaron las notificaciones del sistema operativo asociadas al cambio de idioma, al minimizar en la bandeja y a los controles de voz. Los avisos dentro de MiniKick siguen disponibles para las acciones que requieren confirmación o informan de errores.
- **Ajustes de voz y música más limpios:** se simplificaron las filas de configuración y se eliminaron etiquetas de estado repetidas en la lista de voces.
- **Mantenimiento más cuidadoso:** MiniKick puede recuperar espacio de la base de datos cuando es conveniente y registra objetos inesperados sin eliminarlos automáticamente.

## Correcciones

- Se corrigió un error que podía impedir mostrar correctamente la ayuda de comandos por categoría.
- Se reparó la apertura de Ajustes y la conexión de sus acciones para YouTube y TikTok.
- Se evitó reconstruir tablas de plataformas cuando su estado no había cambiado, reduciendo esperas al volver a ciertas secciones.
- Se corrigieron bloqueos y cierres tardíos asociados a esperas no interrumpibles en conexiones y servicios en segundo plano.
- Se mejoró la cancelación de búsquedas musicales y la limpieza de recursos de voz y audio al finalizar tareas.
- Se corrigieron casos en los que los resultados de tareas canceladas podían llegar a vistas que ya estaban cerradas.
- Se ajustó la presentación de controles deshabilitados, botones de búsqueda, filas de ajustes y ventanas emergentes para que sus estados sean visibles y coherentes.
- Se corrigió la conservación del idioma elegido durante el inicio y se mejoró la tolerancia ante archivos de configuración ilegibles.
