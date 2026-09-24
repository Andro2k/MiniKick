# Notas de la Versión - MiniKick Versión 1.6.0

24 de Septiembre, 2026

## Resumen de la Versión

> [!NOTE]
> MiniKick v1.6.0 representa una actualización integral centrada en la experiencia visual, la estabilidad de transmisión y la calidad acústica. Esta versión incorpora soporte nativo para animaciones GIF en el chat mediante comandos interactivos y emotes de Twitch, un rediseño completo del overlay de chat con estética moderna tipo mensajería, avatares de usuario y perfiles independientes para transmisiones verticales y horizontales con sincronización en tiempo real. 
> 
> Asimismo, se introduce un catálogo ampliado con más de 30 voces comunitarias para el sistema de lectura por voz (TTS), mejoras acústicas profesionales con atenuación automática de música y normalización de volumen, protecciones avanzadas contra textos repetitivos en el chat, arranque automático con el sistema operativo, y la total resolución de incompatibilidades visuales con el modo claro de Windows.

---

## Novedades

### Interacción y Chat en Pantalla

| Característica | Descripción | Beneficio para el Usuario |
|---|---|---|
| Integración de GIFs con Giphy | Comando interactivo (!gif) en el chat de Kick y Twitch para proyectar imágenes animadas en directo. | Mayor dinamismo y participación visual de los espectadores en la transmisión. |
| Soporte Nativo de Emotes Animados de Twitch | Detección directa de animaciones y emotes en los mensajes de Twitch que se muestran visualmente en lugar de código de texto. | Representación fiel y fluida de las expresiones del chat en pantalla. |
| Diseño Moderno tipo Mensajería | Nuevo estilo de burbujas de chat con avatares circulares e insignia de la plataforma (Kick o Twitch) integrada. | Aspecto profesional, limpio y fácilmente identificable en la pantalla de OBS. |
| Tres Temas Visuales para el Chat | Selector de estilos con temas Oscuro, Claro con efecto de cristal esmerilado y Minimalista. | Adaptación estética inmediata a cualquier fondo o videojuego en transmisión. |
| Perfiles Duales (Vertical y Horizontal) | Ajustes totalmente separados de tamaño, tipografía y disposición para formatos tradicionales y formatos móviles (TikTok, Shorts). | Libertad para emitir en múltiples plataformas sin tener que reconfigurar el chat cada vez. |
| Sincronización en Vivo | Cualquier cambio en los paneles de control se refleja al instante en el visor de OBS sin necesidad de recargar la página. | Configuración inmediata y segura sin interrumpir la emisión en directo. |

> [!TIP]
> Puedes alternar entre los perfiles Vertical y Horizontal en cualquier momento desde el panel de ajustes del chat. Las dimensiones, márgenes y alineaciones se guardan por separado para cada perfil, facilitando el streaming simultáneo en Twitch/Kick y TikTok sin desconfigurar tus escenas de OBS.

### Audio y Síntesis de Voz (TTS)

- Nuevo Asistente de Voces Piper TTS: Ventana renovada con acceso directo a más de 30 voces comunitarias de alta calidad en múltiples idiomas y variantes de español, con descarga integrada en un clic y prueba auditiva previa.
- Control de Velocidad y Volumen por Voz: Ajuste independiente de la cadencia de lectura y potencia acústica para adaptar cada voz al estilo del canal.
- Atenuación Automática de Música: La música en reproducción baja su volumen de forma suave cuando el sintetizador de voz lee un mensaje del chat, restaurando el nivel original al concluir.
- Normalización Inteligente de Picos: Las voces que originalmente tenían bajo volumen se elevan a un nivel uniforme y claro sin generar distorsión ni estruendos.
- Curva de Volumen Natural: La barra de volumen de la música ahora responde a una escala acústica que refleja cómo escucha el oído humano, facilitando ajustes precisos en volúmenes suaves.

> [!IMPORTANT]
> El nuevo filtro anti-spam para la síntesis de voz colapsa de forma automática los textos que contienen caracteres o palabras repetitivas y suprime URLs de páginas o GIFs, protegiendo tu transmisión en directo de interrupciones ruidosas o bloqueos de audio.

### Control y Sistema

- Inicio Automático con Windows: Opción configurable en los ajustes para que MiniKick se inicie automáticamente al encender la computadora, arrancando en segundo plano listo para emitir.
- Control Rápido desde la Bandeja del Sistema: Menú contextual en el icono junto al reloj de Windows para pausar, reanudar o cambiar canciones y verificar el estado de las conexiones.
- Diálogos de Confirmación de Borrado: Ventanas de confirmación previas al eliminar comandos, temporizadores, recompensas de canal o voces instaladas, previniendo pérdidas accidentales de datos.
- Conexión Asíncrona Fluida: Enlace simultáneo con Kick y Twitch en segundo plano que mantiene la interfaz rápida y responsiva sin pausas al conectar.

