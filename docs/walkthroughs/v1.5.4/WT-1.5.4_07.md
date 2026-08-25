# Walkthrough WT-1.5.4_07: Optimización de Rendimiento y Eliminación de Lag en Piper TTS

## 1. Resumen de la Tarea

Se optimizó la inicialización, cambio de proveedor y gestión de memoria del motor de voz neuronal **Piper TTS**, resolviendo el bloqueo/congelamiento momentáneo ("lag") de la interfaz gráfica al seleccionarlo en la vista de chat y la demora al arrancar la aplicación cuando Piper era el proveedor activo.

---

## 2. Arquitectura & Principios Aplicados

1. **Non-Blocking Asynchronous Engine Init (High Concurrency)**:
   - La carga inicial de los binarios y dependencias pesadas de ONNX Runtime (`onnxruntime`, C++ DLLs) se aisló en hilos en segundo plano (`threading.Thread(..., daemon=True)`), liberando por completo el hilo principal de la UI (Qt Main Thread).
2. **Granular Signal Blocking en UI (`ChatTtsSettingsPanel`)**:
   - `set_settings_ui` ahora bloquea explícitamente las señales de todos los widgets interactivos hijos (`combo_provider`, `slider_vol`, `slider_speed`, switches) dentro de un bloque `try...finally`, previniendo cascadas de eventos no deseados y arranques redundantes de workers durante la inicialización de la ventana.
3. **Deduplicación de Tareas de Precalentamiento (`_warming_up_voices`)**:
   - Se implementó un conjunto de control atómico `_warming_up_voices: set[str]` y verificación temprana sobre `_loaded_models` en [tts_piper.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_piper.py), eliminando ejecuciones redundantes de síntesis y contención de hilos.
4. **Lazy Provider Resolution en `TTSManager`**:
   - `TTSManager.get_available_voices()` ahora invoca directamente `_get_provider(provider_type)` de manera perezosa, evitando instanciar proveedores no solicitados.

---

## 3. Archivos Modificados

- [backend/providers/voices/tts_piper.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_piper.py):
  - Deduplicación de `warm_up()` con `_warming_up_voices` y chequeo de `_loaded_models`.
  - Eliminada la descarga síncrona bloqueante en `_get_or_load_voice()`.
- [backend/services/chat/tts_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/tts_service.py):
  - `warm_up("piper")` asíncrono no bloqueante en hilo demonio.
  - Resolución directa y perezosa en `get_available_voices()`.
- [frontend/components/chat/tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py):
  - Bloqueo granular de señales en `set_settings_ui()` para todos los widgets de control.
- [tests/unit/test_tts_piper_provider.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/unit/test_tts_piper_provider.py):
  - Pruebas unitarias de deduplicación de precalentamiento y carga en caché.

---

## 4. Verificación de Pruebas Unitarias

```powershell
uv run pytest
```
```
============================= 91 passed in 4.13s ==============================
```
- **91 pruebas unitarias** ejecutadas y aprobadas al 100%.
