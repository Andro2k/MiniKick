# Release Notes - MiniKick Version 1.5.5

**27 de Agosto, 2026**

## Integración TikTok Live, Motor de Voz Local Piper TTS, Overlays Interactivos y Previsualización en Tiempo Real

> [!NOTE]
> MiniKick v1.5.5 representa una de las actualizaciones más completas del proyecto, incorporando compatibilidad completa con TikTok Live en chat y comandos, el nuevo motor de voz neuronal offline Piper TTS con calibración acústica de precisión, previsualización vectorial en tiempo real de overlays musicales, el rediseño del chat flotante minimalista con resplandor, audio hotplug con auto-recuperación y optimizaciones profundas de concurrencia y persistencia.

---

### Novedades (15)

- **[FEATURE] [INTEGRATIONS] Integración Completa con TikTok Live:** Conexión nativa con streams de TikTok Live para recibir comentarios, alertas de regalos, eventos de seguidores y roles de usuario (*super_fan*, *top_gifter*, *moderator*, *subscriber*) en tiempo real y sin necesidad de credenciales complejas (`WT-1.5.5_02`, `WT-1.5.5_03`).
- **[FEATURE] [COMMANDS] Despacho y Ruteo de Comandos para TikTok:** Posibilidad de asignar y ejecutar comandos personalizados y de sistema (`!sr`, `!skip`, `!song`, `!so`, etc.) directamente desde el chat de TikTok con soporte para la columna de base de datos `apply_tiktok` (`WT-1.5.5_03`, `WT-1.5.5_17`).
- **[FEATURE] [AUDIO] Motor de Voz Local Neural Piper TTS:** Síntesis de voz offline ultrarrápida impulsada por modelos ONNX locales, ofreciendo pronunciación natural en español, cero consumo de ancho de banda y latencia inferior a 50 milisegundos (`WT-1.5.5_05`, `WT-1.5.5_14`).
- **[FEATURE] [AUDIO] Calibración Acústica de Precisión para Piper TTS:** Nuevos controles decimales protegidos contra scroll accidental (`NoWheelDoubleSpinBox`) para ajustar la velocidad base (`length_scale`), expresividad fonética (`noise_scale`) y cadencia entre pausas (`noise_w_scale`) (`WT-1.5.5_14`).
- **[FEATURE] [AUDIO] Importador de Modelos ONNX Personalizados:** Funcionalidad para importar cualquier modelo de voz comunitario de Piper (`.onnx` y `.onnx.json`) con normalización automática de configuración en tiempo de ejecución (`WT-1.5.5_14`).
- **[FEATURE] [OVERLAYS] Previsualización Vectorial en Tiempo Real de Reproductores:** Mockup interactivo en la pestaña de Música que refleja de forma instantánea el tema visual seleccionado (*Dynamic, Neon, Glass, Card*) y el modelo de reproductor activo (*Standard, Vinyl Tocadiscos, Pill*) (`WT-1.5.5_20`, `WT-1.5.5_21`).
- **[FEATURE] [OVERLAYS] Nuevo Diseño de Reproductor Tocadiscos (Vinyl):** Overlay musical estilo vinilo clásico con tornamesa, aguja lectora vectorial SVG con cinemática dinámica de pivote, surcos concéntricos y visualizador de ondas sonoras animado (`WT-1.5.5_10`, `WT-1.5.5_22`).
- **[FEATURE] [OVERLAYS] Rediseño de Chat Minimalista (Floating Glow):** Overlay de chat flotante 100% transparente con nombres de usuario con resplandor neón adaptativo al color del autor y texto en blanco puro con doble sombra de alto contraste (`WT-1.5.5_23`).
- **[FEATURE] [OVERLAYS] Biblioteca Completa de Stickers y Secret Emojis de TikTok:** Renderizado vectorial en el overlay de chat de los 46 secret emojis de TikTok, stickers de directos y las mascotas animadas oficiales (Rocky, Rosie, Jollie y Sage) (`WT-1.5.5_15`).
- **[FEATURE] [UI/UX] Indicador Visual de Plataformas en Tabla de Comandos:** Nueva columna en la lista de comandos que muestra insignias vectoriales coloreadas para Kick, Twitch, YouTube y TikTok según la configuración activa de cada comando (`WT-1.5.5_17`).
- **[FEATURE] [UI/UX] Indicador de Dimensiones Recomendadas para OBS Studio:** Textos dinámicos en los ajustes de Chat y Música que sugieren las resoluciones óptimas de lienzo para fuentes de navegador (ej. 1920x80 px en marquesina horizontal, 384x680 px en columna vertical, 580x280 px en vinilo) (`WT-1.5.5_22`, `WT-1.5.5_23`).
- **[FEATURE] [AUDIO] Hotplug y Auto-Fallback de Dispositivos de Audio:** Detección en tiempo real de desconexión de auriculares o altavoces (*QMediaDevices*) con conmutación automática al dispositivo por defecto, evitando congelamientos y bucles de error del sistema CoreAudio (`WT-1.5.5_09`).
- **[FEATURE] [UI/UX] Tarjeta Interactiva de Actualización en la Barra Lateral:** Notificación moderna en el menú lateral con icono estilizado, versión detectada, botón de descarte rápido y botón de acción directa "Actualizar ahora" (`WT-1.5.5_18`).
- **[FEATURE] [FONTS] Soporte Completo para Glifos de Nerd Fonts:** Renderizado nítido de glifos e iconos técnicos de Nerd Fonts en el visor de chat, consola de logs y visor de release notes (`WT-1.5.5_01`).
- **[FEATURE] [TOOLS] Herramienta de Auditoría y Gestión de Iconos:** Nueva utilidad CLI interactiva (`resources/tools/icon_manager.py`) para detectar iconos huérfanos, referencias rotas y exportar reportes de assets (`WT-1.5.5_07`).

