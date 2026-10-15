# Notas de la Versión — MiniKick v1.6.4

Fecha de Publicación: 15 de octubre de 2026

La versión 1.6.4 mejora el control del chat durante la transmisión, facilita consultar el volumen de la música y refuerza la compatibilidad de las alertas de Twitch y la síntesis de voz. También corrige respuestas del comando de solicitud de canciones y el regreso del chat a la vista principal.

---

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Chat | Ventana independiente para el chat | Permite desacoplar el historial del chat en una ventana redimensionable y devolverlo a la vista principal. Al minimizar o cerrar la ventana, el chat regresa automáticamente y conserva su espacio original. | Puedes mantener el chat visible mientras usas otras aplicaciones y volver a la distribución habitual sin perder el historial ni las conexiones activas. |
| Music | Consulta del volumen desde el chat | El comando `!vol` sin número muestra el volumen actual; `!vol 0-100` mantiene el ajuste del nivel. | Tú y tu comunidad pueden comprobar el nivel de música directamente desde el chat antes de cambiarlo. |

## Mejoras

* **Compatibilidad de síntesis de voz:** se actualizó el soporte de Edge TTS para adaptarse al protocolo actual de Microsoft Edge Read Aloud. Esto reduce los errores al iniciar la síntesis de voz.

* **Sincronización del volumen de música:** el valor mostrado por la interfaz y el consultado con `!vol` se mantiene alineado con el volumen usado por el reproductor, incluso al iniciar la aplicación o cambiar el nivel desde el chat.

* **Permisos para alertas de Twitch:** se añadieron los permisos necesarios para recibir alertas de suscripciones y Cheers. Para activar estos eventos, vuelve a autorizar Twitch desde MiniKick y acepta los permisos solicitados.

## Correcciones

* **Registro de eventos de Twitch:** se corrigió el rechazo de Twitch al crear las suscripciones EventSub de suscripciones y Cheers cuando la autorización no incluía los permisos necesarios. Tras renovar la autorización, esos eventos pueden registrarse correctamente.

* **Respuesta al rechazar canciones:** cuando una solicitud `!sr` supera la duración máxima configurada, el mensaje de rechazo vuelve a incluir el nombre de quien la solicitó.

* **Distribución del chat al volver a acoplarlo:** se corrigió el tamaño del panel al devolverlo a la vista principal, para que recupere su proporción original y no reduzca el espacio de los demás controles.

* **Chat minimizado:** se corrigió el estado en que el historial podía quedarse dentro de una ventana minimizada. Ahora vuelve a la vista principal al minimizar la ventana flotante.
