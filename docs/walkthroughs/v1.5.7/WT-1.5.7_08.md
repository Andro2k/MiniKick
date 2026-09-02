# Walkthrough - WT-1.5.7_08: Validación y Restricción de Plataformas en Rewards, Comandos, Timers, Filtros Anti-Spam e Información del Stream (Schedule)

## Contexto y Motivación
Se implementó un sistema de control reactivo sobre el estado de autenticación y vinculación de plataformas (**Kick**, **Twitch**, **YouTube**, **TikTok**) para impedir la creación o edición desincronizada de recompensas de canal (Channel Points), comandos personalizados, temporizadores (Timers), filtros anti-spam y programación/cambio rápido de información del stream (Schedule) cuando las plataformas no se encuentran vinculadas/activas.

---

## Cambios Implementados

### 1. Recompensas de Canal (`RewardsConfigWizard`, `RewardsView`, `RewardsController`)
- **Control de Plataformas**: En el paso 1 del asistente de recompensas, los botones de opción (Radio Buttons) para **Kick** y **Twitch** ahora se habilitan **únicamente si la plataforma respectiva está autenticada**.
- **Herramientas descriptivas y avisos**: Si una plataforma está desconectada, se muestra un tooltip informativo (`platform_kick_offline` / `platform_twitch_offline`).
- **Aviso Global de Desconexión**: Si ninguna de las dos plataformas está vinculada, se despliega una tarjeta de advertencia bloqueando el avance al paso 2 hasta que se vincule una cuenta en el Dashboard.
- **Modo Edición Protegido**: Al editar una recompensa asociada a una plataforma que actualmente está desconectada, se bloquean los campos de la API remota (nombre, costo, prompt, color) y se permite únicamente la edición de la alerta multimedia local.

### 2. Comandos de Chat (`CommandConfigWizard`, `CommandView`, `CommandController`, `CommandService`)
- **Filtro de Plataformas Conectadas**: En la pestaña avanzada del asistente de comandos, las casillas de Kick, Twitch, YouTube y TikTok se activan o desactivan según el estado reportado por `connected_platforms`.
- **Renderizado Dinámico en la Tabla**: En `CommandView._create_platforms_cell()`, los iconos de plataformas reflejan exclusivamente aquellas que están **activas y conectadas**, ocultando las plataformas desconectadas o mostrando `-` si ninguna está disponible.
- **Valores Iniciales Reactivos**: Al crear un comando nuevo, solo se marcan activas aquellas plataformas que se encuentran vinculadas.
- **Emisión Segura de Mensajes**: En `CommandService.send_response()`, se valida `is_authenticated()` en el cliente de Kick y que el worker de Twitch esté activo antes de realizar peticiones de chat.

### 3. Temporizadores de Chat (`TimerConfigWizard`, `TimerView`, `TimerController`)
- **Interruptores de Plataforma en el Asistente**: Los interruptores de Kick y Twitch en el asistente de timers se habilitan únicamente para plataformas activas.
- **Renderizado Dinámico en la Tabla**: En `TimersView._create_platforms_cell()`, la celda de plataforma evalúa el estado real en `connected_platforms`. Si un timer tiene habilitadas ambas plataformas pero solo Kick está conectado, muestra `Kick`; si solo Twitch está conectado, muestra `Twitch`; si ambas están conectadas, muestra `Ambas`; y si ninguna está conectada, muestra `-`.
- **Sincronización Reactiva**: `TimersView` implementa `set_connected_platforms()` y `TimerController.load_initial_data()` inyecta `connected_platforms_provider`, mientras que `MainWindowCore._update_integrations_status_ui` actualiza la vista reactivamente ante cualquier cambio de estado.
- **Carga de Configuración Existente**: Al editar un timer, se respetan las plataformas vinculadas y se deshabilitan aquellas desconectadas.

### 4. Filtros Anti-Spam / Auto-Mod (`SpamView`, `ExpandableSettingCard`, `SpamController`)
- **Interruptores de Plataforma en Tarjetas de Configuración**: En `ExpandableSettingCard`, los switches de Kick y Twitch se habilitan únicamente para plataformas conectadas, desactivándose con tooltip explicativo si la plataforma no está vinculada.
- **Carga y Guardado Consistente**: `set_data()` respeta el estado de conexión de cada plataforma antes de marcar los switches.
- **Sincronización en Vivo**: `SpamView` y `SpamController` reciben `connected_platforms_provider` y reaccionan en vivo ante vinculaciones o desconexiones.

