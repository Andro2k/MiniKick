# Walkthrough WT-1.6.0_25: Corrección de Auto-Embed GIF (HTTP 414) y Exclusión de Bots en Top Chatters

> **Versión**: MiniKick `v1.6.0`  
> **Incidente Relacionado**: `INC-010` (Registrado en `docs/historial_crashes_y_errores.md`)  
> **Área**: Backend Chat Services (`GiphyService`, `ChatController`, `SpamHandler`) y Widgets (`WidgetsController`, `chatters.html`).  

---

## 1. Novedades

- **Extractor Estático de URLs de GIF (`extract_gif_url`)**:
  - Se implementó un método $\mathcal{O}(N)$ en [`backend/services/chat/giphy_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/giphy_service.py) dedicado a detectar y extraer enlaces válidos a imágenes GIF (`.gif`, `.webp`) o páginas/medios canónicos de Giphy (`giphy.com/gifs/...`, `media.giphy.com/media/...`) sin realizar ninguna llamada de red a la API externa.
- **Normalización y Soporte Robusto para Nombres con Arroba (`@`)**:
  - Tanto [`SpamHandler.is_bot`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/spam_handler.py) como [`WidgetsController._record_chatter_message`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py) ahora normalizan de forma transparente identificadores de usuario con o sin prefijo `@`, agrupando los mensajes de un mismo usuario bajo una clave única en el ranking y reconociendo a `@MiniKick` de forma inmediata.

---

## 2. Mejoras

- **Optimización de Complejidad y Reducción de Latencia en Chat Render**:
  - Al procesar mensajes ordinarios con enlaces web (TikTok, YouTube, enlaces informativos, temporizadores), `ChatController._step_ui_render` delega la comprobación a `extract_gif_url` en lugar de una búsqueda de texto en Giphy.
  - Se eliminaron peticiones HTTP espurias a Giphy, reduciendo el tráfico de red innecesario y evitando esperas de timeout.
- **Ampliación Centralizada de Bots Comunes de Streaming**:
  - Se expandió `_DEFAULT_BOTS` y `_IGNORED_CHATTER_BOTS` con los bots más habituales en Twitch y Kick: `minikick`, `@minikick`, `streamlabs`, `wizebot`, `kofi`, `streamerbot`, `fossabot`, `sery_bot`, `blerp`, `soundalerts` y `songlistbot`.
- **Inyección de Dependencias Limpia**:
  - Se inyectó `spam_service` en `WidgetsController` desde `MainWindowCore`, permitiendo a Top Chatters consultar dinámicamente los bots configurados por el streamer en la sección de filtros de spam (`tts_ignored_users`).

---

## 3. Correcciones

- **Eliminación del Error `HTTP Error 414: URI Too Long` en Giphy**:
  - Se corrigió la causa raíz por la cual mensajes de temporizadores con enlaces largos (como `🖤Aquí está el enlace de TikTok!: https://www.tiktok.com/@theandro2k ...`) eran tratados erróneamente como términos de búsqueda en `GiphyService.resolve_gif`.
  - Se agregaron cláusulas de guarda que limitan las búsquedas de texto a $\le 80$ caracteres, rechazan consultas que contengan esquemas `http` y no buscan cuando el parámetro `allow_search` es `False`.
  - Se blindó `_step_ui_render` para saltar la evaluación de GIFs si el autor del mensaje es un bot (`not self.filter_handler.is_bot(dto.user, badges)`).
- **Exclusión Definitiva de Bots en Top Chatters ([chatters.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/chatters.html))**:
  - Se corrigió [`WidgetsController._record_chatter_message`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py):
    - Se verifica si `badges` contiene `"bot"`, descartando inmediatamente el mensaje.
    - Se verifica el nombre normalizado contra `_IGNORED_CHATTER_BOTS` y contra la lista persistida de `ignored_users`.
    - Los mensajes emitidos por `@MiniKick` o respuestas automatizadas ya no suman al contador de Top Chatters en el overlay de OBS.

---

## 4. Pruebas y Validación

- **Pruebas Automatizadas**:
  ```powershell
  uv run pytest resources/tests/test_giphy_and_tts_filter.py
  # ✅ 11 passed (100% pasando)
  uv run pytest resources/tests/
  # ✅ 50 passed (100% pasando)
  ```
- **Auditoría de Parámetros No Utilizados**:
  ```powershell
  uv run python resources/tools/unused_parameter_manager.py
  # ✅ 0 parámetros muertos | 0 contratos huérfanos | 0 eventos Qt desalineados
  ```
- **Auditoría de Código Muerto y Roles**:
  ```powershell
  uv run python resources/tools/dead_code_manager.py
  # ✅ 0 archivos huérfanos | 0 símbolos no usados | 0 imports innecesarios
  uv run python resources/tools/role_manager.py -v
  # ✅ 66/66 roles y 20/20 estados en perfecta sincronía
  ```
