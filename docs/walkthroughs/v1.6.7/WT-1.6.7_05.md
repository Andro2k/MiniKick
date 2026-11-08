# Walkthrough Técnico — MiniKick v1.6.7 (Paso 05)

Se mejoró cómo suenan los mensajes leídos con las voces Piper (todas en español y fonemizadas con espeak-ng) y se añadió una pausa entre mensajes consecutivos del TTS, que antes se encadenaban sin respiro. Se comprobó con el mismo fonemizador que usa Piper qué palabras comunes del chat se pronuncian mal y se definió su forma hablada. Módulos afectados: utilidades de texto, filtro de chat, controlador de chat y gestor de TTS.

---

## Novedades

- Nuevo módulo `backend/utils/speech_text.py` con `apply_pronunciations`, `normalize_symbols_for_speech` y `speakable_username`, exportados desde `backend.utils`.
- Diccionario de pronunciación (`SPEECH_REPLACEMENTS`) para abreviaturas del chat en español (`q`, `xq`, `pq`, `tmb`, `xfa`, `dnd`, `ntp`, `salu2`, entre otras) y términos de streaming y videojuegos en inglés (`gg`, `gl`, `hf`, `afk`, `stream`, `streamer`, `follow`, `followers`, `raid`, `hype`, `noob`, `like`, `hater`, `build`, `loot`, `feed`, `gameplay`, entre otros). Cada forma hablada se contrastó con la salida fonética de espeak-ng; por ejemplo `gg` sonaba como "je je", `follow` como "foyow" y `hype` perdía la h.
- Pausa de 0.7 s entre mensajes consecutivos del TTS (`DEFAULT_MESSAGE_GAP_S` y `TTSManager.set_message_gap`).
- `ChatFilterHandler.build_spoken_text`, que arma la frase final con el nombre ya limpio.

## Mejoras

- `clean_message_for_tts` quita el símbolo de menciones y hashtags al inicio de palabra (`@juan` se lee "juan", `#1` se lee "1"), convierte los guiones bajos internos en espacios y aplica el diccionario. Los correos y símbolos sueltos no se modifican.
- Los nombres de usuario se leen sin decoración `xX_..._Xx`, con separadores y CamelCase convertidos en palabras (`ProGamer` se lee "Pro Gamer") y sin colas de tres o más dígitos (`Juan2005` se lee "Juan"). Si la limpieza deja el nombre vacío se usa el original.
- Los dos puntos donde se construía la frase "usuario dice: mensaje" (mensajes normales y comando de TTS) comparten ahora `build_spoken_text`.
- La pausa se aplica en el gestor, por lo que funciona con todos los proveedores de voz. No se aplica al primer mensaje tras un silencio, la espera se interrumpe al llamar a `stop()` y descarta el mensaje pendiente, y el atenuado de música sigue activo durante la pausa.
- La prueba `test_chat_controller_pipeline_tts_execution` se actualizó porque fijaba el comportamiento anterior (nombre con dígitos y "stream" sin cambios).

## Correcciones

- Los mensajes de distintos usuarios se leían uno detrás de otro sin pausa.
- `gg`, `follow`, `hype`, `q`, `xq` y otras abreviaturas se pronunciaban de forma incorrecta o se deletreaban.
- Los nombres con decoración, guiones bajos o números largos se leían letra por letra o como cifras enormes.

> [!IMPORTANT]
> Los valores de pausa (0.7 s) y las formas habladas del diccionario se eligieron a partir de la salida del fonemizador y no se evaluaron escuchando el audio. La pausa no tiene control en la interfaz todavía. No se modificaron los parámetros de síntesis de Piper (velocidad y variación), que el servicio ya guarda y aplica.

> [!NOTE]
> Las sustituciones afectan a todas las apariciones de la palabra, también en frases en inglés leídas por una voz en español.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `resources/tests/test_tts_speech_text.py` (nuevas: diccionario, símbolos, nombres, constructor de frase y pausa, incluida una prueba con el hilo real del gestor) | 39 aprobadas |
| Pruebas de TTS, controlador de chat, workers, anti-spam, arquitectura, parámetros sin usar, imports perezosos y ruta de mensajes sobre el commit `d7b5aee` más este cambio | 132 aprobadas, 3 fallidas |
| Pruebas fallidas | Tres de `test_giphy_and_tts_filter.py` (requieren API key de Giphy y red); fallan igual sin este cambio |
| Todos los archivos de `resources/tests` ejecutados por separado, antes y después | Sin regresiones; las diferencias son archivos de interfaz que se caen o fallan en el entorno de verificación en ambos casos |
| Suite rápida de auditorías de calidad | 11 de 12 aprobadas; falla Project Translation Keys por la clave `music.youtube.com` en `backend/utils/youtube_url.py`, ajena a este paso |
| Entorno | Python 3.12 en la verificación; el proyecto declara 3.14. Se verificó la fonemización, no se reprodujo audio |
