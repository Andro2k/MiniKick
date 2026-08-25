# Release Notes - MiniKick Version 1.5.4

**24 de Agosto, 2026**

## Soporte Multi-Plataforma YouTube Live Chat, Motor de Voz Neuronal Piper TTS y Aceleración de Rendimiento

> [!NOTE]
> MiniKick v1.5.4 expande el ecosistema de streaming integrando compatibilidad en tiempo real con **YouTube Live Chat**, el motor de voz neuronal local **Piper TTS** con descarga de voces a demanda, aceleración de deserialización JSON en C/Rust (**`msgspec` / `orjson`**), reducción del **~50% en el tiempo de arranque** y optimizaciones algorítmicas $\mathcal{O}(1)$ en toda la aplicación.

---

### Novedades (10)

- **Integración de YouTube Live Chat en Tiempo Real:** Conexión nativa y directa para capturar el chat de emisiones en vivo de YouTube, incluyendo mensajes convencionales, SuperChats e insignias de roles (Broadcaster, Moderador, Miembro/Patrocinador y Verificado) sin necesidad de claves de Google Cloud ni consumo de cuotas.
- **Motor TTS Neuronal Local Piper TTS:** Incorporación de síntesis de voz neuronal de alta calidad basada en modelos compactos ONNX, funcionando al 100% de manera local en CPU a ~19x de velocidad en tiempo real y sin depender de conexión a internet.
- **Gestor y Descargador de Voces a Demanda:** Nuevo diálogo modal que permite explorar, preescuchar, descargar y desinstalar voces en español (España y México) e inglés con barra de progreso en vivo y verificación instantánea de archivos.
- **Emotes de YouTube en Overlays y Widgets:** Renderizado automático de emotes globales y personalizados de membresías de YouTube como imágenes en el overlay web de chat (`chat.html`), con compatibilidad total en los widgets de explosión de emotes y combo.
- **Control Dinámico de Velocidad y Cadencia de Voz:** Ajuste interactivo de velocidad entre 50% y 150% mediante un control deslizante en el panel de chat, modulando la duración de fonemas en tiempo real.
- **Reorganización de Configuración General en 3 Secciones Modulares:** Rediseño integral de la vista de ajustes agrupada en tarjetas temáticas: *Ajustes de la Aplicación*, *Conexiones de Plataformas* (integrando Kick, Twitch y YouTube) y *Actualizaciones y Soporte*.
- **Despacho Multi-Plataforma Tripartito:** Soporte completo en base de datos para habilitar o deshabilitar de forma independiente comandos de chat, temporizadores y filtros de moderación en Kick, Twitch y YouTube.
- **Identidad Visual de YouTube en Chat y Música:** Insignia distintiva roja (`#EF4444`) en la consola de chat, panel de reproducción y tabla de cola de música para solicitudes realizadas por espectadores de YouTube.
- **Diálogo Modal Moderno para Conexión de YouTube:** Asistente modal optimizado para vincular directos de YouTube mediante URLs estándar, transmisiones `/live` o handles de canal (`@streamer`).
- **Precalentamiento Inteligente de Voz (Zero-Latency Warm-Up):** Sistema no bloqueante en segundo plano que compila los grafos de inferencia ONNX en memoria RAM al iniciar la aplicación, entregando respuestas inmediatas (< 100 ms) desde la primera palabra.

---

### Mejoras (10)

- **Arranque en Frío 50% Más Rápido:** Reducción del tiempo total de inicio de la aplicación de 4.17 s a 2.13 s gracias a la carga diferida (*lazy loading*) de workers, dependencias multimedia y propiedades en `AppContainer`.
- **Motor de Deserialización JSON de Ultra-Alto Rendimiento:** Procesamiento de eventos WebSocket acelerado en 2.48x mediante librerías nativas en C/Rust (`msgspec` / `orjson`), reduciendo el uso de CPU en un ~60% por mensaje.
- **Desalojo de Historiales en Tiempo Constante $\mathcal{O}(1)$:** Migración de listas internas a colas de doble extremo `collections.deque` en `SpamService`, `RewardWorker` y `LogService`, eliminando cuellos de botella por desplazamiento de memoria.
- **Calibración Acústica de Alta Naturalidad en Piper TTS:** Calibración de parámetros acústicos (`noise_scale = 0.667`, `noise_w_scale = 0.8`) para lograr entonaciones humanas, fluidas y sin artefactos metálicos.
- **Caché de Assets y Streaming de Overlays Optimizado:** Carga de plantillas HTML/CSS en memoria RAM y transmisión multimedia en bloques de 64 KB en `OverlayServerManager`, protegiendo contra desconexiones abruptas.
- **Bloqueo Granular de Señales en Paneles de Ajustes:** Prevención de cascadas de eventos no deseadas e inicializaciones redundantes al abrir o modificar ajustes de chat y voz.
- **Estandarización de Hilos y Workers Concurrentes:** Nomenclatura uniforme `setObjectName("Worker_...")` en los 15 workers de la aplicación para simplificar el monitoreo y la depuración del sistema.
- **Auditoría Integral de Componentes y Vistas Responsivas:** Verificación estructural de widgets, diálogos modales y reordenamiento automático de orientación en pantallas de diferentes resoluciones.
- **Unificación de Conexiones de Plataformas con Estado Dinámico:** Tarjeta de integraciones con detección contextual de estado (Conectado / Desconectado), nombres de canal y confirmaciones de desvinculación seguras.
- **Internacionalización Completa con 100% de Paridad:** Cobertura total de traducciones en español e inglés para todas las nuevas opciones, diálogos y herramientas sin cadenas de texto hardcodeadas.

---

### Correcciones (8)

- **Eliminación de Anidamiento y Colisión en Emotes de YouTube:** Corrección de la sustitución recursiva de etiquetas HTML al recibir múltiples emotes idénticos consecutivos en un mismo mensaje de YouTube.
- **Supresión de Slugs de Emotes de YouTube en Lectura TTS:** El sintetizador de voz remueve códigos de texto como `:face-purple-crying:` para pronunciar únicamente las palabras habladas de forma natural.
- **Prevención de Falsos Positivos en Moderación Anti-Spam:** Los filtros de símbolos y mayúsculas limpian los shortcodes de YouTube antes de calcular porcentajes, evitando sanciones accidentales a la audiencia.
- **Eliminación de Pausa Inicial y Congelamientos al Cambiar de Voz:** El precalentamiento asíncrono y la carga en hilos demonio eliminan cualquier bloqueo de la interfaz al conmutar entre motores TTS.
- **Limpieza de Interfaces Obsoletas y Código Muerto en Core:** Depuración del módulo residual `music_interfaces.py` y eliminación de métodos huérfanos en `main_window_core.py`.
- **Supresión de Logs Ruidosos de Descomposición de Fonemas:** Eliminación de trazas innecesarias de depuración de bajo nivel de Piper en `minikick.log`.
- **Prevención de Descargas Síncronas Bloqueantes en Hilos de UI:** La verificación de modelos instalados no detiene la interfaz gráfica gracias a la gestión por workers dedicados.
- **Protección contra Desplazamiento Lineal en Redenciones de Kick:** Reemplazo de desplazamientos $\mathcal{O}(n)$ en el historial de eventos por operaciones atómicas $\mathcal{O}(1)$.

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.4 consolida el trabajo desarrollado a lo largo de los documentos `WT-1.5.4_01` al `WT-1.5.4_19`. Todas las configuraciones previas, bases de datos SQLite, comandos, temporizadores y credenciales de Kick y Twitch se migran de forma totalmente automática y segura.
