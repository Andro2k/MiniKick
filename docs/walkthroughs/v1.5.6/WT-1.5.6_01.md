# Walkthrough 1.5.6_01: Auditoría Integral de Frontend, Tests, Runner y Soporte Multi-Plataforma de Puntos de Canal (Kick + Twitch) (MiniKick v1.5.6)

## 1. Detección y Marcado Visual de Archivos Faltantes en Puntos y Recompensas

### Problema Detectado
Al configurar recompensas de puntos de canal vinculadas a archivos multimedia (videos, audios, gifs o imágenes) y posteriormente mover o eliminar dichos archivos del disco:
1. La tabla en la vista de recompensas (`RewardsView`) renderizaba las filas con normalidad sin advertir que el archivo ya no existía en el equipo.
2. Al pulsar el botón "Probar en OBS" en la tabla, el backend enviaba la orden al servidor overlay y este fallaba silenciosamente con un error 404 en la consola web sin notificar al streamer.
3. Cuando un espectador en vivo canjeaba una recompensa con archivo movido/inexistente, el overlay omitía el evento silenciosamente sin avisar al streamer sobre la causa del fallo.
4. El asistente de configuración (`RewardsConfigWizard`) no validaba la existencia física en disco al editar o guardar.

### Solución Aplicada
- **[`RewardsService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/rewards/rewards_service.py)**: Método `is_file_valid(config)` $\mathcal{O}(1)$ y protección en `trigger_preview`.
- **[`RewardsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py)**: Marcado visual con texto en `COLOR_RED`, icono `alert-triangle.svg`, tooltips explicativos y contador de advertencias en encabezado de tarjeta.
- **[`RewardsConfigWizard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/rewards_dialog.py)**: Estado de error visual en campos con rutas inexistentes y validación física previa a guardar.
- **[`RewardsController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/rewards_controller.py)** & **[`MainWindowCore`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)**: Notificaciones Toast y logs cuando se intenta probar o canjear un archivo inexistente.

---

## 2. Auditoría y Optimización de Todas las Capas Frontend

### 2.1. [`frontend/common/`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common) y [`frontend/navigation/`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation)
- **[`theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)**:
  - Añadido `@lru_cache(maxsize=128)` a `get_qss_colored_icon` para resolver rutas generadas en memoria $\mathcal{O}(1)$ sin accesos continuos a disco.
  - Eliminada declaración duplicada de `COLOR_TWITCH_GLOW`.
- **[`icons.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/icons.py)**:
  - Ampliado `maxsize=128` en `_load_svg_raw` y `get_icon` para abarcar la totalidad de los 91 iconos SVG del proyecto sin desalojos de memoria RAM.
  - Optimizado el formato del logger a evaluación perezosa (`%s`).
- **[`sidebar_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py)**:
  - Asignado `self` como padre al grupo de animación `QParallelAnimationGroup` para gestión de ciclo de vida en Qt.
  - Detención segura de animaciones en vuelo para evitar colisiones ante clics repetidos.
  - Simplificada la conexión del slot `finished` sin bloques de desconexión propensos a errores en tiempo de ejecución.

### 2.2. [`frontend/components/`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components)
- **[`widget_card_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/widgets/widget_card_component.py)**:
  - Eliminada la emisión duplicada de `self.widget_changed.emit(...)` en el método `_on_changed()`, evitando dobles escrituras en base de datos.
- **[`tts_settings.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py)**:
  - Documentada la compatibilidad del método `update_languages` y verificado el desacoplamiento de filtros de lenguaje tras la consolidación de proveedores de voz (Piper / Web / Local).

### 2.3. [`frontend/dialogs/`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs)
- **[`timer_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/timer_dialog.py)**:
  - Eliminadas líneas duplicadas de configuración de switches Kick/Twitch en el método `_load_existing`.
- **[`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)**:
  - Añadida clave de traducción `common.status.warning` y claves multi-plataforma asegurando 100% de cobertura en pruebas de integridad i18n.

### 2.4. [`frontend/widgets/`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets)
- **[`blocks.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)**:
  - Reutilización de `self._icon_down` pre-instanciado en el constructor de `ExpandableSettingCard._build_header`, eliminando re-generaciones innecesarias del icono de colapso.

### 2.5. [`frontend/views/`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views)
- **Separación de Responsabilidades (SoR)**:
  - 100% de las 11 vistas (`ChatView`, `CommandView`, `DashboardView`, `LogView`, `MusicView`, `RewardsView`, `ScheduleView`, `SettingsView`, `SpamView`, `TimersView`, `WidgetsView`) operan exclusivamente sobre la capa de presentación mediante señales Qt, sin lógica de persistencia o red acoplada.
