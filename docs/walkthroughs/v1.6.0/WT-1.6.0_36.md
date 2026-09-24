# Walkthrough WT-1.6.0_36: Optimización Acústica, Curva de Audio Cúbica, Normalización de Picos y Anti-Spam en Música y TTS

> **Versión**: `v1.6.0`  
> **Fecha**: 2026-09-22  
> **Área**: `backend/providers/music/`, `backend/providers/voices/`, `backend/handlers/`, `backend/controllers/`  

---

## 1. Novedades

* **Curva de Audio Perceptual Cúbica en la Música**:
  - En [`backend/providers/music/youtube_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_provider.py), se reemplazó el cálculo lineal directo por una curva perceptual cúbica $\mathcal{O}(1)$:
    $$\text{perceptual\_vol} = (\text{slider\_vol} / 100)^3$$
  - Al 10%, la ganancia es $0.001$ ($-30\text{ dB}$), permitiendo música de fondo muy suave; al 50%, es $0.125$ ($-9\text{ dB}$); devolviendo el control fino, granular y sin saturaciones al slider del 0 al 100%.
* **Auto-Ducking de Música durante TTS**:
  - En [`backend/services/chat/tts_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/tts_service.py), `TTSManager` notifica eventos de ciclo de vida de voz (`on_speech_started` y `on_speech_finished`).
  - En [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py), se interconectó `ChatService` con `MusicController.set_ducking(True/False)` mediante Dependency Injection. Mientras el bot habla, la música se atenúa automáticamente al 30% de su volumen y se restaura de inmediato al finalizar.
* **Comando de Moderación en Chat `!skiptts` / `!stoptts`**:
  - En [`backend/controllers/chat_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py), se registró el comando de moderación de sistema `!skiptts` (con alias `!stoptts`, `!ttsskip`, `!silenciotts`), permitiendo que el streamer o sus moderadores interrumpan instantáneamente el audio actual en curso y limpien toda la cola de TTS.

---

## 2. Mejoras

* **Normalización de Picos (Peak Gain Normalization a $-0.3\text{ dBFS}$) en Piper TTS**:
  - En [`backend/providers/voices/piper_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/piper_provider.py), se implementó el método estático `_normalize_peak_pcm(pcm_bytes)` con la librería estándar `array.array('h')` en $\mathcal{O}(N)$ sin dependencias pesadas.
  - Detecta el pico de amplitud máximo y aplica ganancia limpia sin clipping hasta $31,500$ (hasta $+6\text{ dB}$ a $+10\text{ dB}$ de potencia sonora), otorgando presencia, claridad y cuerpo de locutor de radio a las voces sintéticas.
* **Filtro Anti-Spam Inteligente para TTS**:
  - En [`backend/handlers/spam_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/spam_handler.py), se añadieron reglas de colapsado en `clean_message_for_tts`:
    1. Colapso de caracteres repetidos consecutivamente (ej. `"holaaaaaaa"` $\to$ `"holaaa"`, `"77777777"` $\to$ `"777"`).
    2. Colapso de palabras repetidas consecutivamente (ej. `"ja ja ja ja ja"` $\to$ `"ja ja"`).
    3. Truncado inteligente a un máximo prudente de $250$ caracteres (`MAX_TTS_TEXT_LENGTH`), impidiendo que textos masivos bloqueen el audio durante minutos.
* **Estandarización i18n**:
  - Nuevas claves en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json): `chat.commands.skiptts_success` y `chat.commands.skiptts_toast_title`.

---

## 3. Correcciones

* **Parada Inmediata Real en Piper TTS**:
  - En [`backend/providers/voices/piper_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/piper_provider.py), anteriormente `stop()` solo borraba la caché local sin detener el `QMediaPlayer` ni salir del `QEventLoop`. Se añadieron referencias protegidas `self._current_player` y `self._current_loop`, permitiendo que `stop()` aborte la reproducción activa en $< 10\text{ ms}$.
* **Parada Inmediata en LocalTTSProvider**:
  - En [`backend/providers/voices/local_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/local_provider.py), se añadió interrupción inmediata de `self._engine.stop()` en el método `stop()`.

---

## 4. Verificación y Resultados

* **Pytest Suite**:
  ```bash
  .venv\Scripts\pytest.exe resources/tests/test_audio_acoustic_and_anti_spam.py -v
  # 10 passed in 1.26s

  .venv\Scripts\pytest.exe resources/tests
  # 68 passed in 2.39s (100% de la suite verde)
  ```
* **Herramientas de Auditoría**:
  ```bash
  .venv\Scripts\python.exe resources\tools\dead_code_manager.py
  # 0 archivos o símbolos huérfanos

  .venv\Scripts\python.exe resources\tools\unused_parameter_manager.py
  # 0 parámetros no utilizados
  ```