> [!TIP]
> Al habilitar el inicio automático con Windows en los Ajustes del Sistema, MiniKick puede arrancar minimizado directamente en la bandeja del sistema, manteniendo tus comandos, música y overlays activos desde el primer segundo.

---

## Mejoras

### Interfaz de Usuario y Experiencia Visual

- Rediseño Estructural con Paneles Plegables: Organización de las secciones de configuración en tarjetas expandibles que permiten contraer ajustes secundarios para una navegación despejada y cómoda.
- Menús Desplegables y Selectores Contorneados: Rediseño visual de las listas de selección con bordes suaves, esquinas redondeadas y contraste reforzado.
- Alineación Continua de Tablas: Ajuste visual de extremo a extremo en todas las tablas del sistema (Comandos, Temporizadores, Recompensas, Historial y Música), eliminando espacios vacíos en los laterales.
- Formato Estructurado de Mensajes del Bot: Las respuestas automáticas del bot en el chat para avisos, canciones añadidas a la cola y comandos se presentan organizadas con separadores claros y lectura limpia.
- Controles Deslizantes Fluidos: Barras de desplazamiento de volumen, tamaño de texto y márgenes optimizadas para que el arrastre sea suave y no sobrecargue el sistema.

### Protección y Calidad en Directo

- Filtro Anti-Spam para Lectura de Voz: Los mensajes que contienen repeticiones excesivas de caracteres, letras o palabras largas se comprimen automáticamente antes de ser leídos por voz, evitando interrupciones molestas en el directo.
- Supresión de Enlaces en la Voz: Las direcciones web y URLs de imágenes enviadas al chat se omiten de la lectura por voz para evitar la lectura de textos técnicos incomprensibles.
- Mayor Resiliencia en Conexiones de Red: Detección y reconexión inmediata si la plataforma de Kick o Twitch experimenta una caída momentánea de conexión, manteniendo el directo enlazado sin requerir reiniciar la aplicación.
- Optimización de Rendimiento en Arranque: Reducción del tiempo de inicio del programa y carga ligera de las pantallas principales.

---

## Correcciones

### Visualización y Compatibilidad

- Corrección de Fondos en Modo Claro de Windows: Resuelto el fallo donde usuarios con Windows configurado en modo Claro veían textos blancos sobre fondos claros o campos desalineados. Ahora MiniKick mantiene su estética oscura y legible sin importar la configuración de Windows.
- Eliminación de Transparencia en Desplegables de Búsqueda: Corregido el problema por el cual el menú de sugerencias al buscar categorías u opciones se mostraba con fondo transparente y se mezclaba con los botones del formulario.
- Eliminación de Ventanas Fantasma en Segundo Plano: Subsanada la creación de micro-ventanas invisibles que aparecían en la barra de tareas al desplegar calendarios o selectores.
- Estabilidad de la Configuración del Chat: Solucionado el reinicio involuntario de los estilos de la ventana de chat web al abrir la aplicación, preservando siempre la personalización guardada por el usuario.
- Visualización de Opciones en Elementos y Filtros del Chat: Corregido el colapso visual que mostraba vacía la tarjeta de interruptores en los ajustes del chat, permitiendo activar o desactivar con normalidad la visualización de plataformas, insignias, hora, emotes, GIFs, comandos y bots.
- Ajuste de Posición en Chat Horizontal: Corregido el anclaje de mensajes en el formato horizontal para asegurar que las intervenciones fluyan ordenadamente desde la parte inferior de la pantalla.

### Conectividad y Moderación

- Desconexión Segura en Chat de TikTok: Resuelto el cierre forzado y los bloqueos que ocurrían al detener la conexión del chat en vivo de TikTok.
- Corrección de Consultas Largas en Búsqueda de GIFs: Prevenido el fallo de conexión cuando un usuario intentaba buscar animaciones con frases muy extensas en el chat.
- Exclusión de Bots en Espectadores Destacados: El bot del canal y cuentas de moderación ya no se contabilizan indebidamente dentro del ranking de usuarios más activos en el chat.
- Corrección de Superposición en Ventanas Secundarias: Asegurado que los paneles de selección de color y ventanas de confirmación se mantengan siempre visibles por delante de la aplicación para evitar que queden ocultas.
