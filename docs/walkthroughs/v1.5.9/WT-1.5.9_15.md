# Walkthrough v1.5.9 - WT-1.5.9_15: Supresión de Advertencias Nativas de FFmpeg y Estabilización de Seek

En esta iteración se abordó el diagnóstico y resolución de las advertencias del decodificador nativo de audio FFmpeg (`env_facs_q ... is invalid` y `noise_facs_q ... is invalid`) emitidas a la terminal durante saltos repetidos de reproducción en el scrubber musical.

---

## 1. Novedades
*(No se introdujeron nuevas funcionalidades de cara al usuario final en esta iteración de mantenimiento y depuración).*

---

## 2. Mejoras
- **Silenciamiento Nativo de FFmpeg a nivel C (`AV_LOG_FATAL`)**:
  - En [app_logger_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_logger_core.py), se ajustó el nivel de log en `_silence_ffmpeg_native_logging()` de `16` (`AV_LOG_ERROR`) a `8` (`AV_LOG_FATAL`). Esto suprime las advertencias no-fatales de resincronización de paquetes y descarte de micro-frames intermedios emitidas directamente por la librería nativa `avutil-59.dll` hacia `stderr`.
  - En [main.py](file:///c:/Users/TheAn/Desktop/python/Kick/main.py), se actualizó `AV_LOG_LEVEL = "fatal"` y se reforzó `QT_LOGGING_RULES` incorporando comodines completos (`qt.multimedia.*=false;qt.multimedia.ffmpeg.*=false`) para asegurar que la consola permanezca limpia de trazas no deseadas de multimedia.

---

## 3. Correcciones
- **Validación y Clamping de Límites en Seek**:
  - En [youtube_provider.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_provider.py), se blindó el método `seek()` para validar de forma defensiva la existencia de la instancia del reproductor y asegurar el acotamiento de posiciones en el intervalo $[0, \text{duration}]$, evitando llamadas inválidas a `setPosition()`.
- **Compatibilidad y Pruebas Unitarias**:
  - Se incorporó la prueba unitaria `test_music_controller_handle_seek` en [test_music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/backend/controllers/test_music_controller.py), verificando la delegación limpia hacia el proveedor de audio.
  - Se actualizó [test_vertical_layout.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/live/test_vertical_layout.py) para proteger su ejecución en el descubrimiento de tests de pytest.

---

## Verificación de Calidad

| Prueba | Comando | Resultado |
| :--- | :--- | :--- |
| **Nivel activo de avutil** | `uv run python -c "..."` | `Active avutil log level: 8` |
| **Pruebas de Controlador y Provider de Música** | `uv run pytest resources/tests/backend/providers/test_music_audio_hotplug.py resources/tests/backend/controllers/test_music_controller.py` | 15 pasadas (100%) |
| **Pruebas de UI y Componentes** | `uv run pytest resources/tests/frontend` | Todas pasadas |