### 5. Información del Stream y Horarios (`ScheduleView`, `QuickChangePanel`, `ScheduleFormPanel`, `ScheduleController`)
- **Cambio Rápido de Stream**: En `QuickChangePanel`, los interruptores de Kick y Twitch se habilitan y marcan solo si la plataforma correspondiente está conectada; de lo contrario, se desactivan con tooltip informativo y se deshabilita el botón de aplicar si no hay plataformas activas.
- **Formulario de Horarios**: En `ScheduleFormPanel`, los switches de Kick y Twitch y las cajas de búsqueda de categorías solo se habilitan para plataformas conectadas.
- **Sincronización en Tiempo Real**: Al vincular o desvincular cuentas en `MainWindowCore`, `ScheduleView`, `SpamView` y `CommandView` se actualizan reactivamente.

### 6. Internacionalización Estricta (i18n)
- Se agregaron todas las nuevas claves en `locales/es.json` y `locales/en.json` respetando el estándar sin cadenas hardcodeadas:
  - `rewards.dialogs.wizard.step1.platform_kick_offline`
  - `rewards.dialogs.wizard.step1.platform_twitch_offline`
  - `rewards.dialogs.wizard.step1.no_platforms_connected`
  - `rewards.dialogs.wizard.step1.edit_offline_warning`
  - `command.dialog.platform_offline`
  - `timer.dialog.platform_offline`
  - `spam.card.platform_offline`
  - `stream_info.quick_change.platform_offline`

---

### 7. Sincronización de Recompensas, Aislamiento de Plataformas y Manejo de 404 (Recompensas Eliminadas Remotamente)
- **Aislamiento Estricto de Plataformas**: Se corrigió `RewardsController.update_rewards_list` y `RewardsConfigWizard.get_config_data` para garantizar que las recompensas de Kick y Twitch no muten de plataforma ni sobreescriban propiedades cruzadas. En modo edición, la plataforma se preserva de manera inmutable de la configuración guardada.
- **Manejo de Recompensas Eliminadas en la Web (404 Not Found)**:
  - En `RewardsController._on_reward_update_error`, cuando la API de Kick o Twitch responde con `404 Not Found`, se limpia automáticamente el `id` remoto huérfano (`updated_config["id"] = None`) y se guardan los cambios locales de la alerta multimedia.
  - Se notifica al usuario mediante un toast informativo en su idioma (`rewards.status.reward_not_found_on_platform`).
- **Indicadores Visuales de Estado en Tabla (`RewardsView`)**:
  - Si una recompensa tenía ID remoto pero ya no existe en la plataforma remota activa, la columna de plataforma muestra el tag `(Desvinculada)` con icono de advertencia ámbar y tooltip explicativo (`rewards.table.status_unlinked_tooltip`).
  - Si la plataforma se encuentra desconectada, se muestra `(Desconectado)` con icono gris y tooltip explicativo (`rewards.table.status_offline_tooltip`).
- **Nuevas Claves i18n Agregadas**:
  - `rewards.status.reward_not_found_on_platform`
  - `rewards.table.status_unlinked_tag`
  - `rewards.table.status_unlinked_tooltip`
  - `rewards.table.status_offline_tag`
  - `rewards.table.status_offline_tooltip`

---

## Verificación y Calidad

### Pruebas Automatizadas
- `resources/tests/unit/ui/test_dialogs.py`:
  - `test_rewards_config_wizard_platform_gating`
  - `test_command_config_wizard_platform_gating`
  - `test_timer_config_wizard_platform_gating`
- `resources/tests/unit/ui/test_command_ui.py`:
  - `test_command_view_connected_platforms_table_filter`
- `resources/tests/unit/ui/test_schedule_ui.py`:
  - `test_quick_change_panel_platform_gating`
  - `test_schedule_form_panel_platform_gating`
  - `test_schedule_view_set_connected_platforms_delegation`
  - `test_schedule_controller_injects_connected_platforms`
- `resources/tests/unit/ui/test_spam_ui.py`:
  - `test_expandable_setting_card_platform_gating`
  - `test_spam_view_set_connected_platforms`
  - `test_spam_controller_injects_connected_platforms`
- `resources/tests/unit/services/test_rewards_service.py`:
  - `test_rewards_controller_clear_platform_rewards`
  - `test_rewards_controller_platform_isolation_on_update`
  - `test_rewards_controller_404_error_clears_remote_id`
- `resources/tests/unit/services/test_timer_service.py`:
  - `test_timers_view_connected_platforms_table_filter`
  - `test_timer_controller_injects_connected_platforms`
- `resources/tests/unit/services/test_command_service.py`:
  - `test_command_service_unauthenticated_kick_skips`

**Resultado de la Suite Completa**:
```bash
174 passed in 10.92s (100% de éxito)
```