- **Big-O & Rendimiento**:
  - `CommandView` y `TimersView` encapsulan la población de filas en `setUpdatesEnabled(False/True)`.
  - `CommandView._apply_filters` opera en $\mathcal{O}(N)$ de pasada única.
  - `DashboardView` implementa clipping vectorial `QPainterPath` con caché geométrica en `SegmentedDistributionBar`.

---

## 3. Organización de Tests, Runner y Captura de Puntos de Canal (Twitch EventSub)

### 3.1. Corrección de Pytest (`resources/tests/`)
- Eliminado el archivo huérfano duplicado `resources/tests/test_piper_synthesis.py` resolviendo el fallo `import file mismatch` durante la recolección automática de pytest.

### 3.2. Sincronización y Manejo de `Ctrl+C` en [`run_tests.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/run_tests.py)
- Corregidas las rutas a inspectores en vivo y agregada la función `_safe_run` para capturar `KeyboardInterrupt` (`Ctrl+C`) de forma elegante retornando al menú interactivo sin tracebacks.

### 3.3. Estandarización de Estructuras JSON RAW en Todos los Inspectores en Vivo
- **Kick**, **YouTube** y **TikTok** formatean cada evento con su estructura JSON estructurada completa.

### 3.4. Integración de Twitch EventSub WebSocket & Scopes de Puntos de Canal
- Añadidos `channel:read:redemptions` y `channel:manage:redemptions` a [`backend/services/auth/oauth_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py).
- Añadido flag `--login` en [`resources/tests/live/twitch_live.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/live/twitch_live.py) y en el menú interactivo para abrir el navegador y autorizar en 1 clic los permisos de Puntos de Canal.
- Conexión paralela con **Twitch EventSub WebSocket** (`wss://eventsub.wss.twitch.tv/ws`).
- Suscripción y captura en tiempo real de **Puntos de Canal** (`channel.channel_points_custom_reward_redemption.add`), mostrando título, costo, imagen, usuario y payload completo.

---

## 4. Integración Multi-Plataforma de Puntos de Canal (Twitch + Kick) en MiniKick

### 4.1. Base de Datos SQLite (`backend/database/`)
- **[`DatabaseManager`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py)**: Se añadió la columna `platform TEXT DEFAULT 'kick'` a la tabla `obs_rewards` y el diccionario de migraciones automáticas.
- **[`SQLiteRewardsStorage`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/rewards_storage.py)**: Métodos `load_all()` y `save_all()` adaptados para persistir y restaurar el campo `platform` por recompensa.

### 4.2. Cliente Helix de Twitch (`backend/providers/chat/twitch_client.py`)
- Implementados los endpoints completos de recompensas de puntos de canal:
  - `fetch_channel_rewards(broadcaster_id: str) -> dict`: Consulta todas las recompensas personalizadas del canal vía `GET /helix/channel_points/custom_rewards`.
  - `create_channel_reward(broadcaster_id: str, title: str, cost: int, description: str, background_color: str, is_user_input_required: bool) -> dict`: Crea recompensas personalizadas vía `POST /helix/channel_points/custom_rewards`.
  - `update_channel_reward(broadcaster_id: str, reward_id: str, payload: dict) -> dict`: Modifica recompensas existentes vía `PATCH /helix/channel_points/custom_rewards`.
  - `delete_channel_reward(broadcaster_id: str, reward_id: str) -> bool`: Elimina recompensas en canal vía `DELETE /helix/channel_points/custom_rewards`.

### 4.3. Workers de Recompensas (`backend/workers/rewards_worker.py`)
- **`FetchRewardsWorker`**, **`CreateRewardWorker`**, **`UpdateRewardWorker`**: Modificados para aceptar `platform="kick"|"twitch"` y despachar llamadas de forma no bloqueante a los clientes API respectivos.
- **`TwitchRewardWorker`**: Hilo en background (`QThread`) conectado a Twitch EventSub WebSocket (`wss://eventsub.wss.twitch.tv/ws`) que se suscribe automáticamente a `channel.channel_points_custom_reward_redemption.add` y emite la señal `reward_redeemed(user, reward_title, user_input)` en tiempo real.

