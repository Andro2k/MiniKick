# Release Notes - MiniKick Version 1.5.2

**19 de Agosto, 2026**

## Arquitectura Modular de Frontend, Sistema de Tokens de Diseño y Optimización de Rendimiento

> [!NOTE]
> MiniKick v1.5.2 consolida la estabilidad y elegancia de la aplicación mediante una reestructuración modular completa del frontend, un sistema centralizado de tokens de diseño, optimizaciones de rendimiento en tiempo de ejecución sin operaciones de disco innecesarias, autocompletado asíncrono de categorías en temporizadores y cumplimiento estricto de internacionalización sin textos embebidos.

---

### Novedades (6)

- **Buscador Asíncrono de Categorías en Temporizadores:** Integración de barra de búsqueda unificada y menú emergente de sugerencias para autocompletar categorías de Kick y Twitch directamente en el configurador de temporizadores sin congelar la interfaz.
- **Paquete Modular `frontend.common`:** Desacoplamiento de utilidades en módulos especializados por dominio (`paths.py`, `icons.py`, `validators.py`), eliminando dependencias circulares y facilitando importaciones limpias.
- **Sistema Centralizado de Tokens de Diseño:** Implementación de constantes semánticas para radios de borde (`RADIUS_2XS` a `RADIUS_PILL`), espaciados (`PADDING_INPUT`, `PADDING_SPINBOX`, `PADDING_BADGE`, etc.) y bordes reutilizables en todo el tema visual.
- **Helper Modular de Insignias (`create_badge`):** Componente unificado para generar etiquetas estilizadas de roles, plataformas, tipos y estados en una sola línea de código estandarizada.
- **Contador Automático en Tarjetas de Tabla:** Incorporación del método `set_title_count` en las tarjetas modernas para actualizar dinámicamente el título y conteo de registros sin comprobaciones manuales repetitivas.
- **Configuración Declarativa en Comandos de Música:** Estructura basada en tabla de configuración para generar interruptores de comandos musicales en una sola pasada con acceso inmediato en memoria.

---

### Mejoras (8)

- **Control Preciso en Temporizadores:** Sustitución de los controles deslizantes redundantes por selectores numéricos directos con sufijos descriptivos (`min`, `líneas`) para una configuración más rápida y exacta.
- **Caché Vectorial de Ilustraciones SVG:** Almacenamiento en memoria de renderizadores SVG para permitir redibujados instantáneos durante el cambio de tamaño de ventana sin lecturas continuas de disco.
- **Precompilación de Expresiones Regulares:** Evaluación instantánea en controles de texto dinámicos al detectar variables del sistema (`{user}`, `{touser}`) sin recompilaciones en el hilo principal.
- **Alternancia Inmediata en Controles Segmentados:** Eliminación de iteraciones innecesarias al cambiar de opción en selectores segmentados, delegando el estado visual directamente al gestor de grupos de botones.
- **Optimización de Redimensionamiento en Filtros Anti-Spam:** Incorporación de guardas de estado para ejecutar cambios de disposición y columnas únicamente al cruzar los umbrales de resolución necesarios.
- **Estandarización de Gestión de Tags en Chat:** Unificación de la creación visual de etiquetas para bots y palabras silenciadas bajo una rutina común parametrizada.
- **Jerarquía y Proporción Visual en Diálogo de Instancia:** Ajuste armónico en las dimensiones y márgenes de la ilustración y textos informativos cuando la aplicación ya se encuentra en ejecución.
- **Estandarización de Controles sin Rueda del Ratón:** Reubicación de componentes protegidos contra desplazamiento involuntario dentro del paquete principal de widgets de presentación.

---

### Correcciones (6)

- **Cumplimiento Estricto de Internacionalización en Diálogo de Errores:** Eliminación total de textos embebidos y cadenas de respaldo en código fuente, conectando el 100% de títulos, botones y mensajes al servicio de traducción.
- **Seguridad en Cierre de Reportes de Error:** Bloqueo controlado de hilos secundarios al cerrar la ventana de reporte para evitar excepciones o terminaciones inesperadas.
- **Unificación Arquitectónica de Diálogos Modales:** Migración de ventanas emergentes hacia la estructura estándar `ModernModal` para garantizar sombreados consistentes, bordes redondeados y soporte de arrastre.
- **Eliminación de Código Muerto en Widgets:** Retiro de controles obsoletos y parámetros con cadenas estáticas no traducidas en cabeceras de tablas.
- **Alineación Visual de Encabezados y Botón de Actualizar:** Corrección del centrado vertical y márgenes horizontales en la sección de estado de canales de la pestaña de información del directo.
- **Prevención de Notificaciones Duplicadas en Conexión:** Corrección en la secuencia de eventos de autenticación de Twitch para emitir una única alerta de conexión exitosa cuando el canal está completamente sincronizado.

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.2 reúne todas las optimizaciones, limpiezas de arquitectura y mejoras de interfaz desarrolladas en los documentos de trabajo `WT-1.5.2_01` al `WT-1.5.2_07`. Al actualizar, todas tus configuraciones, credenciales, temporizadores, comandos y datos de sesión se conservan sin modificaciones.
