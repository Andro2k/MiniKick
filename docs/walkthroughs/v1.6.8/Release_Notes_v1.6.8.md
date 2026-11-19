# Notas de la Versión — MiniKick v1.6.8

Fecha de Publicación: 15 de noviembre de 2026

MiniKick 1.6.8 amplía las herramientas para gestionar la música y conectar los eventos del stream con servicios externos. También mejora el diseño en ventanas estrechas, actualiza la presentación de la aplicación y sus traducciones, y corrige problemas de actualización, cierre de sesión y miniaturas de Recompensas.

---

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Developer | Webhooks para eventos del stream | Configura destinos para Discord o servicios HTTP compatibles, elige plataforma y eventos, activa o desactiva destinos, filtra y administra la lista, y envía un ping de prueba que muestra el estado y la latencia. Discord utiliza mensajes enriquecidos; los destinos genéricos reciben JSON y pueden usar firma para verificar los mensajes. | Integra alertas y actividad de MiniKick con automatizaciones y servicios externos. |
| Music | Historial de canciones | Consulta hasta 100 canciones reproducidas o quitadas de la cola, con título, autor, solicitante y duración. Puedes volver a agregar una canción a la cola. | Recupera canciones recientes con rapidez. |
| Music | Playlists | Crea y elimina playlists, agrega la canción actual o una canción del historial, quita canciones y agrega una playlist completa a la cola. | Organiza canciones y prepara la música del stream desde la aplicación. |
| Music | Vista previa de video | Abre desde el historial una vista previa sin audio. MiniKick reproduce el archivo de video local en caché cuando es compatible y, si no está disponible, intenta mostrar el video de YouTube. Desde la vista previa también puedes abrir el enlace en el navegador cuando no se pueda incrustar. | Comprueba visualmente qué canción está seleccionada sin duplicar el audio del reproductor. |
| Music | Compatibilidad con streams de YouTube | MiniKick puede obtener tokens de verificación requeridos por algunos streams al resolver música con clientes web compatibles. | Puede resolver canciones que antes fallaban con el aviso de YouTube para confirmar que no eres un bot. |
| Rewards | Recarga de miniaturas | Usa el botón junto a la búsqueda para volver a generar miniaturas con los archivos actuales. La tabla se actualiza al terminar y muestra cuántas miniaturas se regeneraron. | Refresca imágenes y estados de archivos después de mover o restaurar contenido. |

## Mejoras

- **Webhooks más resistentes y seguros:** los envíos se procesan en segundo plano para no frenar el chat ni las alertas. Hay reintentos automáticos, límites para la cola y aislamiento por destino para que una dirección lenta o caída no detenga las demás. La espera indicada por el servidor se respeta con un límite. Las direcciones de Discord requieren HTTPS; la aplicación advierte sobre HTTP en otros destinos. Las direcciones y claves de firma se guardan cifradas, y los tokens de Discord se ocultan en los registros. Los mensajes de Discord evitan menciones masivas.
- **Más eventos para integraciones:** los destinos pueden recibir suscripciones, resuscripciones, suscripciones regaladas, cheers, follows, raids, canjes, comandos ejecutados, cambios de canción y, si se habilitan, mensajes de chat. La disponibilidad depende de los eventos que la plataforma conectada proporciona a MiniKick.
- **Reproductor de música más compacto:** la configuración del overlay se inicia plegada, para dejar más espacio a la pestaña Reproductor. La vista previa usa colores coherentes con el tema y las tarjetas de Cola e Historial se alinean mejor con las pestañas.
- **Vista previa de video más práctica:** los videos locales en caché se muestran sin audio y se pueden pausar o reanudar con un clic. Si no hay un archivo compatible, se usa la vista web de YouTube. La aplicación detecta errores, permite abrir el enlace externamente, libera el reproductor al ocultar la vista y tolera ocultamientos breves sin cerrarlo. La carga web no se inicia hasta que se necesita.
- **Resolución de música desde YouTube:** los clientes web de yt-dlp pueden solicitar tokens de verificación generados por una página oculta, con caché temporal y reintentos ante fallos. Los clientes de iOS y Android no esperan por este proceso, y la música puede seguir resolviéndose sin token si el registro del proveedor falla.
- **Controles y presentación:** los sliders tienen extremos redondeados y las pestañas de Cola e Historial ya no dejan una cuña visual en la esquina. Se silencian avisos de JavaScript originados por la página de YouTube que no corresponden a errores de MiniKick.
- **Ventanas adaptables:** se define un tamaño mínimo para la ventana, el menú lateral se contrae al reducirse el espacio y recupera la preferencia del usuario al ampliar la ventana. Dashboard, estadísticas, chat, agenda, alertas y música adaptan su distribución al ancho disponible. Las tablas de Comandos y Recompensas caben en ventanas estrechas; en Recompensas se oculta temporalmente la columna Posición cuando no hay espacio suficiente.
- **Traducciones y plurales:** el español y el inglés pasan a mensajes Fluent, con plurales correctos en textos como canciones, límites, posiciones y cantidades. Las variables se insertan al resolver el mensaje, y la aplicación recurre al inglés si falta una traducción en el idioma activo.
- **Iconos consistentes:** los iconos se organizan en packs, se normalizan para compartir lienzo y alineación, y la interfaz adopta el estilo Lucide. Se actualizan los nombres y referencias de los iconos y se conserva un icono propio para los elementos sin equivalente en el pack. El icono de la aplicación se regenera en varios tamaños para el ejecutable y el instalador.
- **Instalación y actualizador:** la compilación obtiene la versión de una sola fuente sin modificar el script del instalador. Las actualizaciones silenciosas registran la instalación y pueden volver a abrir MiniKick sin abrir ventanas adicionales ni recrear un acceso directo que el usuario quitó.
- **Estructura y mantenimiento:** los módulos de backend, frontend, arranque y herramientas se reorganizan por función y reciben convenciones de nombres y documentación consistentes. Las comprobaciones del proyecto ahora detectan nombres fuera de convención y puntos de corte de diseño codificados directamente. Estos cambios organizativos no requieren ajustes por parte del usuario.

