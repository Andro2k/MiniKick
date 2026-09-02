# Release Notes - MiniKick Version 1.5.7

**02 de Septiembre, 2026**

## Control Multimedia Global por Teclado, Rendimiento Extremo de Notificaciones, Arquitectura de Logging y Blindaje de Concurrencia

> [!NOTE]
> MiniKick v1.5.7 introduce el control multimedia global de música mediante las teclas físicas del teclado, un nuevo motor de notificaciones Toast ultrarrápido sin latencia de ventana nativa, captura de crashes con faulthandler, telemetría y loggers modulares dedicados, resolución de fallos COM y un blindaje exhaustivo de hilos en segundo plano para máxima estabilidad en sesiones de streaming prolongadas.

---

### Novedades (2)

- **[FEATURE] [MUSIC] Control Multimedia Global por Teclado:** Ahora puedes pausar, reanudar y saltar canciones de YouTube utilizando los botones multimedia de tu teclado (Play/Pause, Next Track, Stop) de forma global, incluso mientras juegas a pantalla completa, transmites en OBS o tienes MiniKick minimizado en la bandeja del sistema. Incluye switch de activación en la configuración de música.
- **[FEATURE] [SYSTEM] Captura y Diagnóstico Automatizado de Crashes con Faulthandler:** Integración de volcado de memoria multi-hilo en tiempo real (`minikick_crash.log`) capturando fallos nativos C/C++ y adjuntándolos automáticamente con el nombre de usuario y versión en los reportes de crash enviados por webhook.

---

### Mejoras (8)

- **[IMPROVEMENT] [PLATFORMS] Control Reactivo de Conexión en Rewards, Comandos, Timers, Filtros Anti-Spam e Información del Stream:** Los asistentes y vistas de creación/edición (`RewardsConfigWizard`, `CommandConfigWizard`, `CommandView`, `TimerConfigWizard`, `TimersView`, `SpamView`, `ExpandableSettingCard`, `ScheduleView`, `QuickChangePanel`, `ScheduleFormPanel`) ahora detectan y reflejan el estado de vinculación en tiempo real. Se ocultan o desactivan las plataformas desconectadas en las tablas y se bloquea el envío o edición desincronizada.
- **[IMPROVEMENT] [TOAST] Motor de Notificaciones Toast de Alto Rendimiento:** Notificaciones Toast transformadas en widgets ligeros sobre la ventana principal, reduciendo a 0 ms el impacto en el hilo de interfaz, optimizando animaciones a 180 ms e incorporando deduplicación inteligente ante cambios rápidos de switches.
- **[IMPROVEMENT] [LOGGING] Loggers Jerárquicos Modulares Dedicados:** Estandarización de logging profesional con nombres de módulo canónicos (`minikick.*`), telemetría de arranque detallada y filtrado de librerías externas para mantener los registros limpios y legibles.
- **[IMPROVEMENT] [UI] Ajuste de Geometría y Alineación de Diálogos Modales:** Sincronización precisa de dimensiones en diálogos (`ModernFramelessShell`, `ModernConfirmDialog`) antes del centrado en pantalla, eliminando advertencias nativas de Windows (`QWindowsWindow::setGeometry`).
- **[IMPROVEMENT] [UI] Eliminación de Advertencias de Fuentes en ComboBoxes:** Inicialización explícita de tamaño en puntos y hojas de estilo para selectores desplegables, suprimiendo advertencias `QFont::setPointSize`.
- **[IMPROVEMENT] [DASHBOARD] Rediseño de Permisos y Switches Táctiles:** Formateo moderno en lista para la visualización de permisos de canal en Kick y Twitch con switches táctiles de respuesta inmediata.
- **[IMPROVEMENT] [REPORTS] Identificación de Usuario y Versión en Logs de Reportes:** Los archivos de log adjuntos en los reportes de bugs y crashes enviados a Discord ahora llevan el nombre de usuario y versión en su nombre de archivo (ej. `minikick_TheAndro2k_v1.5.7.log` o `minikick_crash_TheAndro2k_v1.5.7.log`) junto a un encabezado identificativo con el sistema operativo y severidad.
- **[IMPROVEMENT] [MUSIC] Optimización y Memoización de Cola y Reproductor:** Deduplicación de firmas de cola en $\mathcal{O}(1)$, cálculo instantáneo de áreas de arrastre en la tabla, memoización del temporizador de progreso y sanitización HTML en nombres de usuario.
- **[IMPROVEMENT] [TESTS] Suite de Pruebas Unitarias al 100%:** 174 pruebas unitarias automatizadas cubriendo todas las capas arquitectónicas del sistema.

---

### Correcciones (9)

- **[FIX] [REWARDS] Aislamiento de Plataformas y Prevención de Mutación de Recompensas:** Se corrigió la lógica de actualización en `RewardsController` y `RewardsConfigWizard` para evitar que recompensas creadas en Kick muten a Twitch (o viceversa), preservando inmutable la plataforma en modo edición.
- **[FIX] [REWARDS] Manejo de Recompensas Eliminadas en Web (404 Not Found) e Indicador de Desvinculación:** Al actualizar una recompensa eliminada en la web de Kick o Twitch, se limpia el ID remoto obsoleto para evitar fallos continuos, se guardan los cambios locales multimedia y se muestra el estado `(Desvinculada)` o `(Desconectado)` con icono y tooltip explicativo en la tabla.
- **[FIX] [TIMERS] Renderizado Reactivo de Plataformas en Tabla de Temporizadores:** En `TimersView`, el badge de plataformas de cada timer ahora evalúa dinámicamente las plataformas conectadas en vivo en lugar de mostrar siempre "Ambas".
- **[FIX] [AUTH] Prevención de Ventanas Emergentes Inesperadas de Kick OAuth:** Desacoplamiento de `get_tokens()` para consultas pasivas de token sin abrir el navegador ni abrir puertos locales de servidor HTTP, delegando el flujo de login únicamente al método explícito `login()`.
- **[FIX] [THREADS] Blindaje de QThreads y Prevención de Access Violation (0xC0000005):** Secuencia de apagado paralelo coordinado con desconexión preventiva de señales para evitar condiciones de carrera al cerrar la app o reiniciar conexiones.
- **[FIX] [AUDIO] Resolución del Error COM 0x8001010d (RPC_E_WRONG_THREAD):** Inicialización y liberación explícita del modelo de apartamentos COM en hilos de síntesis de voz (TTS) y controladores de audio.
- **[FIX] [TWITCH] Resiliencia ante Sesión/Token Expirado en Twitch:** Inicialización asíncrona no bloqueante que previene bloqueos de interfaz o cierres inesperados ante desconexiones o fallos de red.
- **[FIX] [TOAST] Corrección de RuntimeWarning libpyside en ModernToast:** Ciclo de vida seguro en animaciones de notificación sin desconexiones dinámicas inválidas.
- **[FIX] [REWARDS] Concurrencia en Consulta de Recompensas de Twitch:** Prevención de solicitudes simultáneas en `FetchRewardsWorker` mediante flags atómicos de estado.

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.7 mantiene total compatibilidad con configuraciones, bases de datos y tokens existentes.
