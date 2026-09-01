# Walkthrough: Resolución del Error COM 0x8001010d (RPC_E_WRONG_THREAD) en Hilos de Audio

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_14.md`  
**Módulos Modificados:**
- [`backend/providers/voices/tts_local.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_local.py)
- [`backend/workers/voice_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/voice_worker.py)
- [`backend/services/chat/tts_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/tts_service.py)
- [`backend/providers/voices/tts_online.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py)

---

## 1. Resumen de Cambios

### A. Eliminación de Desinicialización Destructiva de COM
- En [`tts_local.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_local.py), se eliminó la llamada a `CoUninitialize()` que invalidaba los punteros internos de SAPI5 cacheados por `pyttsx3`.
- Se implementó `_init_com()` idempotente y seguro contra invocaciones múltiples.

### B. Inicialización Explícita de Apartamento COM en Hilos Secundarios
- Se aseguró la llamada a `pythoncom.CoInitialize()` al inicio de cada hilo de ejecución de audio:
  - [`VoiceFetcherWorker.run()`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/voice_worker.py#L18)
  - [`TTSManager._worker()`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/tts_service.py#L141)
  - [`WebTTSProvider._run_event_loop()`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py#L80)

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/ -q --tb=short
```
- **145/145 pruebas unitarias aprobadas al 100%**.
