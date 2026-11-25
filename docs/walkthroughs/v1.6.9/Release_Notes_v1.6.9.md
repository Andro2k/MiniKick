# Notas de la Versión — MiniKick v1.6.9

Fecha de Publicación: 25 de noviembre de 2026

MiniKick 1.6.9 refuerza la seguridad de los overlays y del chat frente al contenido que envían los espectadores, corrige varios filtros, comandos y widgets, y añade registros para investigar por qué algunos canjes de puntos de canal no se activan o no se reproducen en el overlay de Recompensas.

---

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Widgets | Aviso de servidor de overlays no disponible | Si MiniKick no puede iniciar el servidor local de los overlays, por ejemplo porque otra copia de MiniKick u otro programa ya usa el puerto, muestra al arrancar una notificación de error con el puerto afectado. | Sabes de inmediato por qué los overlays no cargan en OBS, en lugar de encontrarte fuentes vacías sin explicación. |
| Rewards | Diagnóstico de canjes y de la reproducción en el overlay | El registro de MiniKick anota por qué un canje de puntos de canal no produce ninguna acción: recompensa sin configuración para ese título, evento incompleto, canje duplicado ignorado o suscripciones de Twitch. También anota los fallos de reproducción del overlay de Recompensas: audio bloqueado por el navegador, formato no compatible, archivo no encontrado o rechazado, o reproducción que termina de inmediato. | Permite identificar la causa cuando una recompensa no se activa o aparece sin sonido, y adjuntarla al reportar el problema. |

## Mejoras

- **Overlays protegidos frente al contenido de los espectadores:** el combo de emotes y las alertas ya no interpretan como código los nombres de emotes, los mensajes ni los nombres de usuario; siempre se muestran como texto. Las plantillas de alerta que escribes tú conservan su formato y la lectura en voz alta de las alertas no cambia.
- **Conexiones de los overlays más estrictas:** el servidor local rechaza las conexiones a canales de overlay que no existen y corta las que envían mensajes de más de 1 MB, para que un cliente defectuoso no pueda consumir la memoria del equipo.
- **Alertas con página HTML propia:** desde la carpeta de una alerta HTML personalizada solo se entregan archivos web: páginas, estilos, scripts, imágenes, audio, video, fuentes y datos en formato JSON. El resto de archivos que haya en esa carpeta, como documentos o configuraciones, ya no se pueden pedir a través del overlay, por ejemplo si la dirección de la fuente de OBS se muestra en pantalla.
- **GIF directos del chat:** los enlaces directos a GIF solo se muestran si usan https y pertenecen a dominios conocidos de GIF y emotes (Giphy, Tenor, 7TV, BetterTTV, FrankerFaceZ, Kick, Twitch y Discord), para que un espectador no pueda cargar imágenes desde servidores arbitrarios en tu overlay. Los GIF de Giphy no cambian.

## Correcciones

- **Respuestas de comandos:** el nombre del usuario y el del destinatario que se insertan en la respuesta de un comando se limpian. Ya no pueden empezar por /, . o !, de modo que un espectador no puede lograr que el mensaje del bot empiece como un comando de Twitch o de otro bot; se limitan a 40 caracteres y, si no se indica destinatario (por ejemplo, solo @), se usa el nombre de quien ejecuta el comando. Además, un valor escrito por un espectador ya no se vuelve a interpretar como variable, como el valor aleatorio. Las plantillas que escribas empezando por / siguen funcionando.
- **Filtro de enlaces:** la lista de enlaces permitidos compara el dominio real del enlace. Permitir un dominio ya no deja pasar otro que lo contenga en su nombre o en el resto de la dirección.
- **Filtros de mayúsculas, emotes y repetición:** cuando no tenían una cantidad máxima guardada, marcaban cualquier mensaje. Ahora usan 10 por defecto, el valor que muestra la interfaz.
- **Ajustes del Chat:** guardar los ajustes de la vista ya no borra la clave propia de Giphy ni las opciones de la voz Piper, por lo que el comando !gif vuelve a usar tu clave en lugar de la compartida.
- **Voz del chat:** un valor dañado de volumen o velocidad ya no rompe el panel del chat; se usa el valor por defecto de 100.
- **Widget de reloj:** se reconecta solo si MiniKick se reinicia o se corta la conexión, y recupera si debía estar visible u oculto, sin tener que refrescar la fuente en OBS.
- **Contador de muertes y marcador:** una actualización que coincide con la reconexión de un widget ya no puede cortar su conexión.
- **Videos en overlays:** los reproductores que piden el final de un archivo de video, algo necesario en algunos MP4, reciben ahora el fragmento correcto.

> [!NOTE]
> Los nuevos registros de diagnóstico no cambian cómo se procesa un canje ni cómo se reproduce la recompensa. Si una recompensa no se activa o aparece sin sonido, adjunta el archivo de registro al reportar el problema.

> [!IMPORTANT]
> Si tu alerta HTML personalizada carga archivos que no son web, por ejemplo documentos de texto, dejará de poder pedirlos tras actualizar. Conviértelos a JSON o inclúyelos dentro de la propia página.

> [!IMPORTANT]
> Los cambios en overlays se comprobaron con pruebas automáticas y simulaciones del servidor local, pero no con una instancia real de OBS. Tras actualizar, conviene probar el combo de emotes, una alerta HTML propia y el reloj en tu escena.
