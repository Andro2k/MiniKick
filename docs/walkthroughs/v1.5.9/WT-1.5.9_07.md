# 🚶 Walkthrough WT-1.5.9_07: Estandarización de Nombres — Handlers y Providers (Fase 2)

## 🎯 Objetivo y Contexto
Estandarizar y alinear la nomenclatura de los procesadores de eventos (`backend/handlers/`) y de los adaptadores de servicios externos (`backend/providers/`) de acuerdo con la convención oficial `{domain}_handler.py` y `{platform}_provider.py` descrita en [`docs/Correcciones.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/Correcciones.md), eliminando palabras redundantes y prefijos innecesarios sin romper contratos ni suites de prueba.

---

## 🛠️ Cambios Implementados

### 1. Estandarización de Handlers (`backend/handlers/`)
Se renombraron 4 archivos de manejadores de eventos mediante `git mv`:
- `chat_filter_handler.py` ➔ [`backend/handlers/spam_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/spam_handler.py) (dominio centralizado en `spam`)
- `log_handler.py` ➔ [`backend/handlers/logs_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/logs_handler.py) (plural uniforme con controllers y storage)
- `music_command_handler.py` ➔ [`backend/handlers/music_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/music_handler.py) (elimina redundancia "command")
- `tts_voice_handler.py` ➔ [`backend/handlers/tts_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/tts_handler.py) (elimina redundancia "voice")

Actualización de imports:
- [`backend/handlers/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/__init__.py)

### 2. Estandarización de Providers (`backend/providers/`)
Se renombraron 10 archivos de proveedores externos mediante `git mv`:

#### Chat Providers (`backend/providers/chat/`):
- `kick_client.py` ➔ [`backend/providers/chat/kick_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_provider.py)
- `kick_websocket.py` ➔ [`backend/providers/chat/kick_ws_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_ws_provider.py)
- `tiktok_chat_provider.py` ➔ [`backend/providers/chat/tiktok_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/tiktok_provider.py)
- `twitch_client.py` ➔ [`backend/providers/chat/twitch_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_provider.py)
- `twitch_websocket.py` ➔ [`backend/providers/chat/twitch_ws_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/twitch_ws_provider.py)
- `youtube_chat_provider.py` ➔ [`backend/providers/chat/youtube_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/youtube_provider.py)

#### Music Providers (`backend/providers/music/`):
- `youtube_client.py` ➔ [`backend/providers/music/youtube_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_provider.py)

#### Voice/TTS Providers (`backend/providers/voices/`):
- `tts_local.py` ➔ [`backend/providers/voices/local_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/local_provider.py)
- `tts_online.py` ➔ [`backend/providers/voices/online_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/online_provider.py)
- `tts_piper.py` ➔ [`backend/providers/voices/piper_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/piper_provider.py)

Actualización de imports:
- `backend/providers/chat/__init__.py`
- `backend/providers/music/__init__.py`
- `backend/providers/voices/__init__.py`

### 3. Actualización de Puntos de Referencia y Pruebas Unitarias
Se actualizaron todas las referencias e imports en 21 archivos de pruebas y servicios:
- `resources/tests/backend/core/test_logging.py`
- `resources/tests/backend/core/test_diagnostic_telemetry.py`
- `resources/tests/backend/providers/test_tts_local.py`
- `resources/tests/backend/providers/test_tts_online.py`
- `resources/tests/backend/providers/test_tts_piper_provider.py`
- `resources/tests/backend/providers/test_piper_synthesis.py`
- `resources/tests/backend/providers/test_music_audio_hotplug.py`
- `resources/tests/backend/providers/test_youtube_chat.py`
- `resources/tests/backend/providers/test_twitch_websocket.py`
- `resources/tests/backend/providers/test_tiktok_chat.py`
- `resources/tests/backend/providers/test_kick_websocket.py`
- `resources/tests/backend/providers/test_kick_rewards.py`
- `resources/tests/backend/providers/test_kick_auth.py`
- `resources/tests/backend/providers/test_twitch_rewards.py`
- `resources/tests/backend/workers/test_youtube_chat_worker.py`
- `resources/tests/backend/services/test_rewards_service.py`
- `resources/tests/backend/services/test_alert_service.py`
- `resources/tests/backend/services/test_tts_role_filtering.py`
- `resources/tests/backend/controllers/test_music_controller.py`
- `resources/tests/frontend/views/test_dashboard_view.py`
- `resources/tests/live/tiktok_live.py`
- `resources/tests/live/chat_benchmark_live.py`

---

## 🔬 Validación y Pruebas
- **Ejecución de Tests de Providers y Controllers:**
  - `.\.venv\Scripts\python.exe -m pytest resources/tests/backend/providers/ resources/tests/backend/controllers/`
  - **Resultado:** `153 passed in 3.96s` ✅ (82 tests de providers + 71 tests de controllers).
- **Control de Versiones:** Todos los cambios fueron ejecutados mediante `git mv`, preservando historial de commits y trazabilidad.
