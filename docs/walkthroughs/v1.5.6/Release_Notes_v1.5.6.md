# Release Notes - MiniKick Version 1.5.6

**30 de Agosto, 2026**

## Puntos de Canal Multi-Plataforma (Twitch + Kick), Detección de Archivos Faltantes y Optimización del Sistema

> [!NOTE]
> MiniKick v1.5.6 introduce el soporte integral de Puntos de Canal para **Twitch** junto a **Kick**, permitiendo crear, editar, vincular y activar alertas multimedia interactivas en OBS Studio desde ambas plataformas en tiempo real, además de incorporar detección proactiva de archivos faltantes, mejoras en el reproductor de overlays, autorelleno inteligente en reportes de error, sincronización dinámica de la barra lateral y optimizaciones integrales de logging y pruebas automatizadas.

---

### Novedades (2)

- **[FEATURE] [REWARDS] Soporte Multi-Plataforma de Puntos de Canal (Twitch + Kick):** Integración completa para captura de eventos y gestión de recompensas de Twitch en tiempo real junto a Kick. Permite vincular recompensas existentes o crear nuevas en ambas plataformas, visualizándolas en la tabla de recompensas con insignias temáticas e iconos nativos de cada servicio.
- **[FEATURE] [REWARDS] Detección y Marcado Visual de Archivos Multimedia Faltantes:** Identificación en tiempo real de archivos inexistentes o movidos en la tabla de recompensas vinculadas, mostrando advertencias visuales en color rojo, iconos de alerta, tooltips descriptivos y notificaciones informativas al streamer tanto en previsualizaciones manuales como en canjes en vivo.

---

### Mejoras (8)

- **[IMPROVEMENT] [REWARDS] Asistente de Recompensas con Selección y Creación Multi-Plataforma:** El asistente de configuración permite elegir entre Kick y Twitch, filtrando dinámicamente las recompensas disponibles, auto-asignando el color temático característico de cada plataforma y gestionando la creación y edición directa.
- **[IMPROVEMENT] [OVERLAYS] Reproductor de Overlays Polimórfico:** El overlay de recompensas para OBS Studio ahora detecta automáticamente el tipo de archivo (videos MP4/WebM, audios MP3/WAV e imágenes o GIFs animados), aplicando temporizadores de duración configurables y controles seguros de reproducción automática.
- **[IMPROVEMENT] [REPORTS] Botón Único y Autorelleno de Contacto en Reportes de Error:** Optimización del diálogo de reporte de errores con un único botón de acción directa y autorelleno automático del nombre de usuario según la plataforma activa (Kick, Twitch, TikTok o YouTube).
- **[IMPROVEMENT] [SIDEBAR] Sincronización Dinámica de Perfiles en Barra Lateral:** La barra lateral ahora actualiza automáticamente el nombre del streamer, avatar y estado en vivo tanto al conectar con Twitch como con Kick, gestionando conmutaciones elegantes ante desconexiones de cualquiera de las cuentas.
- **[IMPROVEMENT] [LOGGING] Estandarización Modular de Logs y Auditoría de Acciones:** Registro uniforme de acciones de usuario y eventos de desvinculación para Kick, Twitch, YouTube y TikTok, junto a la reducción de ruido en búsquedas interactivas para mantener los archivos de log limpios y legibles.
- **[IMPROVEMENT] [TESTS] Reestructuración Modular de la Suite de Pruebas Automatizadas:** Reorganización completa de las 142 pruebas unitarias en capas arquitectónicas independientes (Núcleo, Base de Datos, Servicios, Proveedores e Interfaz de Usuario) con ejecución granular y menú interactivo.
- **[IMPROVEMENT] [DB] Migración Automática de Base de Datos:** Actualización automática y transparente del esquema de base de datos local para incorporar soporte multi-plataforma en recompensas sin pérdida de datos.
- **[IMPROVEMENT] [I18N] Cobertura Total de Internacionalización:** Todas las nuevas cadenas de interfaz, asistentes, avisos y notificaciones incorporadas en español e inglés con paridad completa.

---

### Correcciones (4)

- **[FIX] [DASHBOARD] Desacoplamiento del Interruptor de Autostart:** Corregido el conmutador de inicio automático en el panel principal para que únicamente guarde la preferencia de configuración sin disparar ventanas emergentes de autenticación en el navegador mientras la app está en uso.
- **[FIX] [SYSTEM] Corrección de Permisos en Instalación:** Eliminado el falso aviso de error de permisos al procesar archivos de configuración temporal cuando la aplicación se ejecuta instalada en carpetas del sistema.
- **[FIX] [TIMERS] Envío Multi-Plataforma en Temporizadores Automáticos:** Corregido el despachador de mensajes de temporizadores periódicos para enviar alertas de manera segura a los chats de Kick y Twitch según las plataformas seleccionadas.
- **[FIX] [OVERLAYS] Eliminación de Fallos Silenciosos en OBS:** Validación previa de existencia física de recursos antes de emitir alertas al servidor de overlays, evitando errores silenciosos de recursos no encontrados.

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.6 preserva íntegramente las configuraciones y bases de datos previas, migrando automáticamente los datos de recompensas para soportar plataformas múltiples de forma transparente.