## Correcciones

- **Miniaturas de Recompensas:** se corrige el caso en que una miniatura ausente quedaba guardada como vacía y no volvía a intentarse. Las lecturas de la vista dejan de generar miniaturas y bloquear la interfaz. La recarga se ejecuta en segundo plano, procesa los archivos en secuencia con un reproductor reutilizado, limita el tiempo por archivo, evita ejecuciones duplicadas y continúa aunque uno de ellos falle. Los audios no se procesan como videos y una captura fallida no borra una miniatura existente. Los registros permiten identificar el archivo que se estaba procesando.
- **Captura de video para miniaturas:** la captura espera a que el medio esté listo, termina pronto ante errores y deja información del estado del reproductor cuando no se obtiene un fotograma. Se corrige también la gestión del temporizador para que no queden capturas pendientes.
- **Historial y playlists:** las playlists ya no pueden crearse con un nombre vacío y el botón de confirmación se habilita solo con un nombre válido. Se corrige la inicialización del diálogo de selección y se aclara la acción de agregar a una playlist desde el reproductor o el historial.
- **Autenticación y cierre:** cerrar MiniKick mientras Kick o Twitch esperan la respuesta del login ahora cancela la espera en lugar de mantener un worker activo hasta agotar el tiempo máximo.
- **Detección de actualizaciones:** las versiones se comparan por sus componentes numéricos, por lo que una versión como 1.6.10 se reconoce como posterior a 1.6.9. Los tags sin números no se anuncian como versiones nuevas.
- **Diálogo de actualización:** se corrigen el alto de la barra de progreso, el cálculo del espacio del diálogo y el repintado entre estados, que podía dejar textos superpuestos hasta mover el cursor. Se simplifica también la tarjeta de actualización del menú lateral.
- **Instalador:** se corrigen las rutas de recursos y de salida del instalador. La actualización silenciosa ya no abre el asistente de forma interactiva ni crea de nuevo un acceso directo eliminado por el usuario.
- **Tablas estrechas:** se ajustan las columnas de Comandos y se oculta Posición en Recompensas cuando no cabe, evitando que las cabeceras o los datos queden cortados por el desplazamiento horizontal.
- **Webhooks:** el filtro de búsqueda se conserva tras activar, guardar o eliminar un destino; los destinos que no se pueden descifrar se preservan al guardar desde otro perfil; la prueba de Discord muestra su título correcto; y el servicio rechaza destinos sin eventos o plataformas seleccionados.
- **Iconos y elementos visuales:** se corrige el icono de la aplicación usado por el ejecutable y el instalador, y se ajustan la cuadrícula, el centrado y algunas equivalencias visuales del pack.

> [!NOTE]
> La vista previa de YouTube y la generación de tokens para ciertos streams requieren validación adicional en Windows. La vista previa puede cerrar el video al ocultar la ventana y no se reanuda automáticamente. El historial agrupa canciones reproducidas y canciones quitadas de la cola.

> [!IMPORTANT]
> La compilación del instalador con Inno Setup, la actualización silenciosa real y algunas comprobaciones visuales de Windows quedaron pendientes en los walkthroughs. La entrega de webhooks con Discord o servicios reales también requiere una prueba manual de integración.
