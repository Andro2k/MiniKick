# Walkthrough - MiniKick v1.6.0 #32: Autostart Nativo del Sistema y Conexión Fluida Asíncrona (Kick + Twitch)

## Novedades
- **Autostart como Estándar del Sistema**:
  - La conexión automática de plataformas se convirtió en una característica nativa, estándar y transparente del sistema.
  - Al iniciar MiniKick, las plataformas que cuenten con credenciales válidas o canales configurados (Kick, Twitch, YouTube, TikTok) inician su conexión de forma automática sin requerir intervención manual ni conmutadores en la interfaz.

## Mejoras
- **Limpieza y Armonización Visual del Dashboard (`dashboard_view.py`)**:
  - Se eliminó el conmutador `sw_autostart` y la fila de configuración `row_autostart` de la tarjeta principal en [dashboard_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py), presentando una cuadrícula de plataformas directa y sin redundancias.
  - Se retiraron las importaciones no utilizadas `SettingRow`, `ModernSwitch` y `MARGIN_SETTING_ROW_COMPACT`.
- **Escalonamiento Asíncrono de Conexión en el Arranque (`main_window_core.py`)**:
  - Se eliminó la inicialización simultánea agresiva de plataformas en el milisegundo cero, introduciendo un escalonamiento no bloqueante con temporizadores de un solo disparo (`QTimer.singleShot`):
    - Kick: Inmediato ($0\text{ ms}$).
    - Twitch: $350\text{ ms}$.
    - YouTube: $700\text{ ms}$.
    - TikTok: $1000\text{ ms}$.
  - Esto evita saturación del runtime de Python, colisión de hilos y picos de uso en el bucle de eventos principal.
- **Saneamiento de Diccionarios de Internacionalización (i18n)**:
  - Eliminadas las claves `autostart_title` y `autostart_desc` de [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) y [locale_defaults.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/locale_defaults.py), manteniendo una paridad del 100%.

## Correcciones
- **Erradicación del Lag en Notificaciones Toast y Bloqueo de UI**:
  - Se eliminó la llamada síncrona `fetch_full_channel_info()` (que ejecutaba hasta 3 peticiones HTTP bloqueantes a la API Helix de Twitch: `fetch_user_data`, `fetch_channel_followers`, `get_channel_metadata`) directamente en el hilo principal de Qt dentro de `_on_twitch_connected`. Ahora se utiliza de forma inmediata el diccionario `user_data` previamente recopilado en segundo plano por `TwitchChatWorker`.
  - Se eliminó la resolución síncrona de `broadcaster_id` en `_fetch_twitch_rewards()`. Ahora [FetchRewardsWorker](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/rewards_worker.py) resuelve de forma autónoma el `broadcaster_id` en su propio hilo secundario si no ha sido suministrado, liberando al hilo principal de cualquier espera de red.
  - Como resultado, las animaciones de entrada y deslizamiento de los Toasts en [ToastManager](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py) se ejecutan a 60 FPS estables sin congelamientos ni saltos visuales.
- **Pruebas y Verificación**:
  - Suite de pruebas completa: **50/50 pruebas pasadas exitosamente** (`pytest`).
  - Auditoría AST: 0 parámetros huérfanos (`unused_parameter_manager.py`), 0 código muerto (`dead_code_manager.py`) y 66/66 roles y 20/20 estados QSS sincronizados (`role_manager.py -v`).
