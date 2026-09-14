# Release Notes - MiniKick Version 1.5.9

**12 de Septiembre, 2026**

## Suite de Alertas Granular, Duplicación Cross-Platform, Overlays Zero-Latency, Nuevos Widgets y Restauración Selectiva

> [!NOTE]
> MiniKick v1.5.9 representa una de las actualizaciones evolutivas más extensas del proyecto. Introduce un sistema de restauración selectiva de respaldos con inspección instantánea, una suite remodelada de personalización granular de alertas con 14 animaciones y layout simétrico de 3 columnas, duplicación cross-platform de recompensas y alertas, modernización del overlay de chat con insignias en Base64 a 0 ms de latencia y Prime Gaming, nuevos widgets de OBS para espectadores activos y reloj, control de música con scrubber interactivo, comandos en vivo de moderación de voz, y la estandarización canónica del 100% de la arquitectura del código.

---

### Novedades (14)

- **[FEATURE] [BACKUP] Diálogo Interactivo de Restauración Selectiva de Respaldos:** Permite seleccionar de forma granular qué secciones restaurar (Ajustes, Alertas, Recompensas, Comandos, Filtros Anti-Spam, Temporizadores, Horarios y Widgets) mediante una ventana modal interactiva con recuento de elementos, botones de selección rápida y verificación previa en tiempo constante sin sobreescribir datos innecesariamente.
- **[FEATURE] [ALERTS] Biblioteca de Animaciones de Entrada y Salida Independientes:** 7 animaciones de inicio y 7 de cierre (desvanecidos, desplazamientos laterales y verticales, zoom y rebotes elásticos) con configuración de duración en segundos ajustable de forma independiente para cada alerta y sincronización precisa con OBS Studio.
- **[FEATURE] [ALERTS] Control Visual Granular y Tipografía Avanzada de Contenedor:** Ajustes de dimensiones de contenedor (ancho y alto personalizables o automático), radio de esquinas redondeadas, relleno interior, separación entre elementos, sombra profunda de caja, alineación de texto de 4 modos, peso tipográfico de 4 niveles (Normal, Seminegrita, Negrita, Extra negrita) y sombra de texto para garantizar contraste sobre cualquier fondo de directo.
- **[FEATURE] [ALERTS] Barra de Variantes de Alerta y Layout Simétrico de 3 Columnas:** Navegación por pestañas tipo píldora con scroll horizontal para alternar y conmutar el estado activo de cada evento rápidamente. Organización de la interfaz en tres columnas perfectamente emparejadas (Ajustes de Contenedor, Previsualización expandida al centro y Ajustes de Tipografía/Multimedia) con adaptación automática a diseño vertical en resoluciones inferiores a 1280 px.
- **[FEATURE] [ALERTS] Duplicación Rápida de Configuraciones de Alerta:** Botón de duplicar que permite clonar instantáneamente todos los estilos visuales, colores, animaciones, tipografía y multimedia de un evento hacia otro o propagarlos hacia todas las demás alertas en un solo clic.
- **[FEATURE] [REWARDS] Duplicación Cross-Platform de Recompensas de Puntos:** Asistente de duplicación que precarga multimedia, costos, volumen y colores de una recompensa existente con sugerencia inteligente para clonarla directamente en la plataforma opuesta (Kick hacia Twitch o viceversa) o en la misma plataforma con sufijo automático.
- **[FEATURE] [REWARDS] Soporte Multiplataforma para Recompensas con el Mismo Nombre:** Posibilidad de crear y gestionar simultáneamente recompensas homónimas en Kick y Twitch de forma totalmente independiente, aislando sus configuraciones mediante claves compuestas para que ninguna acción en una plataforma altere a la otra.
- **[FEATURE] [CHAT] Insignias Oficiales Zero-Latency y Soporte de Prime Gaming:** Integración de insignias oficiales de Twitch y Kick en Base64 de alta resolución garantizando 0 ms de latencia y eliminando imágenes rotas, incorporando la corona oficial de Prime Gaming, los 99 niveles oficiales de Kick y soporte para emoticonos gigantes (Bigmoji).
- **[FEATURE] [CHAT] Desvanecimiento Suave (Edge Fade) y Contraste Dinámico de Nombres:** Efecto de máscara de degradado en los bordes del chat para disolver los mensajes de forma cinematográfica en OBS, junto con un algoritmo de corrección automática de luminosidad que garantiza legibilidad de nombres oscuros sobre fondos oscuros.
- **[FEATURE] [WIDGETS] Nuevos Widgets para OBS (Live Top Chatters y Reloj/Fecha):** Nuevo widget en vivo para reconocer a los espectadores más activos del chat en pantalla y nuevo widget configurable de hora y fecha actual, ambos construidos con iconografía vectorial SVG y estética de cristal minimalista.
- **[FEATURE] [MUSIC] Barra de Progreso Deslizante Interactiva (Scrubber) y Búsqueda Seek:** Capacidad de saltar a cualquier punto de la reproducción de canciones de YouTube o música local en tiempo real arrastrando la barra de progreso en el reproductor.
- **[FEATURE] [TTS] Comandos de Moderación en Chat y Control por Plataforma:** Comandos de moderación en tiempo real (!ttsmute y !ttsblock) ejecutables desde el chat de transmisión, acompañados de switches individuales en la interfaz para activar o silenciar la voz sintetizada por plataforma de forma independiente.
- **[FEATURE] [SYSTEM] Selector de Navegador Web para Autenticación y Enlaces:** Selector dedicado con detección automática de navegadores instalados en el sistema (Chrome, Edge, Firefox, Brave, Opera, Vivaldi) o selección de ejecutable personalizado para flujos de inicio de sesión OAuth y apertura de previsualizaciones.
- **[FEATURE] [INTEGRATIONS] Integración Estable de TikTok Live Chat sin Navegador Embebido:** Conexión directa y fluida mediante WebSocket autenticado con firma dedicada, permitiendo recibir eventos de chat en vivo con avatares y roles sin necesidad de ventanas de navegador embebidas ni resolución manual de captchas.

