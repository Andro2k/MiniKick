# Notas de la Versión — MiniKick v1.6.8

Fecha de Publicación: 15 de noviembre de 2026

MiniKick 1.6.8 incorpora nuevas herramientas para conectar los eventos del stream con otros servicios y organizar la música, además de una vista previa de video para las canciones. La interfaz se adapta mejor a ventanas estrechas, las traducciones presentan plurales correctos y se corrigen problemas que podían bloquear Recompensas, impedir el cierre durante un inicio de sesión o afectar las actualizaciones.

---

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Developer | Envío de eventos a servicios externos | Configura destinos para enviar eventos del stream a Discord u otros servicios compatibles mediante webhooks. Puedes elegir eventos y plataformas, enviar un ping de prueba y, para destinos genéricos, habilitar la firma de los mensajes. | Conecta MiniKick con automatizaciones y servicios externos, y comprueba el destino desde la propia aplicación. |
| Music | Historial de canciones | Consulta las canciones reproducidas o retiradas recientemente de la cola y vuelve a agregarlas con una acción. | Recupera canciones sin tener que buscarlas de nuevo. |
| Music | Playlists | Crea playlists, agrega canciones desde el reproductor o el historial, quita canciones y agrega una playlist a la cola. | Organiza canciones y prepara la cola desde MiniKick. |
| Music | Vista previa de video | Abre desde el historial una vista previa sin audio. Si hay un video compatible en la caché, se reproduce localmente; de lo contrario, MiniKick intenta mostrarlo desde YouTube. | Identifica visualmente la canción mientras el audio continúa en el reproductor de MiniKick. |
| Rewards | Recarga de miniaturas | Solicita regenerar las miniaturas de archivos de recompensas y actualiza la tabla al terminar. | Refresca las imágenes después de mover o restaurar archivos. |

## Mejoras

- **Música:** la pestaña del reproductor ocupa menos espacio inicialmente, la vista previa utiliza colores coherentes con el tema y los controles del historial y las playlists mantienen acciones claras. El video local evita cargar una página web cuando el archivo en caché es compatible.
- **Diseño adaptable:** la ventana tiene un tamaño mínimo definido, el menú lateral se ajusta al ancho disponible y las vistas reorganizan su contenido. Las tablas de Comandos y Recompensas evitan el desplazamiento horizontal en ventanas estrechas.
- **Traducciones:** los mensajes ahora utilizan traducciones Fluent en español e inglés, con plurales según la cantidad y respaldo al inglés cuando falta una traducción.
- **Presentación:** los iconos de la aplicación se unifican con el estilo Lucide y se corrigen tamaños, alineación y algunos controles visuales.
- **Instalación y actualizaciones:** las instalaciones silenciosas gestionan mejor la reapertura de MiniKick y el acceso directo del escritorio; las versiones se comparan por sus componentes numéricos y el instalador puede dejar un registro de instalación.
- **Organización interna:** se estandarizan nombres y ubicación de módulos y se amplían las comprobaciones automáticas para mantener esa estructura. Estos cambios no alteran los flujos de uso de la aplicación.

## Correcciones

- La recarga de miniaturas de Recompensas se ejecuta en segundo plano y ya no debe dejar la interfaz bloqueada mientras procesa varios archivos. También se corrige la detección de miniaturas faltantes y se evita repetir capturas en cada lectura.
- Se corrige un caso en que la comparación de versiones podía dejar de detectar una actualización al alcanzar números de versión de dos dígitos, como 1.6.10.
- Cerrar MiniKick durante un inicio de sesión pendiente ya no obliga a esperar hasta que expire el tiempo máximo del proceso de autenticación.
- Las tablas de Comandos y Recompensas caben mejor en ventanas estrechas, sin cortar su contenido ni mostrar desplazamiento horizontal innecesario.
- Se corrigen rutas del instalador y el tamaño del diálogo de actualización para evitar contenido cortado o superpuesto.
- Se actualiza el icono de la aplicación utilizado por el ejecutable y el instalador.
- Se corrigen detalles de estado y validación en la configuración de webhooks y en la creación de playlists.

> [!NOTE]
> La generación de tokens para ciertos streams de YouTube está implementada para mejorar la resolución de música, pero su funcionamiento con el motor web y las pistas afectadas aún requiere validación en Windows.

> [!IMPORTANT]
> La compilación real del instalador y la actualización silenciosa, así como la comprobación visual de algunas funciones en Windows, quedaron pendientes en las verificaciones documentadas para esta versión.
