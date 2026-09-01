# Walkthrough: Corrección del Ciclo de Vida y Prevención de Muerte de Hilos en TTS

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_13.md`  
**Módulos Modificados:**
- [`backend/services/chat/tts_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/tts_service.py)
- [`backend/providers/voices/tts_online.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py)
- [`backend/services/chat/chat_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/chat_service.py)
- [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)

---

## 1. Resumen de Cambios

### A. Separación de `stop()` vs `shutdown()` en `TTSManager`
- Se corrigió `TTSManager.stop()` para que drene las colas pendientes y detenga la reproducción de audio sin insertar el centinela `None`. Los hilos `_downloader_worker` y `_worker` ahora permanecen activos y listos para seguir procesando mensajes tras cualquier parada o pausa.
- Se añadió `TTSManager.shutdown()` exclusivamente para la terminación completa al cerrar la aplicación.

### B. Preservación del Event Loop en `WebTTSProvider`
- Se actualizó `WebTTSProvider.stop()` para detener `QMediaPlayer` y cancelar descargas en caché sin apagar el bucle de eventos `asyncio`.
- Se añadió `WebTTSProvider.shutdown()` para el cierre ordenado de tareas asíncronas.

### C. Desconexión Limpia en `MainWindow`
- Se integró `chat_service.shutdown()` dentro de `_stop_all_workers` en `main_window_core.py`.

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/ -k "tts or chat or pipeline or voice" -q --tb=short
```
- **47/47 pruebas seleccionadas aprobadas al 100%**.
