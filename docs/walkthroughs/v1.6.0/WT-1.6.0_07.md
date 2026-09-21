# Walkthrough - Estandarización Global de Botones (action_outlined vs action_accent)

## Novedades
- **Estandarización Unificada de Botones Neutros (`action_outlined`)**: Se estableció `action_outlined` como el estándar global único para todos los botones secundarios, acciones utilitarias y filas de configuración en toda la interfaz de usuario, eliminando la duplicidad con el rol heredado `action_neutral_border`.

## Mejoras
- **Jerarquía Visual y Reducción del Ruido en [`SettingsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py)**:
  - Se modificó `btn_update` (Buscar actualizaciones) y `btn_feedback` (Reportar error) de `action_accent` a `action_outlined`, alineándolos con la estética sobria de las filas de opciones y evitando que compitan visualmente con los botones de confirmación principales.
  - Se migraron los botones de respaldo (`btn_export` y `btn_import`) y el selector de navegador (`btn_browse_browser`) a `action_outlined`.
  - Se unificó el estado desconectado de las integraciones de plataformas (`btn_kick_integration`, `btn_twitch_integration`, `btn_youtube_integration`, `btn_tiktok_integration`) a `action_outlined`, tanto en la construcción inicial como en `update_integrations_status`.
- **Estandarización en Componentes y Paneles**:
  - [`OverlayCard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/overlay_card.py): Se cambió `btn_copy_url` de `action_accent` a `action_outlined`, unificando su comportamiento con el resto de botones de copia de URL de la aplicación.
  - [`BotMute`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/bot_mute.py): Se cambiaron `btn_add_bot` y `btn_add_word` de `action_accent` a `action_outlined`.
  - [`ChatOverlaySettings`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/overlay_settings.py): Se migró `btn_copy_overlay_obs` a `action_outlined`.
  - [`TtsSettings`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py) y [`PiperVoiceItem`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/piper_voice_item.py): Se migraron los botones de prueba de audio (`btn_test`) a `action_outlined`.
  - [`PlayerSettings`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/player_settings.py): Se migraron `btn_play_pause`, `btn_skip` y `btn_copy_music_url` a `action_outlined`.
  - [`ScheduleFormPanel`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/schedule/schedule_form_panel.py): Se migró `btn_now` a `action_outlined`.
  - [`WidgetCard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/widgets/widget_card.py): Se migraron los botones de reset (`btn_reset`) y copia de overlay (`btn_copy_obs`) a `action_outlined`.
  - [`LogsControls`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/log/logs_controls.py): Se migraron todos los botones de la barra de control de logs a `action_outlined`.
- **Estandarización en Vistas y Diálogos**:
  - [`RewardsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py) y [`DashboardView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py): Se migraron `btn_copy_url`, botones de reproducción de prueba y `btn_open_channel` a `action_outlined`.
  - [`PiperDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/piper_dialog.py): Se actualizaron `btn_reset_synthesis`, `btn_import` y `btn_close` a `action_outlined`.
  - [`ReleaseNotesDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/release_notes_dialog.py): Se migró `btn_github` a `action_outlined`.
  - [`ImportBackupDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/import_backup_dialog.py): Se migraron `btn_select_all`, `btn_deselect_all` y `btn_cancel` a `action_outlined`, manteniendo `btn_confirm` como el único CTA afirmativo con `action_accent`.
  - [`RewardsDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/rewards_dialog.py): Se migraron `btn_refresh`, `btn_browse` y `btn_visual` a `action_outlined`.

## Correcciones
- **Eliminación de la Sobreexposición de `action_accent`**: Se corrigió el uso indebido de `action_accent` (verde primario sólido) en botones de descarte/cierre (`btn_close`), enlaces informativos externos (`btn_github`), campos de texto auxiliares y filas de configuración general. Ahora `action_accent` queda estrictamente reservado para acciones de guardado, envío, confirmación afirmativa y botones principales de creación en tablas (`TableWidget`).
