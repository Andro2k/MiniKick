# Walkthrough v1.5.9 - WT-1.5.9_16: Saneamiento del Ciclo de Vida de Hilos y Prevención de Excepciones de Acceso en Tests

En esta iteración se abordó el diagnóstico y corrección de la excepción de violación de acceso de memoria (`0xC0000005` / SegFault) capturada por `faulthandler` en `minikick_crash.log` durante la ejecución en lote de la suite de pruebas automatizadas.

---

## 1. Novedades
*(No se introdujeron nuevas funcionalidades de cara al usuario final en esta iteración de infraestructura y saneamiento de pruebas).*

---

## 2. Mejoras
- **Apagado Limpio y Determinista en `WebTTSProvider`**:
  - En [online_provider.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/online_provider.py), se refactorizó `shutdown()` para verificar si el bucle asyncio no está cerrado (`not self._loop.is_closed()`), invocar `self._loop.stop()` a través de `call_soon_threadsafe`, y esperar de forma determinista la finalización del hilo (`self._loop_thread.join(timeout=1.0)`).
  - Se agregó `__del__()` como red de seguridad para garantizar que cualquier instancia descartada por el recolector de basura de Python ejecute `shutdown()` automáticamente.
- **Doble Drenado Protegido en `conftest.py`**:
  - En [conftest.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/conftest.py), se amplió el fixture `qt_drain` para procesar la cola de eventos de Qt (`processEvents()`) tanto en el setup previo como en el teardown posterior de cada prueba, envolviendo las llamadas en bloques protegidos contra excepciones. Esto garantiza que ningún evento asíncrono o `deleteLater()` se desborde hacia pruebas posteriores.

---

## 3. Correcciones
- **Eliminación de Hilos Huérfanos en Tests de TTS**:
  - En [test_tts_online.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/backend/providers/test_tts_online.py), se introdujo el fixture `tts_provider` con cierre automático (`yield` + `shutdown()`), eliminando la fuga de múltiples hilos en segundo plano (`WebTTSAsyncLoop`) que persistían ejecutándose en el proceso de pytest.
  - Se añadió la prueba unitaria `test_web_tts_provider_shutdown` para certificar que el hilo del proveedor se detiene inmediatamente tras invocar `shutdown()`.

---

## Verificación de Calidad

| Prueba | Comando | Resultado |
| :--- | :--- | :--- |
| **Pruebas de TTS Online con Shutdown** | `uv run pytest resources/tests/backend/providers/test_tts_online.py` | 7 pasadas (100% éxito) |
| **Pruebas Combinadas de Providers** | `uv run pytest resources/tests/backend/providers/test_tts_online.py resources/tests/backend/providers/test_youtube_chat.py` | 16 pasadas (0 errores, 0 access violations) |
| **Pruebas de Música y Scrubber** | `uv run pytest resources/tests/backend/providers/test_music_audio_hotplug.py resources/tests/backend/controllers/test_music_controller.py` | 15 pasadas (100% éxito) |