---

### Mejoras (11)

- **[IMPROVEMENT] [ARCHITECTURE] Estandarización Canónica del 100% de la Base de Código:** Auditoría y normalización integral de los 179 archivos del proyecto bajo convenciones canónicas estrictas en todas las capas (interfaces, manejadores, proveedores, servicios, diálogos y vistas), eliminando redundancias léxicas y dependencias circulares.
- **[IMPROVEMENT] [UI] Erradicación Total de Estilos Inline en Favor del Tema Nativo:** Reemplazo de estilos CSS manuales en componentes por selectores de roles y estados centralizados, asegurando coherencia visual global y mantenimiento simplificado.
- **[IMPROVEMENT] [UI] Optimización de Altura y Espaciado en Tablas del Sistema:** Incremento de la altura estándar de filas a 42 px y optimización del relleno interior a 2px vertical, otorgando holgura completa a caracteres tipográficos con trazos descendentes (como las letras p, g, j, q, y) en las 6 tablas de la aplicación (Comandos, Recompensas, Temporizadores, Logs, Horarios y Cola de Música).
- **[IMPROVEMENT] [REWARDS] Ordenamiento Alfabético Predeterminado:** La tabla de recompensas vinculadas se organiza automáticamente de forma alfabética de la A a la Z al cargar o actualizar datos, mejorando la localización visual de elementos.
- **[IMPROVEMENT] [ALERTS] Fidelidad Geométrica 1:1 en Previsualización:** Cálculo proporcional exacto en el lienzo de vista previa que reproduce fielmente relaciones de aspecto cuadradas y rectangulares, manteniendo centrado el contenido textual y multimedia tal como se emitirá en OBS Studio.
- **[IMPROVEMENT] [CHAT] Modularización y Optimización de Peso del Overlay de Chat:** Desacoplamiento de la lógica del chat web y reducción de peso de 238 KB a 14.8 KB con soporte de recarga automática en caliente por fecha de modificación de archivo.
- **[IMPROVEMENT] [WIDGETS] Sustitución de Emojis por Iconografía Vectorial SVG:** Estandarización visual de todos los overlays de widgets de OBS sustituyendo emojis dependientes del sistema operativo por iconos vectoriales nítidos de alta definición.
- **[IMPROVEMENT] [WIDGETS] Reconciliación REST y Resolución de Empates en Encuestas:** Algoritmo concurrente para sincronización de encuestas en vivo y resolución equitativa en caso de empate de votos.
- **[IMPROVEMENT] [DATABASE] Esquema Relacional Compuesto y Migraciones No Destructivas:** Clave primaria compuesta por nombre y plataforma en tablas de recompensas con actualización de esquema automática que preserva íntegramente el historial de redenciones previas.
- **[IMPROVEMENT] [I18N] Consolidación de Claves de Copiado de Enlaces:** Unificación de todas las acciones de copiado de URLs para overlays bajo una única clave común en español e inglés, reduciendo la memoria del árbol de localización.
- **[IMPROVEMENT] [QUALITY] Herramientas de Auditoría y Calidad de Código:** Calibración de herramientas de análisis sintáctico para detección estricta de selectores QSS huérfanos, iconos sin uso y paridad completa de cadenas de idioma en archivos JSON.

