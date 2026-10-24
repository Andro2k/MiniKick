# Notas de la Versión — MiniKick v1.6.5

Fecha de Publicación: 16 de octubre de 2026

MiniKick 1.6.5 renueva la experiencia visual y el overlay de música, facilita la configuración inicial desde el Dashboard e incorpora nuevas opciones para controlar las actualizaciones. También incluye ajustes para que la aplicación sea más clara, adaptable y estable durante el uso diario.

---

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Music | Diseños Classic y Vinyl para el overlay | Elige entre un reproductor con portada y detalles de la canción, o un diseño inspirado en un disco de vinilo. Ambos muestran el título, el artista y el progreso de reproducción. | Personaliza la fuente de música en OBS y permite que tu audiencia identifique lo que está sonando. |
| Dashboard | Bienvenida y configuración inicial | La bienvenida reúne accesos para conectar plataformas, crear comandos, configurar timers y vincular recompensas, junto con el estado de configuración disponible. | Encuentra las tareas iniciales y llega directamente a las secciones que necesitas configurar. |
| Dashboard | Perfil del canal y actividad por plataforma | Consulta los datos del canal, ajusta el tamaño del avatar y revisa la actividad de tus plataformas. Si Kick y Twitch están conectados, puedes alternar entre ambos perfiles desde la bienvenida. | Personaliza el panel y comprueba de un vistazo qué canal está activo y dónde participa tu audiencia. |
| Settings | Descarga automática opcional de actualizaciones | Activa la descarga de actualizaciones al iniciar MiniKick. La instalación y el reinicio solo ocurren después de tu confirmación; si desactivas la opción, puedes seguir actualizando manualmente. | Elige entre preparar las actualizaciones automáticamente o conservar el control manual. |
| Developer | Instalación de Windows desde PowerShell | El instalador remoto permite una instalación interactiva o silenciosa y comprueba la integridad del paquete antes de ejecutarlo. | Simplifica la instalación y ayuda a evitar ejecutar un paquete que no haya superado la verificación. |

## Mejoras

- **Overlay adaptable a OBS:** los diseños musicales ajustan sus elementos al espacio disponible y acortan títulos o nombres extensos para conservar una composición legible. Sus acentos de color acompañan la portada de la canción.
- **Bienvenida más clara:** la información del canal se presenta de forma compacta, las tarjetas de conexión se adaptan a ventanas estrechas y el tamaño del avatar se puede ajustar.
- **Controles de TTS más compactos:** los interruptores para habilitar plataformas de chat ocupan menos espacio y son más fáciles de revisar junto a los ajustes de voz.
- **Interfaz más consistente:** se mejoraron la legibilidad del tema oscuro, los estados de foco y la presentación de botones, tarjetas y controles. Los estilos y márgenes mantienen una apariencia más uniforme en las distintas secciones.
- **Secciones listas cuando las necesitas:** MiniKick abre primero el Dashboard y prepara las demás secciones al visitarlas. Una vez abiertas, quedan disponibles al volver a ellas.
- **Cierre más fluido:** las conexiones en segundo plano se detienen de forma coordinada, evitando que la ventana tenga que esperar a cada una por separado.
- **Actualizaciones automáticas bajo tu control:** la descarga es opcional, se realiza en segundo plano y siempre pide confirmación antes de instalar y reiniciar.

## Correcciones

- Si un enlace del overlay indica un diseño que ya no está disponible, se utiliza Classic para que la música continúe visible.
- Se corrigieron recortes de la portada, el disco y el brazo del diseño Vinyl en fuentes de OBS pequeñas, así como desbordamientos causados por metadatos extensos.
- Al desconectar o cambiar el perfil activo, la bienvenida deja de mostrar información del canal anterior.
- Al navegar a Chat, la sección se carga correctamente y la aplicación permanece disponible.
- La instalación remota se detiene cuando el paquete no corresponde a la versión esperada o no puede verificarse.
- Se reforzó la coordinación del cierre para evitar que operaciones en segundo plano utilicen servicios después de que la aplicación los haya cerrado.
- Si una descarga automática no puede comenzar o falla, MiniKick informa el problema y no inicia la instalación.
