# Release Notes - MiniKick Version 1.5.0

**17 de Agosto, 2026**

## Soporte Multi-Plataforma Twitch, Overlays Rediseñados y Optimización de Rendimiento

> [!NOTE]
> MiniKick v1.5.0 transforma la experiencia de streaming al incorporar compatibilidad simultánea para Kick y Twitch, un sistema de overlays con 5 identidades visuales únicas, apagado instantáneo de la aplicación, moderación inteligente sin falsos positivos y nuevos controles de interfaz de alta precisión.

---

### Novedades (10)

- **Integración Multi-Plataforma en Vivo:** Conexión simultánea y en tiempo real con Kick y Twitch, permitiendo gestionar el chat, alertas y eventos de ambas plataformas desde un único panel centralizado.
- **Ruteo de Plataforma para Comandos y Moderación:** Posibilidad de configurar comandos de chat, temporizadores automáticos, programación de directos y filtros de spam para que respondan en Kick, en Twitch o en ambas plataformas al mismo tiempo.
- **Overlays con 5 Identidades Visuales Únicas:** Rediseño completo para los overlays de chat y música con personalidades gráficas bien diferenciadas:
  - **Glass:** Acabado de cristal translúcido esmerilado con desenfoque de lujo, reflejos de luz y bordes redondeados orgánicos.
  - **Neon:** Contorno eléctrico vibrante con resplandor continuo que reacciona dinámicamente al color del usuario o rol.
  - **Card:** Ficha estructurada en material oscuro con cápsula destacada para el nombre y relieves elegantes.
  - **Cyber:** Interfaz futurista de videojuego con esquinas biseladas angulares, cuadrícula tecnológica y acentos cian y magenta neón.
  - **Minimal:** Formato de subtítulo flotante no invasivo con degradado suave, ideal para integrarse sobre cualquier videojuego sin estorbar la pantalla.
- **Emoticones Oficiales de Twitch en Overlays:** Los emotes de Twitch ahora se visualizan automáticamente como imágenes en el overlay de chat en lugar de texto plano.
- **Control de Lectura de Voz (TTS) por Roles:** Switches independientes para activar o silenciar la voz en Streamers, Moderadores, VIPs, Suscriptores o Espectadores Generales, con selección de voz personalizada para cada grupo.
- **Gestor Completo de Recompensas de Kick:** Creación, edición de costo, descripción, color de fondo, requisitos de texto, asignación de archivos multimedia y sincronización automática de recompensas de canal directamente con Kick.
- **Previsualización Multimedia en Recompensas:** Miniaturas visuales automáticas para videos, imágenes y audios dentro de la tabla de recompensas, con columnas de posición en pantalla y volumen individual.
- **Control Segmentado Moderno:** Nuevo selector visual interactivo por botones para alternar plataformas y cambiar la orientación, flujo y animaciones del overlay de chat con un solo clic.
- **Nuevo Selector Numérico de Precisión:** Componente numérico compacto protegido contra desplazamientos accidentales de la rueda del ratón y con texto descriptivo especial (como 'Nunca' al desactivar el desvanecimiento).
- **Visor de Novedades Integrado:** Diálogo renovado para consultar las notas de actualización directamente dentro de la aplicación con tipografía nítida y formato de lectura cómodo.

---

### Mejoras (10)

- **Cierre Instantáneo de la Aplicación:** El proceso de salida se completa de inmediato y en segundo plano sin congelamientos de pantalla ni esperas al confirmar la salida.
- **Historial de Chat en Segundo Plano:** Los mensajes recibidos se almacenan de forma continua para que el chat aparezca completo al instante en cuanto abres la pestaña.
- **Caché Inteligente de Canciones:** Las pistas más reproducidas se conservan en el equipo para reproducirse de inmediato sin descargas repetidas ni consumo innecesario de red.
- **Resolución Automática de Categorías:** El programador de directos detecta y asigna automáticamente los nombres de juegos y categorías compatibles tanto en Kick como en Twitch.
- **Indicador Visual al Ordenar Canciones:** Resaltado verde interactivo al arrastrar y soltar canciones en la cola de reproducción para saber con exactitud dónde se insertará la pista.
- **Búsqueda Rápida con Botón de Borrado:** Barra de búsqueda unificada en comandos, temporizadores y registros con botón de limpieza rápida y paginación por bloques.
- **Respuestas de Comandos de Widgets Multi-Plataforma:** Los comandos interactivos de widgets (como conteo de muertes o victorias) responden de forma automática por la plataforma donde fueron solicitados.
- **Identidad Oficial de MiniKick en Windows:** La aplicación y sus alertas en el Centro de Notificaciones de Windows muestran el icono y nombre oficial de MiniKick en lugar de ejecutables genéricos.
- **Controles de Fecha y Calendario Protegidos:** Selectores de fecha y hora diseñados para evitar cambios accidentales por la rueda del ratón, con navegación de calendario en colores claros.
- **Internacionalización Completa:** Todas las nuevas funciones, opciones de plataforma y mensajes del sistema cuentan con traducciones completas en español e inglés.

---

### Correcciones (8)

- **Eliminación de Falsos Positivos en Moderación:** Los filtros anti-spam descuentan emoticones y enlaces antes de evaluar mayúsculas o símbolos, evitando sanciones erróneas a espectadores.
- **Voz TTS Limpia sin Códigos de Emotes:** El sintetizador de voz ignora las etiquetas técnicas de emoticones de Kick y Twitch para leer únicamente el mensaje hablado natural.
- **Lectura Continua de Voz en Windows:** Corrección de pausas en el motor de voz local de Windows, garantizando que todos los mensajes se lean de forma fluida.
- **Prevención de Respuestas Duplicadas del Bot:** Sincronización precisa entre plataformas para evitar que los mensajes automáticos del bot se muestren repetidos en el chat.
- **Reconexión Automática ante Vencimiento de Tokens:** Detección transparente de credenciales expiradas en Twitch con renovación automática sin interrumpir la transmisión ni la sesión del usuario.
- **Eliminación de Recortes en Chat Horizontal:** Corrección de márgenes y bordes en el modo marquesina horizontal para que las marcas de tiempo y nombres nunca se corten.
- **Corrección de Bordes Deformados en Tema Minimal:** Eliminación del efecto de arco o paréntesis en los bordes curvos de los overlays.
- **Preservación de Estado en Filtros de Comandos:** Los interruptores de activación de comandos mantienen su estado exacto al realizar búsquedas o filtrar por categoría.

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.0 reúne todas las mejoras y características desarrolladas en los documentos de trabajo `WT-1.5.0_01` al `WT-1.5.0_14`. Al actualizar, todos tus ajustes, comandos, recompensas y conexiones previas se mantendrán intactos.
