# Walkthrough: Blindaje de QThreads y Eliminación de Access Violation (0xC0000005)

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_11.md`  
**Módulos Modificados:**
- [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)
- [`backend/providers/music/youtube_client.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py)
- [`backend/workers/rewards_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/rewards_worker.py)
- [`backend/workers/timers_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/timers_worker.py)
- [`backend/workers/schedule_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/schedule_worker.py)

---

## 1. Resumen de Cambios

### A. Eliminación de `terminate()`
- Se eliminaron por completo las llamadas a `instance.terminate()` que causaban corrupción de memoria en C++ / Access Violation cuando un hilo no terminaba inmediatamente.
- Se implementó el patrón de parada cooperativa segura: `instance.requestInterruption()`, `instance.stop()`, `instance.wait(2000)` y `instance.deleteLater()`.

### B. Desacoplamiento de `QThread` del Árbol GUI (`parent=self`)
- Se removió `parent=self` en la instanciación de todos los workers (`TimerWorker`, `RewardWorker`, `FetchRewardsWorker`, `KickChatWorker`, `TwitchChatWorker`, `TwitchAuthWorker`, `TwitchRewardWorker`, `ScheduleWorker`, `YouTubeChatWorker`, `TikTokChatWorker`).
- Esto evita que el Garbage Collector y el ciclo de vida de la ventana principal intenten destruir o iterar sobre hilos en ejecución.

### C. Respuesta Inmediata a la Parada (< 50ms)
- En `RewardWorker`, `TimerWorker` y `ScheduleWorker`, los bucles de espera se redujeron a micro-bloques de 50ms chequeando continuamente `self.isInterruptionRequested()` y `self._running`.

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/ -q --tb=short
```
- **145/145 pruebas unitarias aprobadas al 100%**.
