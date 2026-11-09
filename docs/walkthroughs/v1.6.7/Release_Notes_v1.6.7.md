# Notas de la Versión — MiniKick v1.6.7

Fecha de Publicación: 9 de noviembre de 2026

MiniKick 1.6.7 mejora la experiencia del chat y la lectura de voz, conserva mejor tu espacio de trabajo y evita una ventana fugaz durante el inicio. También incorpora diagnósticos más útiles para investigar retrasos de mensajes y conexiones, y presenta las notas de versión de GitHub con un formato más completo.

---

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Settings | Notas de versión más completas | Las notas obtenidas desde GitHub conservan el idioma original e incluyen mejor formato para tablas, listas, enlaces y bloques de código. | Puedes consultar los cambios publicados con su presentación original y sin traducciones automáticas del contenido. |
| Chat | Diagnóstico de retrasos | MiniKick registra mediciones de los tramos entre la llegada de un mensaje y su procesamiento, junto con información de la conexión. | Facilita distinguir si una demora se relaciona con la conexión o con el procesamiento de la aplicación. |
| Chat | Búsqueda de GIF sin pausa en la interfaz | Las búsquedas de GIF se realizan en segundo plano mientras las direcciones directas siguen funcionando como antes. | Puedes seguir usando el chat mientras se obtiene el resultado. |
| Chat | Lectura de voz más clara | La voz omite emojis, reconoce abreviaturas frecuentes y prepara mejor los nombres de usuario para su lectura. | Los mensajes y nombres suenan más naturales y se evitan pausas causadas por la lectura literal de símbolos. |
| Chat | Pausa entre mensajes de voz | Se incorpora una breve separación entre mensajes consecutivos leídos en voz alta. | Es más fácil distinguir dónde termina un mensaje y comienza el siguiente. |
| Chat | Ventana flotante que recuerda su posición | La ventana desacoplada conserva su ubicación y tamaño al volver a abrirla, además de mantenerlos al acoplar y desacoplar durante la sesión. | Recuperas la distribución de pantalla que prefieres sin tener que acomodar la ventana cada vez. |

## Mejoras

- **Chat de Kick:** se amplían las mediciones de conexión y de procesamiento para ayudar a identificar el origen de los retrasos. Las búsquedas de GIF ya no bloquean la interfaz, y las comprobaciones de conexión detectan antes algunas conexiones inactivas.
- **Conexiones más estables:** se ajusta la recuperación del tiempo de espera de reconexión y una respuesta lenta a una comprobación de diagnóstico ya no debe cerrar por sí sola el chat activo.
- **Registro de actividad:** los mensajes de diagnóstico mantienen un idioma consistente y el registro en disco evita escrituras innecesariamente frecuentes.
- **Lectura de voz:** la limpieza de símbolos, la preparación de nombres y las pronunciaciones comunes se aplican de forma coherente a los mensajes, nombres y otros textos enviados a la voz.
- **Presentación:** los iconos y badges se muestran con bordes más nítidos y tamaños adecuados; las notas de versión se adaptan mejor al tema de MiniKick.
- **Inicio más ordenado:** la etiqueta de versión de la barra lateral permanece dentro de la ventana principal desde su creación, y la pantalla de inicio ya no viene acompañada por una pequeña ventana vacía.
- **Consistencia visual:** se eliminaron duplicaciones internas de valores de tema sin cambiar los colores, medidas ni estilos resultantes.

## Correcciones

- Se evita que una etiqueta de la barra lateral aparezca fugazmente como una ventana independiente durante el inicio.
- La voz ya no pronuncia los nombres de los emojis y evita deletrear nombres de usuario por tener símbolos decorativos o números largos.
- Se corrigen pronunciaciones poco naturales de abreviaturas comunes del chat y términos habituales de streaming.
- Una búsqueda de GIF lenta ya no detiene temporalmente el procesamiento de la interfaz.
- Se corrige el caso en que el tiempo de espera para reconectar podía permanecer elevado tras varias desconexiones.
- Las respuestas lentas de diagnóstico ya no se confunden con una conexión inactiva que deba cerrarse.
- La ventana flotante del chat conserva su posición y tamaño al volver a acoplarla y desacoplarla, y también entre ejecuciones.
- Se corrige el recorte de algunos iconos y los bordes irregulares de badges en diálogos.

> [!NOTE]
> Las mediciones de latencia ayudan a investigar los retrasos, pero no determinan por sí solas si su origen está en la plataforma, la red o el equipo.

> [!IMPORTANT]
> Las pronunciaciones se contrastaron con el fonemizador de voz; no se evaluó auditivamente el audio generado. Las mediciones de conexión tampoco se validaron durante una transmisión en vivo.