---

### Mejoras (15)

- **[IMPROVEMENT] [PERFORMANCE] Precarga de Pistas Musicales (*Zero-Latency Gap*):** Descarga y resolución en segundo plano de la siguiente canción en cola mientras la pista actual se reproduce, logrando transiciones fluidas sin silencios entre canciones (`WT-1.5.5_11`).
- **[IMPROVEMENT] [SECURITY] Sanitización y Reconstrucción Segura contra XSS en Overlays:** Refactorización en el procesamiento de emotes y mensajes en `chat.html` con sanitización estricta por bloques ascendentes antes de inyectar elementos visuales (`WT-1.5.5_16`).
- **[IMPROVEMENT] [SECURITY] Tokens Criptográficos de Sesión en Overlays:** Generación de identificadores de sesión de 32 caracteres para restringir el acceso a los endpoints HTTP y WebSockets locales exclusivamente a las fuentes autorizadas de OBS (`WT-1.5.5_11`).
- **[IMPROVEMENT] [PERFORMANCE] Deduplicación en Cola Circular para TikTok:** Registro de mensajes mediante *Ring-Buffer* de 1,000 identificadores para prevenir duplicados durante ráfagas masivas de comentarios sin incremento de memoria (`WT-1.5.5_02`).
- **[IMPROVEMENT] [AUDIO] Limpieza y Filtrado de Emotes Multi-Plataforma para TTS:** Sanitización previa de etiquetas técnicas de Kick, Twitch, YouTube y TikTok antes de enviar el texto al sintetizador de voz (`WT-1.5.5_15`, `WT-1.5.5_16`).
- **[IMPROVEMENT] [PERFORMANCE] Eliminación del Módulo Network para Ahorro de CPU:** Remoción del servicio en segundo plano que realizaba pings periódicos a servidores externos, reduciendo el consumo de red y ciclos de CPU en reposo (`WT-1.5.5_08`).
- **[IMPROVEMENT] [DATABASE] Auto-Reparación y Chequeo de Integridad SQLite:** Verificación de integridad (*PRAGMA integrity_check*) durante el arranque con reconstrucción automática de esquema y tablas ante fallos de corriente o archivos corruptos (`WT-1.5.5_12`).
- **[IMPROVEMENT] [ARCH] Estandarización de Inyección de Dependencias `i18n`:** Reutilización estricta de la instancia del servicio de traducciones a través de controladores, manejadores y workers para evitar duplicación de cadenas en memoria (`WT-1.5.5_05`, `WT-1.5.5_24`).
- **[IMPROVEMENT] [UI/UX] Distinción de Plataformas en Cola de Música:** Insignias vectoriales coloreadas para Kick (`#53FC18`), Twitch (`#A970FF`), YouTube (`#FF0000`) y TikTok (`#00F2FE`) tanto en la lista de espera como en el panel de reproducción actual (`WT-1.5.5_04`).
- **[IMPROVEMENT] [UI/UX] Depuración y Simplificación del Catálogo de Overlays de Música:** Enfoque en los 3 mejores layouts (*Standard, Vinyl, Pill*) y 4 temas visuales principales (*Dynamic, Glass, Neon, Card*), depurando estilos obsoletos (`WT-1.5.5_13`).
- **[IMPROVEMENT] [PERFORMANCE] Descarte Inmediato de Moderación para Plataformas Read-Only:** Desvío anticipado en $\mathcal{O}(1)$ en los filtros de spam para mensajes provenientes de plataformas de solo lectura como YouTube y TikTok (`WT-1.5.5_04`).
- **[IMPROVEMENT] [UI/UX] Diálogos Modernizados de Confirmación y Desvinculación:** Diálogos estilizados para conectar, desconectar o editar canales de Kick, Twitch, YouTube y TikTok con retroalimentación visual inmediata (`WT-1.5.5_03`, `WT-1.5.5_06`).
- **[IMPROVEMENT] [NETWORK] Heartbeat Keep-Alive en Conexión Twitch WebSocket:** Configuración de intervalos de ping cada 30 segundos para evitar desconexiones silenciosas por parte de routers o cortafuegos (`WT-1.5.5_09`).
- **[IMPROVEMENT] [OVERLAYS] Optimización de Purga del DOM en Overlay de Chat:** Reemplazo del filtrado completo de nodos por eliminación directa del primer hijo cuando el contenedor supera el límite máximo de mensajes configurado (`WT-1.5.5_16`).
- **[IMPROVEMENT] [UI/UX] Unificación de Notificaciones Toast de Conexión:** Formato homogéneo para los avisos de conexión y desconexión en todas las plataformas soportadas (`WT-1.5.5_06`).

