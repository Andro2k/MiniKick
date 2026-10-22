# Walkthrough Técnico — MiniKick v1.6.5 (Paso 22)

Se ajustó la bienvenida del Dashboard para mostrar el canal activo y el reparto de mensajes junto con las opciones de conexión a plataformas.

---

## Novedades

- Se agregó un anillo segmentado que muestra la distribución de mensajes de Kick, Twitch, YouTube y TikTok alrededor del avatar del canal activo.
- Las tarjetas de conexión muestran el icono de cada plataforma y su proporción de mensajes.
- Se movió la fecha de creación, seguidores, categoría, identificador, horario y tipo de emisor a badges bajo la descripción.
- El canal Kick muestra una insignia con corona cuando la cuenta es afiliada.
- Se añadió un botón flotante sobre el avatar para alternar entre Kick y Twitch; solo aparece con ambas cuentas conectadas.

## Mejoras

- El nombre y la descripción del canal aparecen debajo del avatar en la bienvenida.
- Se retiró la tarjeta de perfil duplicada y se conservó el acceso para abrir el canal.
- Las tarjetas se organizan en dos columnas y pasan a una columna cuando el espacio disponible es reducido.
- La distribución se calcula en una pasada sobre las cuatro plataformas, con complejidad O(p), donde p es el número fijo de plataformas.
- Se retiró el checklist de configuración anterior y se reutilizaron las tarjetas de conexión existentes.
- Se actualizaron las traducciones de español e inglés para las etiquetas nuevas.

## Correcciones

- Al desconectar o cambiar el perfil activo, la bienvenida limpia el avatar y restablece la información del canal para evitar mostrar datos anteriores.
- Las actualizaciones del estado de conexión ya no reemplazan el porcentaje de mensajes mostrado en las tarjetas.
- La información y el badge de afiliado se actualizan al cambiar entre Kick y Twitch.

## Validación

- Se verificaron sintaxis, traducciones y auditoría estática del proyecto.
- La vista en ejecución no se validó visualmente en este entorno porque PySide6 no está disponible.
