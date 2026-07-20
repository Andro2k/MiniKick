# Release Notes | MiniKick v1.4.2
*Autocompletado de Variables, Ayuda Interactiva Regex, Temas Premium de Música con Barra de Progreso, Iconos de Alta Resolución (High DPI) y Mejoras de Rendimiento*

En esta versión (v1.4.2), MiniKick da un gran salto en usabilidad y rendimiento. Hemos introducido un novedoso sistema de autocompletado y borrado rápido de variables de chat, así como un asistente interactivo para la creación de expresiones regulares (Regex) con resaltado de sintaxis, ideal para moderadores avanzados. La sección de música se renueva completamente con la inclusión de barra de progreso predictiva, carátulas de álbumes y 5 impresionantes variantes visuales (destacando los temas Cyberpunk y Premium Card). Finalmente, corregimos los iconos borrosos en pantallas con escalado de Windows, eliminamos fugas de memoria y optimizamos la base de datos para una velocidad de carga instantánea.

---

## 1. Asistente de Variables y Autocompletado Inteligente
Simplificamos la configuración de respuestas automáticas en el chat para evitar errores de escritura al ingresar variables:
* **Sugerencia de Variables con `{`**: Al escribir una llave `{` en los campos de respuesta de comandos o temporizadores, aparecerá un menú flotante para autocompletar variables como `{user}`, `{touser}` y `{random}` de forma interactiva usando las flechas de tu teclado.
* **Eliminación Inteligente en Bloque**: Si borras con `Backspace` o `Delete` al final o al inicio de una variable (como `{user}`), el sistema eliminará el tag completo de un solo golpe, evitando tener que borrar letra por letra.

> [!IMPORTANT]
> La eliminación en bloque y el menú de sugerencias dinámicas reducen a cero las equivocaciones tipográficas al configurar el bot y agilizan significativamente la personalización del chat.

---

## 2. Asistente Interactivo y Resaltado Regex
Agregamos facilidades visuales para crear reglas de moderación avanzadas mediante expresiones regulares (Regex):
* **Autocompletado de Expresiones comunes**: Al escribir una barra inclinada `\` en la configuración avanzada de comandos, se desplegará una lista interactiva con descripciones breves de expresiones comunes (como dígitos, letras o caracteres especiales) para guiarte en su construcción.
* **Coloreado Inteligente**: Los tokens Regex se pintan de color **ámbar en negrita** para destacar de manera óptima sobre el tema oscuro del programa y facilitar la revisión del patrón.
* **Interfaz de Comandos más Compacta**: Al integrar la ayuda interactiva directamente en el editor, eliminamos el panel estático lateral derecho de instrucciones, logrando reducir el ancho del formulario de comandos a un tamaño compacto de `520px`.

---

## 3. Reproductor de Música Premium, Barra de Progreso y Overlays
Renovamos los widgets para overlays de OBS con diseños modernos y soporte para visualización completa de pistas:
* **Información Enriquecida de Canción**: Los reproductores de música para Spotify y YouTube ahora extraen y muestran de forma interactiva la carátula del álbum de la canción, el tiempo actual, la duración total y la barra de progreso en vivo.
* **Barra de Progreso Predictiva**: La barra de progreso de los widgets en pantalla se desplaza de manera predictiva y fluida segundo a segundo, disminuyendo la carga de llamadas continuas al procesador de tu computadora.
* **Temas Premium y Cyberpunk**: Añadimos 5 variantes visuales seleccionables desde los ajustes de música (Glass, Minimal, Neon, Cyberpunk y Premium Card) para personalizar la apariencia de la música en tus transmisiones.
* **Servidor Local sin Conflictos**: Corregimos un error en el servidor interno de overlays que bloqueaba la carga de hojas de estilo (.css) en el navegador de OBS (retornando errores 403), garantizando fondos transparentes perfectos.

> [!TIP]
> Al copiar el enlace de tu widget de música desde el panel, el sistema adjuntará de forma automática el parámetro del tema seleccionado (ej: `theme=cyber`) listo para pegar como fuente de navegador en tu OBS.

---

## 4. Mejoras de Rendimiento en Capa de Datos
Optimizamos los tiempos de respuesta y redujimos el consumo de disco de los procesos en segundo plano:
* **Acceso Directo a Base de Datos**: Al editar o eliminar un comando o temporizador, la aplicación ahora accede de manera directa a ese elemento en base de datos en $O(1)$ sin necesidad de recargar la colección completa a la memoria RAM de tu computadora.
* **Carga Veloz en Registros de Logs**: Mejoramos el sistema de guardado de registros. Al agrupar varias líneas en tiempo real, el bot usa punteros de clave primaria, acelerando el guardado a disco y evitando las subconsultas lentas de base de datos.
* **Desacoplamiento Interno**: Aislamos la lógica de actualización en segundo plano del diseño gráfico de la ventana, garantizando que los diálogos e interfaces no sufran pequeños congelamientos de pantalla.

---

## 5. Soporte High DPI e Iconos Nítidos
* **Iconos Vectoriales en Alta Resolución**: Corregimos el problema de iconos borrosos en sistemas con pantallas escaladas en Windows (ej. 125%, 150%). Los iconos ahora se dibujan vectorialmente desde sus archivos SVG originales en lugar de estirar imágenes pre-rasterizadas, asegurando que se vean nítidos en todo tipo de pantallas.

---

## 6. Filtrado Inteligente de Logs por Rango
* **Filtros por Rango Relativos**: Simplificamos el selector de filtros de fecha en los logs del desarrollador. En lugar de un selector manual de calendario, ahora puedes filtrar los registros fácilmente desde un dropdown: "Todo el tiempo", "Últimas 24 horas", "Últimos 3 días" y "Últimos 7 días".

---

## 7. Corrección de Fugas de Memoria y Estabilidad (Robustez)
* **Protección de Memoria RAM (Auto-mod)**: Limitamos el historial del filtro anti-spam a un máximo de 1,000 usuarios activos en memoria en cola FIFO, asegurando que la aplicación no consuma memoria excesiva en directos de larga duración.
* **Cierre Limpio del Programa**: Reemplazamos las esperas asíncronas de base de datos en los trabajadores de recompensas para suspenderse de manera segura, logrando que el programa se cierre al instante de forma limpia sin dejar subprocesos colgados en segundo plano.
* **Liberación de Memoria en Logs**: Corregimos una fuga de memoria en la visualización de logs de modo que los elementos de texto descartados se eliminen formalmente de la memoria al cambiar de página o limpiar registros.
* **Migración Automática Silenciosa**: Implementamos una migración interna de base de datos que adapta la estructura anterior a la nueva al iniciar la aplicación sin pérdida de datos locales.

> [!CAUTION]
> No requieres reinstalar el programa ni borrar tu base de datos antigua; MiniKick se encarga de actualizar y migrar todas tus tablas de forma automática sin interrumpir tus comandos y temporizadores.