### 4.4. Asistente y Vista de Recompensas (`frontend/`)
- **[`RewardsConfigWizard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/rewards_dialog.py)**:
  - Selector de plataforma (Radio buttons Kick vs Twitch) en el Paso 1.
  - Filtrado dinámico de recompensas existentes según la plataforma seleccionada.
  - Auto-ajuste de color temático por defecto (`#00e701` para Kick y `#9146FF` para Twitch).
  - Bloqueo y persistencia de plataforma en modo edición.
- **[`RewardsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py)**:
  - Añadida columna "Plataforma" en la tabla de recompensas con badges coloridos e iconos nativos (`brand-kick.svg` y `brand-twitch.svg`).
  - Cabecera y estado vacío actualizados para reflejar compatibilidad multi-plataforma.

### 4.5. Controlador y Núcleo (`RewardsController` & `MainWindowCore`)
- **[`RewardsController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/rewards_controller.py)**: Despacho inteligente de creación, edición y carga de recompensas según la plataforma especificada en el diccionario de configuración.
- **[`MainWindowCore`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)**:
  - En `_on_twitch_connected`, inicia `TwitchRewardWorker` y consulta recompensas existentes vía `_fetch_twitch_rewards`.
  - Conecta la señal `reward_redeemed` de Twitch directamente con el servidor overlay y reproductor multimedia (`_on_reward_redeemed`).
  - Detención segura e integrada de todos los workers de Twitch al desconectar o cerrar la aplicación.

### 4.6. Resiliencia en Edición ante Restricciones de Twitch API (HTTP 403)
- **Manejo de Recompensas Creadas en el Dashboard de Twitch**: Twitch Helix restringe la modificación vía API (`PATCH /helix/channel_points/custom_rewards`) únicamente a recompensas creadas por el mismo `Client-Id`. Al editar una recompensa creada en la web de Twitch, `RewardsController._on_reward_update_error` captura el error 403 y **siempre guarda los ajustes locales del trigger multimedia (archivo, volumen, coordenadas X/Y, escala) en SQLite `obs_rewards`**, emitiendo un Toast informativo con la aclaración de que el título/costo en Twitch debe cambiarse en la web.

### 4.7. Barra de Búsqueda, Filtros Multi-Plataforma y Columna de Costo en `RewardsView`
- **Barra de Búsqueda Reactiva**: Integrada en la tarjeta con filtrado dinámico en tiempo real $\mathcal{O}(N)$ por nombre de recompensa, archivo o plataforma.
- **Columna de Costo (`col_cost`)**: Incorporada en el layout de la tabla (`X pts`), con ordenamiento numérico (*Menor a mayor / Mayor a menor*).
- **Filtros por Encabezado (`ModernFilterHeader`)**:
  - Filtro desplegable para Plataforma (*Todos*, *Kick*, *Twitch*) con ordenamiento A-Z / Z-A.
  - Ordenamiento alfabético en columna Recompensa.
  - Ordenamiento numérico en columna Costo.

### 4.8. Verificación Exhaustiva y Renovación Separada de Permisos (Kick & Twitch)
- **Catálogo Completo de Scopes**:
  - `KickAuthManager`: Valida `user:read`, `channel:read`, `channel:write`, `channel:rewards:read`, `channel:rewards:write`, `chat:write`, `moderation:ban`, `moderation:chat_message:manage`.
  - `TwitchAuthManager`: Valida `chat:read`, `chat:edit`, `user:read:chat`, `user:write:chat`, `channel:moderate`, `moderator:manage:chat_messages`, `moderator:manage:banned_users`, `channel:manage:broadcast`, `channel:read:redemptions`, `channel:manage:redemptions`.
- **Banners Separados en `DashboardView`**: Notificaciones independientes con insignias e iconos temáticos (`brand-kick.svg` y `brand-twitch.svg`), botones dedicados (`btn_update_kick` y `btn_update_twitch`) y evaluación automática en arranque y cambios de sesión.

### 4.9. Renovación Integral del Panel de Control (Dashboard Multi-Plataforma, Analítica SQLite, Perfil Desacoplado y Persistencia $\mathcal{O}(1)$)
- **Centro Multi-Plataforma**: 4 mini-tarjetas dedicadas (**Kick**, **Twitch**, **YouTube**, **TikTok**) con insignias temáticas, estado en vivo (@canal o desconectado), contador de mensajes en tiempo real y botones de acción rápida.
- **Desacoplamiento Total de la Visibilidad**:
  - La analítica, las métricas globales de sesión, la barra de distribución y el top 5 de comandos permanecen **permanentemente visibles y activos** sin importar qué plataforma esté conectada o si Kick no está vinculado.
- **Tarjeta de Perfil Multi-Canal Inteligente con Metadatos Completos de Twitch y Fecha de Creación**:
  - Renderiza automáticamente los datos de perfil del canal activo (**Kick** o **Twitch**).
  - **Tarjeta de Fecha de Creación**: Reemplazo de la tarjeta de VODs por la fecha de apertura del canal (`created_at`) con icono temático `calendar.svg`.
  - **Enriquecimiento Integral de Twitch**: Soporte oficial del scope `moderator:read:followers` con consulta a `/helix/channels/followers?broadcaster_id={id}&moderator_id={id}` para el conteo real de seguidores, y `/helix/channels` para la última categoría de transmisión (`game_name`).
  - Selector dinámico de pestañas `[Canal Kick]` y `[Canal Twitch]` con alternancia instantánea $\mathcal{O}(1)$ cuando múltiples cuentas están conectadas.
  - Estado neutral compacto y no invasivo cuando no hay canales de streaming vinculados.
- **Persistencia en SQLite y Caché Binaria de Avatares**:
  - **Tabla `channel_profiles`**: Almacena en base de datos local la última información conocida de cada streamer. Al iniciar la aplicación, los datos se cargan de inmediato en $\mathcal{O}(1)$ sin peticiones de red.
  - **Integración `SQLiteAvatarStorage`**: `AvatarService` recupera de inmediato los avatares binarios cacheados (`avatar_cache`), reduciendo al mínimo el consumo de ancho de banda y cuota de APIs externas.
- **Analítica SQLite en Tiempo Real**:
  - Extracción agregada $\mathcal{O}(\log N)$ de los **Top 5 Comandos más usados** con barras de progreso relativo.
  - Resumen visual de módulos en ejecución (Comandos activos, Timers activos, Recompensas vinculadas).
  - Próximo horario de stream agendado reflejado directamente en las tarjetas de estadísticas del canal.
  - **Barra de Distribución Segmentada**: Proporción visual instantánea de mensajes procesados entre Kick, Twitch, YouTube y TikTok.

### 4.10. Optimización de Respuesta Instantánea en Escalado de UI (Font Size)
- **Eliminación del Debounce Innecesario**: Se removió el temporizador de retardo de 250 ms en `_apply_dynamic_theme`, aplicando el cambio de estilo de forma síncrona e instantánea $\mathcal{O}(1)$ al seleccionar una opción en el `QComboBox`.
### 4.12. Corrección de Distintivo de Plataforma en Canjes de Puntos
- **Enrutamiento Preciso Multi-Plataforma**: `_on_reward_redeemed` ahora recibe y propaga explícitamente el parámetro `platform` (`"twitch"` o `"kick"`), garantizando que el distintivo de plataforma en `ChatDisplayPanel` renderice el icono y color oficial correspondiente (**Twitch** `#9146FF` o **Kick** `#53FC18`).
- **Integración con TTS y Pipeline**: Se asegura que el `ChatMessageDTO` originado por el mensaje de entrada del usuario en el canje preserve la plataforma de procedencia.

### 4.14. Tarjeta Unificada de Perfil de Canal (SaaS / Fintech Aesthetic)
- **Consolidación en un Único Card**: Se refactorizó la visualización del perfil del canal en `DashboardView`, integrando en una sola tarjeta (`card_channel_profile`):
  - **Fila Superior (Hero)**: Avatar circular de 68x68 px, subtítulo de categoría (`CANAL DE STREAMING`) y columna de identidad estructurada verticalmente:
    1. **Línea 1**: `Nombre del Streamer` (`role="h1"`) junto al `[badge de kick o twitch]` (`role="badge_kick"` / `role="badge_twitch"`).
    2. **Línea 2**: `# de seguidores` formateado en su propia línea (`role="body"`).
    3. **Línea 3**: `Descripción / Biografía` con ajuste de línea multilínea (`role="body"`).
    - Botón de acción rápida: `[ Abrir Canal ↗ ]` que enlaza directamente a la transmisión del streamer.
  - **Integración de Badges en Theme**: Las insignias `badge_kick` y `badge_twitch` se alinearon formalmente con la familia de componentes `QFrame[role="badge"]` / `QLabel[role="badge_*"]` usando `border-radius: {RADIUS_MD}px; padding: {PADDING_BADGE}; font-weight: 700;`.
  - **Divisor Horizontal Sutil**: Separador visual tenue `ModernDivider`.
  - **Fila Inferior (Metadatos)**: 4 columnas organizadas con encabezado en mayúsculas gris tenue y valor destacado: `FECHA CREACIÓN`, `ÚLTIMA CATEGORÍA`, `ID DE CANAL / SALA` y `PRÓXIMO HORARIO`.
- **Adaptabilidad Responsiva**: La cuadrícula de metadatos se reorganiza fluidamente a 2x2 en pantallas estrechas ($< 600\text{px}$) y 1x4 en pantallas estándar.
- **Eliminación de Warnings de Layout en Qt**: Cada columna de metadatos se encapsula como un `QWidget` individual en `self.metadata_grid`, previniendo advertencias de re-asignación de layout (`QLayout::addChildLayout`) durante el redimensionamiento o renderizado inicial.

### 4.15. Estandarización y Renombrado de Workers Multi-Plataforma
- **Simetría en la Capa de Workers**: Se crearon [`kick_auth_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/kick_auth_worker.py) y [`kick_chat_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/kick_chat_worker.py) definiendo explícitamente `KickAuthWorker` y `KickChatWorker`.
- **Compatibilidad hacia atrás**: Se mantuvieron shims en `auth_worker.py` y `chat_worker.py` con alias `AuthWorker` y `ChatWorker` para salvaguardar cualquier import legacy.
- **Exportación Limpia**: Se actualizó [`backend/workers/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/__init__.py) y [`main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py) para que toda la suite de workers utilice nomenclatura unificada y coherente con `twitch_auth_worker`, `twitch_chat_worker`, `youtube_chat_worker` y `tiktok_chat_worker`.

### 4.18. Filtrado Estricto de Recompensas Disponibles en el Asistente de Configuración
- **Corrección en `RewardsConfigWizard` (`rewards_dialog.py`)**: Se eliminó un bucle secundario redundante en `_filter_rewards_by_platform()` que volvía a inyectar todas las recompensas remotas de `rewards_details_map` a pesar de que ya estuviesen vinculadas en la base de datos local.
- **Aislamiento Multi-Plataforma**: El menú desplegable muestra exclusivamente los puntos de canal sin vincular pertenecientes a la plataforma seleccionada (Kick o Twitch).
- **Prueba Unitaria de Validación**: Se añadió `test_rewards_config_wizard_excludes_already_linked_rewards` en [`resources/tests/unit/test_twitch_rewards.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/test_twitch_rewards.py).

### 4.19. Purga Dinámica de Puntos de Canal Eliminados al Recargar
- **Sincronización en `RewardsController.update_rewards_list` (`rewards_controller.py`)**: Se eliminó la acumulación infinita de claves en `rewards_details_map` y `current_rewards_list`. Al presionar el botón de recargar o al sincronizar con la API, se purgan las recompensas obsoletas de la plataforma correspondiente antes de incorporar el conjunto actualizado.
- **Propagación en Tiempo Real al Asistente**: `update_active_dialog_rewards` propaga el nuevo mapa limpio hacia `RewardsConfigWizard.update_rewards` para que cualquier recompensa eliminada en Twitch o Kick desaparezca de inmediato del diálogo abierto.
- **Prueba Unitaria de Validación**: Se añadió `test_rewards_controller_update_rewards_list_purges_deleted_rewards` en [`resources/tests/unit/test_twitch_rewards.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/test_twitch_rewards.py).

### 4.20. Eliminación del Congelamiento UI al Navegar a Settings
- **Eliminación de Recálculo Redundante de QSS**: En `SettingsController._load_initial_state()`, se eliminó la emisión de `style_reload_requested(current_font)`. Esta señal forzaba a Qt a re-parsear y re-evaluar los estilos CSS de todo el árbol de widgets de la aplicación cada vez que se abría la vista de ajustes.
- **Apertura Instantánea**: Los estilos solo se recargan cuando el usuario realmente modifica el tamaño de fuente (`handle_font_size`), reduciendo el tiempo de apertura de la vista de ajustes de ~2.0s a ~0.02s.
- **Prueba Unitaria de Validación**: Se añadió [`resources/tests/unit/test_settings_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/test_settings_controller.py) validando que la inicialización no dispare recargas globales de CSS.

---

## 5. Verificación Final

### Pruebas Automatizadas
- Suite completa de pruebas unitarias (`uv run pytest resources/tests/unit/`):
  - **141/141 pruebas superadas al 100%** (`141 passed in 7.01s`).
  - Suites `test_settings_controller.py`, `test_twitch_rewards.py`, `test_tts_online.py`, `test_dashboard_analytics.py`, `test_roles_integrity.py`, `test_twitch_auth.py`, `test_tts_piper_provider.py` y `test_rewards_file_validation.py`.
- Auditoría de paridad e integridad i18n (`uv run python resources/tests/run_tests.py --i18n`):
  - **3/3 pruebas superadas al 100%** (`3 passed in 0.74s`).
- Verificación de ejecución del Runner interactivo (`resources/tests/run_tests.py --unit`):
  - **141 pruebas ejecutadas exitosamente**.
