# Walkthrough WT-1.5.5_09: Auto-Recuperación y Hotplug de Dispositivos de Audio

## 1. Resumen de la Implementación
Se implementó un sistema automático de detección de cambios de hardware de audio (**Audio Hotplug & Auto-Fallback**) para prevenir los bucles de advertencias `AUDCLNT_E_DEVICE_INVALIDATED` en Windows CoreAudio cuando un usuario desconecta sus auriculares o altavoces:
- **Reproductor de Música ([backend/providers/music/youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py)):**
  - Suscripción en tiempo real a la señal `QMediaDevices.audioOutputsChanged`.
  - Conmutación automática instantánea a `defaultAudioOutput()` si el auricular o altavoz configurado es desconectado del sistema operativo.
  - Manejador de error en `_handle_player_error` para recuperar la reproducción fluida si un dispositivo falla durante la reproducción activa.
- **Motores TTS ([backend/providers/voices/tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py) y [backend/providers/voices/tts_piper.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_piper.py)):**
  - Verificación preventiva de existencia de dispositivo antes de reproducir síntesis de voz, con fallback seguro al dispositivo por defecto si el ID ya no existe en el sistema.
- **Twitch WebSocket Keep-Alive ([backend/providers/chat/twitch_websocket.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_websocket.py)):**
  - Habilitado `ping_interval=30, ping_timeout=10` para evitar cortes por inactividad (`WinError 10054`) generados por routers domésticos o balanceadores.

---

## 2. Archivos Modificados

- [backend/providers/music/youtube_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py): Añadido watcher `QMediaDevices` y slot `_on_audio_outputs_changed`.
- [backend/providers/voices/tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py): Auto-fallback preventivo a `defaultAudioOutput()`.
- [backend/providers/voices/tts_piper.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_piper.py): Auto-fallback preventivo a `defaultAudioOutput()`.
- [backend/providers/chat/twitch_websocket.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_websocket.py): Activado heartbeat `ping_interval=30`.
- [resources/tests/unit/test_music_audio_hotplug.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/test_music_audio_hotplug.py): Tests unitarios de auto-fallback.

---

## 3. Verificación Automatizada

- **Pytest:** Ejecución de 98 tests unitarios (`uv run pytest`) $\rightarrow$ **98 pasadas al 100%**.