---

### Correcciones (12)

- **[FIX] [DATABASE] Preservación de Plataformas en Comandos:** Corrección del reinicio involuntario a todas las plataformas en comandos personalizados y plugins (`!so`, `!death`, `!score`, `!sr`, `!skip`, `!tts`) al iniciar la app o alternar interruptores (`WT-1.5.5_25`).
- **[FIX] [OVERLAYS] Desconexión de Piezas en Aguja de Tocadiscos:** Sustitución de fragmentos CSS por un trazado vectorial SVG unificado con rotación continua sobre su eje de pivote (0° en reproducción, -30° en pausa) (`WT-1.5.5_22`).
- **[FIX] [OVERLAYS] Eliminación de Franjas Negras en Carátulas de YouTube:** Aplicación de escalado inteligente y recorte proporcional (`object-fit: cover`) para erradicar las barras negras superior e inferior codificadas en miniaturas 4:3 de YouTube (`WT-1.5.5_11`).
- **[FIX] [OVERLAYS] Truncamiento y Desbordamiento en Layout Pill:** Corrección de estilos flexbox y adición de puntos suspensivos para garantizar que títulos largos nunca empujen el botón de reproducción fuera del contenedor (`WT-1.5.5_12`).
- **[FIX] [UI/UX] Botón Prematuro de Reinicio en Diálogo de Actualización:** Ocultamiento del botón "Reiniciar ahora" durante la fase inicial de comprobación del servidor, mostrándolo únicamente tras descargar el instalador por completo (`WT-1.5.5_19`).
- **[FIX] [AUDIO] Latencia en Primera Frase de Modelos Piper:** Implementación de precalentamiento asíncrono (*warm-up*) en hilos secundarios para eliminar el retraso de inicialización de tensores ONNX (`WT-1.5.5_14`).
- **[FIX] [AUDIO] Normalización de Modelos Piper Comunitarios:** Corrección en caliente de archivos de configuración antiguos o experimentales para evitar errores de sintaxis fonética o campos ausentes (`WT-1.5.5_14`).
- **[FIX] [NETWORK] Cierre Asíncrono de WebSockets de TikTok:** Corrección de advertencias de tareas pendientes al desconectar streams de TikTok mediante una espera acotada del handshake de cierre (`WT-1.5.5_03`).
- **[FIX] [UI/UX] Sincronización Bidireccional de Switches en Música:** Corrección de estados en los interruptores de comandos musicales para reflejar fielmente la base de datos sin sobrescribir configuraciones (`WT-1.5.5_13`).
- **[FIX] [OVERLAYS] Superposición de Bordes en Chat Minimalista:** Eliminación de contenedores oscuros opacos en el tema Minimal, garantizando fondo 100% transparente y alto contraste tipográfico (`WT-1.5.5_23`).
- **[FIX] [UI/UX] Mockup Estándar de Música:** Ajuste de proporciones en la carátula, barras de ecualización y marcas de tiempo inferior para coincidir exactamente con el overlay HTML (`WT-1.5.5_21`).
- **[FIX] [UI/UX] Estandarización de Cero Texto Quemado:** Migración de mensajes de estado, diálogos, descripciones de dimensiones y tooltips a los catálogos de localización `es.json` y `en.json` (`WT-1.5.5_05`, `WT-1.5.5_06`, `WT-1.5.5_17`, `WT-1.5.5_18`).

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.5 integra la totalidad de las características, refactorizaciones y optimizaciones desarrolladas en los documentos de trabajo desde `WT-1.5.5_01` hasta `WT-1.5.5_25`. Todas tus configuraciones previas, modelos de voz instalados, credenciales, comandos y bases de datos se preservan automáticamente al actualizar.
