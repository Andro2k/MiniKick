# Walkthrough: Soporte de TikTok y Reconocimiento de Emotes en el Overlay de Chat

**Versión:** 1.5.5  
**Documento:** `WT-1.5.5_15.md`  
**Módulos afectados:** [assets/overlays/chat/chat.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/chat.html), [backend/providers/chat/tiktok_chat_provider.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/tiktok_chat_provider.py), [backend/workers/tiktok_chat_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/tiktok_chat_worker.py), [resources/tests/unit/test_tiktok_chat.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/test_tiktok_chat.py)

---

## 1. Resumen Ejecutivo
Se implementó la integración completa de la plataforma **TikTok** en el sistema de Overlay de Chat para OBS (`assets/overlays/chat/chat.html`), junto con un motor de **reconocimiento y renderizado dinámico de emotes** para mensajes de TikTok, Kick, Twitch y YouTube.

---

## 2. Cambios Implementados

### Backend (TikTok Integration & TTS Filtering)
- [backend/providers/chat/tiktok_chat_provider.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/tiktok_chat_provider.py):
  - Extracción exhaustiva de emotes desde `event.emotes` inspeccionando tanto el objeto `EmoteWithIndex` como el modelo interno `emote` (`place_in_comment`, `emote_id`, `image.url_list`).
  - Inclusión de los emotes en la estructura `raw_data["emotes"]`.
- [backend/workers/tiktok_chat_worker.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/tiktok_chat_worker.py):
  - Serialización JSON de los emotes en `ChatMessageDTO.emotes_tag` para su transmisión directa a través del pipeline y el servidor de overlay WebSocket (`topic=chat`).
- [backend/handlers/chat_filter_handler.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/chat_filter_handler.py):
  - Inclusión de `_TIKTOK_EMOTE_REGEX = re.compile(r"\[[a-zA-Z0-9_\-]+\]")` en `clean_message_for_tts()`.
  - Limpieza automática de nombres de emotes en texto para que el sintetizador de voz (TTS) no lea los nombres de los stickers (ej. `[rockyloveit]`).
- [backend/services/chat/spam_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/spam_service.py):
  - Filtrado de emotes de TikTok en `_get_clean_text()` para evitar falsos positivos de spam por símbolos o longitud.

### Frontend Overlay (`chat.html`)
- [assets/overlays/chat/chat.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/chat.html):
  - **Badge de Plataforma TikTok:** Clase CSS `.badge-platform-tiktok` con gradiente dinámico `#00F2FE` a `#FF0050` y sombreado neon cian.
  - **Iconografía Vectorial:** Inclusión de iconos SVG oficiales de TikTok, Super Fan y Top Gifter en el mapa `ICONS`.
  - **Diccionario Nativo de Stickers y Secret Emojis de TikTok (`TIKTOK_STICKERS`):**
    - Mapeo completo de los 46 secret emojis de TikTok (`[smile]`, `[happy]`, `[angry]`, `[cry]`, `[wow]`, etc.).
    - Mapeo de stickers de directos (`[thanks]`, `[laughcry]`, `[thumb]`, `[hi]`, `[heart]`, `[congrat]`).
    - Mapeo de las mascotas animadas de TikTok LIVE: **Rocky** (`[rockyloveit]`, `[rockyserious]`, `[rockyproud]`, `[rockycool]`, etc.), **Rosie** (`[rosiedislike]`, `[rosieawkward]`, `[rosiekisskiss]`, `[rosiecute]`), **Jollie** (`[jolliekissingface]`, `[jolliewow]`, `[jolliespeechless]`), y **Sage** (`[sagethink]`, `[sagefulfilled]`, `[sageclever]`, `[sagemoney]`).
    - Renderizado vectorial de alta resolución vía SVG (Twemoji CDN) con fallback nativo `onerror`.
  - **Motor Dual de Emotes:** Soporte tanto para emotes personalizados de suscriptores (mediante `emotes_tag`) como para la librería completa de stickers estándar de TikTok.
  - **Badges de Roles TikTok:** Soporte y etiquetas para `super_fan`, `top_gifter`, `moderator`, `broadcaster` y `subscriber`.

---

## 3. Pruebas y Validación
Se ejecutó la suite de pruebas unitarias con `python resources/tests/run_tests.py --unit`:
- `test_tiktok_chat_worker_emits_dto_with_emotes`: **PASSED**
- `test_overlay_server_trigger_chat_message_tiktok`: **PASSED**
- `test_clean_message_for_tts_tiktok_emotes`: **PASSED**
- `test_spam_service_tiktok_emotes`: **PASSED**
- **Resultado Global:** 107 pruebas unitarias ejecutadas y aprobadas en 5.31s (0 fallos).
