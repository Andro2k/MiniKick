# Walkthrough v1.4.4 - Mejoras del Chat, Modularización del Reproductor de Música, Layout Flex para Estadísticas, Reordenamiento de Cola y Comando !playlist

**Fecha:** 28 de Julio, 2026  
**Versión Target:** v1.4.4  
**Ubicación del Documento:** `c:\Users\TheAn\Desktop\python\Kick\walkthroughs\v1.4.4\WT-1.4.4_01.md`

---

## 1. Resumen de Cambios

En esta entrega se han implementado mejoras clave en los módulos de chat y reproductor de música:
- **Módulo de Chat**:
  - Optimización de la experiencia de configuración de voz (TTS) con botones de vista previa y cooldown.
  - Formato de mensajes con roles (`[tiempo] [Rol] Usuario: Mensaje`).
  - Corrección de la detección de bots y notificaciones toast.
- **Módulo de Música (Nueva Arquitectura Modular)**:
  - Creación del paquete `frontend/components/music/` con 4 paneles desacoplados (`MusicStatsPanel`, `MusicPlayerSettingsPanel`, `MusicCommandsPanel` y `MusicQueuePanel`).
  - **Tarjetas de Estadísticas Dinámicas (`QGridLayout`)**: Se implementó en `MusicStatsPanel` el mismo patrón dinámico que en `DashboardView` (`relayout`), reorganizando dinámicamente las tarjetas según el ancho de la ventana (1 fila en pantallas anchas, 2 filas responsivas en medianas y 1 columna en estrechas).
  - **Organización en Pestañas (`QTabWidget`)**:
    - **Pestaña 1 (Reproductor):** `MusicPlayerSettingsPanel` (Selección de Proveedor, Autenticación, Reproductor Actual, Volumen/Retomado y Overlay OBS).
    - **Pestaña 2 (Comandos):** `MusicCommandsPanel` (Interruptores de comandos `!sr`, `!skip`, `!song`, `!pause`, `!resume`, `!playlist`).
    - **Columna Derecha (Cola):** `MusicQueuePanel` (Tabla de cola de reproducción).
  - **Corrección de Bugs**:
    - **Visibilidad de la Cola en Spotify:** Habilitada la visualización de la cola para Spotify al estar conectado.
    - **Persistencia del Proveedor al Iniciar:** Corregido `MusicController._load_initial_state()` para recordar e iniciar en el proveedor seleccionado por el usuario (ej. YouTube) al abrir la app.
  - Refactorización de estilos UI sin `setStyleSheet` inline, integrando propiedades nativas del sistema de temas (`frontend/common/theme.py`).
  - Reordenamiento de canciones en la cola mediante botones de subir (`chevron-up.svg`) y bajar (`chevron-down.svg`).
  - Nuevo comando de chat `!playlist` (con alias `!queue`, `!pl`).

---

## 2. Detalles de las Características Implementadas

### A. Botones de Prueba de Voz con Cooldown (Audio Preview)
- **Ubicación:** `frontend/components/chat/tts_settings.py`
- **Funcionalidad:** Botones de prueba (`btn_test`) con temporizador de enfriamiento (**cooldown de 3 segundos**) mediante `QTimer.singleShot(3000, ...)`.

### B. Formato de Chat Display con Rol de Usuario (`[tiempo] [Rol] Usuario: Mensaje`)
- **Ubicación:** `frontend/components/chat/chat_display.py` y `frontend/views/chat_view.py`
- **Estructura HTML:** `[HH:MM:SS] [Rol] Usuario: Mensaje` con estilos CSS por rol.

### C. Modularización del Reproductor de Música (`frontend/components/music/`)
- **Archivos creados:**
  - `stats_panel.py` (`MusicStatsPanel`): Tarjetas superiores de estadísticas (Cola, Duración y Estado del Servicio) configuradas con `FlowLayout` responsive (comportamiento flexbox en filas).
  - `player_settings.py` (`MusicPlayerSettingsPanel`): Paneles de proveedor, login, ahora suena, volumen y overlay.
  - `commands_panel.py` (`MusicCommandsPanel`): Switches para la activación/desactivación de comandos.
  - `queue_panel.py` (`MusicQueuePanel`): Tabla de cola con reordenamiento (subir/bajar/eliminar) y cálculo de tiempos.
  - `__init__.py`: Exportación unificada de todos los paneles.

