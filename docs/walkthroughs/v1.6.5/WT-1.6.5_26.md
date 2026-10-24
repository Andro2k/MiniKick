# Walkthrough Técnico — MiniKick v1.6.5 (Paso 26)

Se optimizó el enrutamiento de mensajes entrantes y se refactorizó la coordinación de la ventana principal. La creación de vistas, la deduplicación de recompensas y el ciclo de parada de workers se separaron en componentes especializados, manteniendo las dependencias del contenedor central y el bucle de eventos de Qt.

---

## Novedades

- Se incorporó un coordinador para solicitar la parada de varios workers y supervisar su finalización de forma asíncrona mediante un temporizador de Qt.
- Se extrajo una factoría que crea las vistas de navegación de forma diferida y las conecta con sus controladores.
- Se añadió una caché acotada de deduplicación de recompensas que combina una cola y un conjunto para recordar eventos recientes y consultar duplicados en tiempo constante.
- Se incorporó una señal para notificar cuándo terminó la limpieza de la ventana y permitir que las pruebas esperen el cierre completo.

## Mejoras

- El cierre ya no espera secuencialmente a cada hilo desde la interfaz. Se solicitan las paradas primero y se supervisan sin bloquear el hilo gráfico.
- Los servicios del contenedor y la base de datos se cierran después de que hayan terminado los workers, reduciendo el riesgo de que un hilo utilice recursos ya cerrados.
- Las sustituciones y desconexiones de workers de Kick, Twitch, YouTube y TikTok continúan al finalizar su parada, evitando esperas bloqueantes y evitando iniciar workers obsoletos si el usuario cambia de operación o cierra la aplicación.
- Se mantienen bajo demanda las vistas secundarias y se eliminó el precalentamiento que las creaba todas tras el inicio. La consulta inicial de métricas se difirió al siguiente ciclo del bucle de eventos.
- Se dividió la hidratación final de ajustes en pasos de autoinicio por plataforma, con registro explícito de errores por fase.
- En la ruta de recepción de mensajes, se conserva el timestamp existente y solo se consulta el reloj cuando el mensaje necesita uno nuevo.
- La comprobación de duplicados de recompensas pasó de una búsqueda lineal en la cola a una búsqueda O(1), conservando el límite de memoria.
- Se retiraron claves de traducción de estados de espera y terminación forzada que dejaron de usarse con el nuevo apagado cooperativo, conservando la paridad de los archivos de idioma y los valores predeterminados.

## Correcciones

- Se evita cerrar los servicios del contenedor mientras todavía pueden ser utilizados por workers activos.
- Se previene que las finalizaciones asíncronas creen conexiones o workers después de una desconexión, una reconexión más reciente o el cierre de la ventana.
- Los errores en callbacks de finalización y tareas de limpieza quedan registrados en lugar de descartarse silenciosamente.
- Se ajustaron las pruebas de ciclo de vida para esperar la finalización asíncrona de la ventana antes de destruir los widgets Qt.

## Validación

- La suite de calidad rápida aprobó las 12 auditorías.
- La regresión automatizada aprobó 261 pruebas. Se excluyó una prueba de tema que falla por una expectativa previa de QSS para ComboBox, no relacionada con estos cambios.
- Las pruebas específicas cubren la deduplicación acotada, la creación única de vistas, la parada no bloqueante de un worker, el inicio de conexiones en vivo y la limpieza de la ventana.
- Los módulos Python modificados compilaron correctamente y `git diff --check` no encontró errores de formato.
