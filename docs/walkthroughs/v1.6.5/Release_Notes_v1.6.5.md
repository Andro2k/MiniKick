# Notas de la Versión — MiniKick v1.6.5

Fecha de Publicación: 16 de octubre de 2026

La versión 1.6.5 renueva el overlay de música con dos diseños inspirados en reproductores clásicos y vinilos. Ambos aprovechan los datos de la canción y adaptan sus colores a la portada para integrarse mejor con la música que suena en la transmisión.

---

## Novedades

| Sección | Característica | Descripción | Beneficio para el Usuario |
|---|---|---|---|
| Music | Diseños Classic y Vinyl para el overlay | Elige entre un reproductor clásico con portada y detalles de la canción, o un diseño de vinilo con la portada en el centro del disco. Ambos muestran el título, artista y avance de reproducción. | Puedes adaptar la fuente de música de OBS al estilo de tu transmisión y mantener visible la información de la canción. |

## Mejoras

* **Colores que acompañan la portada:** los acentos y fondos de los dos diseños toman como referencia los colores de la portada actual, haciendo que el overlay se integre visualmente con cada canción.

* **Vista previa y tamaños recomendados:** la configuración presenta los dos modelos disponibles y sus dimensiones sugeridas para agregarlos a OBS.

* **Ajuste al tamaño de la fuente:** la portada, el disco y el brazo reducen su tamaño para ajustarse a la ventana de OBS. Los títulos y nombres largos se acortan con puntos para evitar que invadan el diseño; el reproductor Classic aprovecha ese espacio sin la fila de controles decorativos.

* **Mejor legibilidad del tema oscuro:** las etiquetas secundarias y los estados de foco destacan mejor sobre los fondos oscuros, y el texto de los botones principales conserva una lectura más clara al interactuar.

* **Botones más simples:** las acciones tienen superficies planas y estados más claros al pasar el cursor o presionarlas, con colores y textos más legibles.

## Correcciones

* **Diseños no reconocidos en la URL del overlay:** si una URL contiene un modelo que ya no está disponible, el reproductor abre con el diseño Classic para mantener visible la música.

* **Recorte del diseño Vinyl:** el disco y el brazo ahora reducen su tamaño en fuentes de OBS pequeñas, y los metadatos extensos se recortan con puntos para conservar la distribución.