---

### Correcciones (10)

- **[FIX] [DATABASE] Corrección de Conflicto de Clave Foránea en Recompensas:** Eliminación del error de coincidencia de claves foráneas en SQLite que impedía guardar o eliminar configuraciones de recompensas y provocaba reversión de cambios al recargar.
- **[FIX] [REWARDS] Corrección de Falso Estado de Recompensa Desvinculada:** Resuelto el problema donde recompensas homónimas entre Twitch y Kick se sobreescribían en memoria y se mostraban incorrectamente como desvinculadas en la tabla.
- **[FIX] [ALERTS] Corrección de Imagen Velada y Fondo Lechoso en Alertas:** Supresión de filtros de desenfoque y opacidades indebidas en diseños superpuestos, permitiendo fondos 100% transparentes sin halos grisáceos sobre la transmisión.
- **[FIX] [ALERTS] Corrección de Desbordamiento Multimedia y Recorte de Formas:** Contención del elemento multimedia dentro de los límites de la tarjeta de alerta y reemplazo de recortes circulares forzados por bordes rectangulares redondeados elegantes.
- **[FIX] [ALERTS] Sincronización de Duración en Despedida de Alertas:** Cálculo dinámico de la animación de salida en el overlay web respetando los segundos exactos configurados antes de la remoción del elemento.
- **[FIX] [ALERTS] Especialización Exclusiva de Alertas para Twitch:** Eliminación limpia de alertas no oficiales de Kick para concentrar el módulo en webhooks 100% oficiales y estables.
- **[FIX] [UI] Corrección de Letras Cortadas en Disparadores de Comandos:** Ajuste de márgenes verticales y alineación en celdas de tabla para evitar el truncamiento del trazo inferior en comandos como !explosion.
- **[FIX] [THREADS] Blindaje de Hilos Secundarios en Moderación y Pruebas:** Prevención de cierres inesperados y excepciones de acceso en tareas en segundo plano mediante desconexión preventiva de señales y cierre coordinado de hilos.
- **[FIX] [AUDIO] Supresión de Advertencias Nativas de FFmpeg:** Silenciamiento de advertencias de consola no críticas durante la reproducción y salto de pistas de audio.
- **[FIX] [TIKTOK] Resolución de Rechazo WebSocket HTTP 400:** Corrección de la cabecera y firma de conexión en el cliente de chat de TikTok Live garantizando enlace permanente.

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.9 mantiene compatibilidad total con bases de datos existentes mediante migraciones automáticas al iniciar, preserva todas las configuraciones previas e incorpora el nuevo diálogo de importación selectiva para mayor seguridad al restaurar copias de seguridad.