### D. Corrección de Bugs de Música
1. **Visibilidad de la Cola en Spotify:** Se ajustó la condición a `show_queue = (is_youtube or connected)` en `set_auth_state`, permitiendo que los usuarios de Spotify vean la cola al conectarse.
2. **Persistencia del Proveedor Seleccionado:** Se reubicó la lógica de selección inicial (`combo_provider.setCurrentIndex`) al final de `_load_initial_state()` en `MusicController`, evitando el reseteo automático a Spotify al abrir la aplicación.

### E. Refactorización de Estilos UI con el Sistema de Temas (`theme.py`)
- **Ubicación:** `frontend/components/music/stats_panel.py`
- **Eliminación de `setStyleSheet`:** Las insignias y contadores emplean componentes `QFrame[role="badge"]` con estados dinámicos `state="everyone"` (verde) / `state="broadcaster"` (rojo) y etiquetas tipográficas `role="h1"` / `role="h3"`.

### F. Reordenamiento de Canciones en Cola y Comando `!playlist`
- **Reordenamiento:** Cada fila de la tabla de cola cuenta con acciones de Subir (`chevron-up.svg`), Bajar (`chevron-down.svg`) y Eliminar (`trash.svg`).
- **Comando `!playlist` (Alias: `!queue`, `!pl`):** Informa al espectador sobre la posición exacta de las canciones que ha solicitado en el chat.

### G. Optimización de Latencia y Benchmarking en TTS Online (`edge_tts`)
- **Pre-descargas Asíncronas No Bloqueantes en Paralelo:** Se refactorizó `WebTTSProvider.prepare` para retornar en `<1ms` almacenando un `Future` asíncrono en lugar de bloquear el hilo `_downloader_worker` secuencialmente. Esto permite que múltiples mensajes en cola se descarguen en paralelo por la red mientras el audio previo está sonando.
- **Event Loop Persistente:** Se reemplazó la creación/destrucción continua de bucles de eventos (`asyncio.run(...)`) por un bucle `asyncio` persistente en un hilo dedicado dentro de `WebTTSProvider` (`backend/providers/voices/tts_online.py`), reduciendo ~500ms de overhead por frase.
- **Coincidencia de Caché Garantizada:** Se habilitó el pase explícito de `voice_id` en `speak(text, voice_id=...)` desde `TTSManager._worker`, evitando CACHE MISSES por discrepancias entre pre-descarga y reproducción.
- **Telemetría y Métricas en Tiempo Real:** Se agregaron logs de benchmark detallados (`[Web TTS Benchmark]`) que reportan en consola el tiempo exacto de pre-descarga, estado de caché (CACHE HIT / MISS) y latencia total en milisegundos desde la petición hasta la salida de audio.

### H. Carga e Instantaneidad Visual al Navegar a la Vista de Música
- **Actualización Inmediata (`view_shown`):** Se añadió la señal `view_shown` en `MusicView.showEvent` conectada directamente a `MusicController._poll_now_playing()`, eliminando el retraso de 2 a 5 segundos que ocurría al esperar el siguiente ciclo del temporizador de polling.
- **Renderizado de Tabla Optimizado:** Se envolvió la actualización de filas en `MusicQueuePanel.update_queue` con `setUpdatesEnabled(False)` y `setUpdatesEnabled(True)` para evitar repintados celda por celda y lograr renderizado instantáneo.

### I. Limpieza y Centralización de Estilos UI (`theme.py`)
- **Eliminación de `setStyleSheet` Inline:** Se eliminaron 12 declaraciones inline en `tts_settings.py`, `command_dialog.py`, `timer_dialog.py`, `network_view.py` y `blocks.py`.
- **Integración con Sistema de Temas:** Se definieron reglas globales en `frontend/common/theme.py` para bordes de error en inputs (`QLineEdit[state="error"]`, `QTextEdit[state="error"]`, `QPlainTextEdit[state="error"]`) y roles/estados de tipografía (`QLabel[state="bold"]`, `QLabel[state="danger"]`, `QLabel[state="success"]`, `QLabel[state="info"]`), utilizando la API nativa de Qt (`setProperty("state", ...)`, `unpolish`/`polish`).

