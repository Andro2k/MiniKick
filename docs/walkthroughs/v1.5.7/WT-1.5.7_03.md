# Walkthrough: Blindaje de Concurrencia en QThreads, Prevención de Access Violation (0xC0000005) y Resiliencia en Servicios (Twitch / Audio COM / TTS)

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_03.md`  
**Módulos Involucrados:**
- `backend/core/main_window_core.py`
- `backend/workers/twitch_auth_worker.py`
- `backend/workers/rewards_worker.py`
- `backend/services/chat/tts_service.py`
- `backend/providers/voices/` (TTS providers)
- `backend/providers/music/youtube_client.py`

---

## 1. Resumen de Objetivos y Cambios

### A. Prevención de Fallos Críticos por Access Violation (`0xC0000005`)
- **Causa Raíz:** Concurrencia insegura al destruir o finalizar hilos `QThread` mientras el bucle nativo de C++ (`QEventLoop`) seguía despachando señales pendientes o invocando `deleteLater()` concurrentemente.
- **Solución:**
  - Implementación del método de apagado paralelo seguro `_stop_workers_parallel()` en `MainWindowCore`.
  - Desconexión preventiva de señales antes de `requestInterruption()`, `quit()` y espera acotada con `wait(1000-2000ms)`.

### B. Inicialización Asíncrona y Resiliencia en Sesión de Twitch
- **Problema:** Al expirar el token de Twitch o fallar la red al inicio, la validación síncrona bloqueaba el hilo principal de la interfaz o disparaba excepciones no controladas.
- **Solución:**
  - Migración a autenticación en segundo plano mediante `TwitchAuthWorker`.
  - Captura controlada de tokens inválidos con revocación limpia y notificación visual sin interrumpir la operación de Kick ni del reproductor.

### C. Resolución del Error COM `0x8001010d` (`RPC_E_WRONG_THREAD`) en Audio y TTS
- **Problema:** Los motores de voz locales SAPI5 / Windows Speech Engine arrojaban excepciones COM al inicializarse o invocarse a través de diferentes hilos de Qt.
- **Solución:**
  - Inicialización y liberación explícita de `pythoncom.CoInitialize()` y `pythoncom.CoUninitialize()` en cada ciclo de vida del hilo de síntesis de voz.

### D. Protección de Concurrencia en `FetchRewardsWorker`
- Prevención de ejecuciones superpuestas al consultar la API de recompensas de Twitch mediante flags atómicos `_is_fetching` y reintentos exponenciales con límite de fallo.

---

## 2. Verificación
- Pruebas unitarias de concurrencia y sockets en `resources/tests/unit/providers/` y `resources/tests/unit/workers/` pasando al 100%.
- Múltiples ciclos continuos de inicio, suspensión y cierre de la aplicación sin advertencias ni cierres inesperados.
