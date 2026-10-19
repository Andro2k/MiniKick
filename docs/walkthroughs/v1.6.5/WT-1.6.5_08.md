# Walkthrough Técnico — MiniKick v1.6.5 (Paso 08)

Revisión de contraste y estados de teclado en el tema oscuro global, guiada por los principios de legibilidad, consistencia y visibilidad del estado del sistema.

---

## Novedades

- No se agregaron componentes ni flujos nuevos.

## Mejoras

- Los títulos secundarios de navegación y las etiquetas de apoyo usan un tono con contraste superior sobre los fondos oscuros. Se mantienen los tonos atenuados existentes para controles deshabilitados.
- Los botones de acción principal usan verdes más oscuros para conservar texto claro legible en los estados normal, hover y presionado.
- Los bordes de foco usan un verde visible y coherente entre los principales controles interactivos.

- Se unificó la geometría visual de los botones y se retiraron sus gradientes, biseles y contornos decorativos; los estados conservan cambios simples de superficie y foco.
- Se centralizaron los colores fijos de los mockups Qt de chat, alertas y música, así como los tonos de acento translúcidos de diálogos y controles.
- Los tokens de navegación y texto agregados en Fase 1 ahora se consumen desde las reglas QSS correspondientes.

## Correcciones

- Se retiró la regla QSS global que suprimía los indicadores nativos de foco y se eliminó la supresión específica de botones. Los botones conservan además un borde de foco explícito.

- Se completaron las exportaciones publicas de tokens de color que faltaban, evitando un `ImportError` al iniciar la aplicacion.

- Se fijo en 32 x 32 px el boton de accion del buscador y el boton para explorar el navegador, como otros controles de icono.