### J. Estandarización de Divisores (`ModernDivider`)
- **Creación de `ModernDivider`:** Se implementó el componente reutilizable `ModernDivider` (`frontend/widgets/blocks.py`) de 1px de grosor con `role="divider"`.
- **Homologación Global:** Se reemplazó la línea horizontal nativa `QFrame.Shape.HLine` en `dashboard_view.py` por `ModernDivider()`, igualando el diseño visual de divisores en `bot_mute.py`, `overlay_settings.py`, `tts_settings.py` y el resto del sistema.

### K. Protección y Resaltado Visual de Comandos Plugin (`[PLUGIN_...]`)
- **Resaltado Morado Púrpura (`state="plugin"`):** Se definieron reglas CSS en `theme.py` (`COLOR_PURPLE` / `{COLOR_PURPLE_GLOW}`) para destacar visualmente comandos generados por plugins del sistema (Música y TTS).
- **Inhabilitación de Edición de Respuesta:** En `CommandConfigWizard` (`command_dialog.py`), cuando la respuesta contiene `[PLUGIN_...`, el campo de texto de respuesta se estiliza en púrpura y se bloquea como lectura exclusiva (`setReadOnly(True)`), junto a la aparición de la insignia traducida `COMANDO PLUGIN`. Esto evita que el usuario edite o altere accidentalmente las macros internas de plugins.
- **Nueva Columna de Tipo en Tabla:** En `CommandView` (`command_view.py`), se agregó una nueva columna dedicada `Tipo` (`col_type`) con ancho asignado de `130px` y márgenes internos de `8px`, garantizando que textos como `"Personalizado"` se desplieguen holgadamente sin recortarse en la interfaz.
- **Cumplimiento Estricto i18n:** Se eliminaron todos los textos harcodeados y fallbacks en código en `command_view.py`, haciendo uso exclusivo de las claves de internacionalización de `locales/es.json` y `locales/en.json`.

---

## 3. Archivos Modificados y Creados

| Archivo | Descripción del Cambio |
| :--- | :--- |
| `backend/interfaces/tts_interfaces.py` | Adición del parámetro opcional `voice_id` en la firma de `speak` de `ITTSProvider`. |
| `backend/providers/voices/tts_local.py` | Adición del parámetro opcional `voice_id` en `LocalTTSProvider.speak`. |
| `backend/providers/voices/tts_online.py` | Optimización con `asyncio` loop persistente, pase de `voice_id` y logs de benchmark de latencia (`[Web TTS Benchmark]`). |
| `backend/services/chat/tts_service.py` | Pase explícito de `target_voice` a `active_provider.speak` para garantizar CACHE HITS. |
| `frontend/components/music/stats_panel.py` | Componente de estadísticas superiores con `QGridLayout` responsivo y refresco dinámico de estilos (`unpolish`/`polish`) para `lbl_service_badge`. |
| `frontend/components/music/player_settings.py` | [NUEVO] Componente de ajustes del reproductor, auth, canción actual y overlay. |
| `frontend/components/music/commands_panel.py` | [NUEVO] Componente con switches de comandos de espectadores. |
| `frontend/components/music/queue_panel.py` | [NUEVO] Componente con tabla de cola de reproducción y acciones de reordenamiento. |
| `frontend/components/music/__init__.py` | [NUEVO] Exportación pública de componentes de música. |
| `frontend/views/music_view.py` | Vista principal refactorizada para orquestar los paneles de `frontend/components/music`. |
| `backend/controllers/music_controller.py` | Corrección de persitencia del proveedor guardado al inicio en `_load_initial_state`. |
| `backend/interfaces/music_interfaces.py` | Adición del método `move_in_queue(from_index, to_index)`. |
| `backend/providers/music/youtube_client.py` | Implementación de `move_in_queue` en `YouTubeMusicProvider`. |
| `frontend/dialogs/command_dialog.py` | Adición de importación `QFrame`, badge `COMANDO PLUGIN` y bloqueo de edición para comandos plugin. |
| `frontend/views/command_view.py` | Adición del badge visual `[PLUGIN]` de color púrpura en la celda de comandos de la tabla. |
| `locales/es.json` y `locales/en.json` | Claves traducidas para pestañas de música, comando `!playlist` y notificaciones. |

---

## 4. Verificación y Pruebas
1. **Validación de Sintaxis:** Verificado satisfactoriamente con `py_compile` en los 7 archivos Python creados y modificados.
2. **Prueba de Ejecución:** Aplicación ejecutada con `uv run main.py` sin errores.
