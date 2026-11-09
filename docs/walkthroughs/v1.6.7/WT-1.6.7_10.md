# Walkthrough Técnico — MiniKick v1.6.7 (Paso 10)

Se corrigió la aparición fugaz de una pequeña ventana nativa durante el inicio. La causa era la etiqueta de versión de la barra lateral, que se hacía visible antes de pertenecer a la ventana principal. Se le asignó su contenedor desde la creación y se añadió una prueba que detecta etiquetas mostradas como ventanas independientes. También se amplió la auditoría de ventanas para probar el splash visible y se centralizó el manejo de clics de las tarjetas de severidad y las pestañas de alertas en el widget compartido.

---

## Novedades

- La auditoría runtime incluye el splash visible y busca ventanas top-level inesperadas mientras se muestra.
- La auditoría estática revisa también el código de arranque y advierte expresamente que ese modo no detecta ventanas creadas durante la ejecución.
- Se añadieron pruebas que detectan si una etiqueta se muestra accidentalmente como ventana independiente y verifican el manejo compartido de clics.

## Mejoras

- La etiqueta de versión de la barra lateral recibe su contenedor padre desde su creación, manteniéndose dentro de la ventana principal durante la construcción de la interfaz.
- Las tarjetas de severidad y las pestañas de variantes de alertas reutilizan el manejo común del clic izquierdo y conservan sus señales y datos asociados.
- La auditoría de ventanas informa claramente el alcance de sus comprobaciones: las vistas se prueban de forma aislada y no se inicia la aplicación completa.

## Correcciones

- Se eliminó la microventana fugaz con barra de título y contenido vacío que aparecía junto a la pantalla de inicio.
- Se previene que la etiqueta de versión se convierta temporalmente en una ventana nativa independiente antes de ser incorporada al diseño de la barra lateral.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| Pruebas focalizadas de la barra lateral y widgets clicables | 7 aprobadas |
| Auditoría runtime de ventanas | 12 de 12 escenarios limpios; incluye splash visible y vistas aisladas |
| Suite rápida de auditorías de calidad | 11 de 12 aprobadas; falla Project Translation Keys por la clave `music.youtube.com` ausente en ambos idiomas |

