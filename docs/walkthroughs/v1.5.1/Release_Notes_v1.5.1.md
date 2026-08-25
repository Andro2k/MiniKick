# Release Notes - MiniKick Version 1.5.1

**17 de Agosto, 2026**

## Navegación por Teclado Accesible, Enfoque Visual en Controles y Optimización de Rendimiento

> [!NOTE]
> **¿Por qué una actualización inmediata tras la v1.5.0?**
> Tras el gran lanzamiento de la versión 1.5.0 con soporte multi-plataforma y nuevos overlays, detectamos oportunidades cruciales para mejorar la accesibilidad y la agilidad de la aplicación: la navegación rápida con la tecla **Tab** carecía de indicadores de foco claros en botones e interruptores, y el visor de novedades requería una optimización interna de rendimiento. En lugar de posponer estas mejoras para una versión lejana, decidimos publicar la **v1.5.1** de manera ágil para ofrecerte una experiencia de usuario completamente pulida, fluida y accesible desde el primer momento.

---

### Novedades

- **Navegación Integral por Teclado (Tab Focus):** Ahora puedes recorrer toda la interfaz de MiniKick utilizando exclusivamente la tecla **Tab** y **Shift+Tab**. Todos los botones, selectores de plataforma, chips de filtrado, casillas de verificación y pestañas cuentan con un halo de enfoque visual nítido y de alto contraste.
- **Control por Teclado en Interruptores (ModernSwitch):** Los switches personalizados ahora reciben foco por teclado y permiten alternar su estado instantáneamente presionando las teclas **Espacio** o **Enter/Return**, mostrando bordes de resaltado verdes o blancos según su activación.

---

### Mejoras

- **Visor de Novedades Ultrarrápido:** El motor interno de lectura y formateo de Markdown para las notas de versión fue optimizado con precompilación de patrones y almacenamiento en caché ($\mathcal{O}(1)$), logrando que la apertura de la ventana de novedades sea instantánea.
- **Generación de Estilos con Memoización:** La hoja de estilos global de la aplicación (`QSS`) ahora se almacena en memoria caché de acceso directo, optimizando los recursos del sistema al cambiar tamaños de fuente o redimensionar ventanas.
- **Protección y Cierre Seguro de Hilos:** Se reforzó el ciclo de vida de los procesos en segundo plano para garantizar que las consultas de red se cancelen limpiamente al cerrar ventanas modales, evitando consumos innecesarios en segundo plano.
- **Compatibilidad Absoluta de Recursos en Windows:** Estandarización automática en las rutas de iconos vectoriales SVG para asegurar una visualización perfecta en cualquier entorno del sistema operativo.

---

### Correcciones

- **Eliminación de Foco Invisible:** Se corrigió el comportamiento donde el foco del teclado se perdía o quedaba oculto al alternar entre múltiples botones o controles de configuración.
- **Limpieza de Reglas de Estilo:** Eliminación de propiedades redundantes e incompatibles en el motor de estilos de Qt, garantizando un renderizado visual más limpio y consistente.

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.1 es una actualización incremental totalmente compatible. Todas tus configuraciones, comandos, directos programados y conexiones de Kick y Twitch permanecen intactos.
