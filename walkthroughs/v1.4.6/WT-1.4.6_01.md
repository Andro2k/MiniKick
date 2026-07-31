# Walkthrough v1.4.6 - Prevención de Crash en Cascada por Disco Lleno, Sanitización de Emojis/Símbolos en Web TTS y Corrección de WinError 5 en Descargas yt-dlp

**Fecha:** 30 de Julio, 2026  
**Versión Target:** v1.4.6  
**Ubicación del Documento:** `c:\Users\TheAn\Desktop\python\Kick\walkthroughs\v1.4.6\WT-1.4.6_01.md`

---

## 1. Resumen de Cambios

En esta versión (v1.4.6) se resuelven tres fallos críticos identificados a partir de los análisis de registros de producción (`minikick.log`):

- **Prevención de Crash en Cascada por Disco Lleno (`[Errno 28]` / `AttributeError`)**:
  - **Manejador de Consola Seguro en `StreamToLogger`**: En ejecuciones compiladas de GUI en Windows (`pythonw` / PyInstaller), `sys.__stderr__` es `None`. Se añadió una comprobación preventiva en [log_handler.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/log_handler.py#L30-L38) para evitar excepciones no capturadas `AttributeError: 'NoneType' object has no attribute 'write'`.
  - **Eliminación de Bucles de Registro Recursivo**: En [log_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/log_service.py#L42-L68), se reemplazó el uso de `print()` dentro de los bloques de excepción de SQLite por escrituras seguras a `sys.__stderr__`. Esto evita la reentrada al despachador de logs cuando el almacenamiento de disco está lleno (`[Errno 28] No space left on device`).
  - **Corrección de Sangría en Sintaxis Python**: Se ajustó la alineación de sangría del bloque `try/except` en [log_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/log_service.py#L60-L68), solucionando los errores de análisis sintáctico.

- **Sanitización y Filtrado de Texto en Motor Web TTS (`edge-tts`)**:
  - **Validación Prevención `No audio was received`**: Implementación de `_is_speakable_text()` en [tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py#L26-L70).
  - **Filtrado de Emojis y Símbolos Solos**: Se omiten automáticamente las peticiones de síntesis de voz si el mensaje del chat consiste únicamente de símbolos (ej: `??`, `ð`), emojis o caracteres invisibles/especiales Unicode (ej: `\ufffc`). Evita llamadas fallidas a la API remota.

- **Prevención de Error de Permisos en Windows al Descargar Canciones (`[WinError 5] Acceso denegado`)**:
  - **Descarga Directa sin Archivos `.part`**: Configuración de `'nopart': True` en `ydl_opts` dentro de [music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py#L50-L61).
  - **Eliminación de Bloqueos de Renombrado**: Al escribir directamente en el archivo de salida final, se elimina el paso de renombrado `.part` -> `.mp4` que solía ser bloqueado por el antivirus o el indizador de archivos de Windows.

---

## 2. Detalles de las Correcciones Implementadas

### A. Manejo de Excepciones en Sistema de Logging
- **Archivos:** [log_handler.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/log_handler.py), [log_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/log_service.py)
- **Cambio:** `StreamToLogger.write()` valida si `sys.__stderr__ is not None` antes de escribir. `LogService` no llama a `print()` cuando ocurren errores de conexión o I/O en SQLite.

### B. Validación de Texto Pronunciable en Web TTS
- **Archivo:** [tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py)
- **Cambio:** Incorporación del método estático `_is_speakable_text(text: str) -> bool` utilizando expresiones regulares Unicode (`re.sub(r'[^\w\s]', '', text)`). `prepare()` y `speak()` descartan de forma transparente textos no hablados.

### C. Deshabilitación de Archivos Parciales `.part` en yt-dlp
- **Archivo:** [music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py)
- **Cambio:** Inclusión del parámetro `'nopart': True` en el diccionario de configuración `ydl_opts` para evitar que Windows arroje `[WinError 5] Acceso denegado`.

---

## 3. Archivos Modificados

- [frontend/common/log_handler.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/log_handler.py)
- [backend/services/system/log_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/log_service.py)
- [backend/providers/voices/tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py)
- [backend/workers/music_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/music_worker.py)

---

## 4. Plan de Verificación y Compilación

- **Compilación de Sintaxis Python**: `python -m py_compile` ejecutado exitosamente en los 4 módulos modificados.
- **Sin Errores de Sintaxis en IDE**: Resueltos todos los reportes de parseo sintáctico en `log_service.py`.
