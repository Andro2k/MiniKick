# Walkthrough v1.6.0_26: Rediseño Messenger Overlay con Avatares de Usuario, Temas Unificados (Dark, Light, Minimal) y Timestamps HH:MM

## Novedades

1. **Overlay de Chat Estilo Messenger con Avatares Circulares**:
   - Integración de avatares de perfil (38px en vertical, 28px en horizontal) tanto en el web overlay (`assets/overlays/chat/`) como en el mockup visual de configuración (`chat_mockup.py`).
   - Algoritmo de fallback determinista $\mathcal{O}(1)$: si un usuario no posee foto de perfil o mientras se descarga, se genera un gradiente armónico basado en el código del nombre con su letra inicial en negrita.
   - Insignia de rol flotante superpuesta en la esquina inferior derecha del avatar (`broadcaster`, `streamer`, `moderator`, `vip`, `subscriber`, `bot`).
   - Propagación y resolución de `avatar_url` a lo largo de todo el pipeline backend y frontend:
     - `kick_chat_worker.py` y `twitch_chat_worker.py`: pre-sembrado automático del avatar del streamer autenticado.
     - `main_window_core.py`: vinculación directa de `avatar_url` para mensajes del streamer en Kick y Twitch.
     - `chat_pipeline.py`: campo `avatar_url: str = ""` en `ChatMessageDTO`.
     - `chat_controller.py`: emisión en señal `message_received` y para respuestas del bot.
     - `overlay_manager.py`: emisión hacia los clientes WebSockets en el topic `chat`.
     - `chat.js`: motor de resolución y caché asíncrono en cliente (`clientAvatarCache` $\mathcal{O}(1)$) con soporte nativo para avatares de Kick y Twitch (DecAPI).

2. **Consolidación Estética a 3 Temas Modernos**:
   - Eliminación de temas legados redundantes (`card.css`, `cyber.css`, `glass.css`, `neon.css`).
   - Implementación de los 3 únicos temas oficiales:
     - `dark` (*Messenger Oscuro*): Tarjetas burbuja translúcidas con fondo `rgba(22, 24, 38, 0.88)`, bordes sutiles con brillo perimetral y soporte de avatar circular a la izquierda.
     - `light` (*Messenger Claro*): Burbujas frosted con fondo blanco translúcido `rgba(255, 255, 255, 0.92)`, contraste tipográfico `#1e293b` y sombreado suave.
     - `minimal` (*Minimalista*): Renderizado ultra-ligero y limpio sin bordes ni contenedores pesados.
   - Migración transparente en `overlay_settings.py`: cualquier configuración previa con temas legados se normaliza automáticamente a `dark`.

## Mejoras

1. **Formato de Marcas de Tiempo sin Segundos (`HH:MM`)**:
   - Eliminación de segundos en todas las vistas y capas del overlay:
     - `chat.js`: visualización estandarizada `[HH:MM]` en el cliente web.
     - `chat_mockup.py`: maquetas actualizadas a formato `[10:49]`.
     - Workers backend (`kick_chat_worker.py`, `twitch_chat_worker.py`, `youtube_chat_worker.py`, `tiktok_chat_worker.py`): formateo directo con `strftime("%H:%M")`.
     - `main_window_core.py`: enrutamiento interno de mensajes con `strftime("%H:%M")`.

2. **Paridad y Estandarización i18n**:
   - Actualización sincronizada de `locales/es.json` y `locales/en.json` con las claves:
     - `chat.overlay.theme_dark`
     - `chat.overlay.theme_light`
     - `chat.overlay.theme_minimal`
   - Paridad validada al 100% (1,225 claves en español y 1,225 en inglés).

3. **Arquitectura y Eficiencia Big-O**:
   - Despacho y mapeo de temas en $\mathcal{O}(1)$ mediante conjuntos inmutables (`VALID_CHAT_THEMES = frozenset({"dark", "light", "minimal"})`).
   - Hash lookup $\mathcal{O}(1)$ para la selección de gradientes y colores de avatares según el primer caracter del usuario.
   - Caché en memoria `clientAvatarCache` (Map en JS) que evita re-descargas de avatares de chatters recurrentes.
   - Retrocompatibilidad asegurada con slots de PySide6 (`@Slot` multitipo en `widgets_controller.py` y `chat_controller.py`).

## Correcciones

1. **Alineación del Layout Messenger (Avatar sobre el Texto)**:
   - Corrección de la propiedad `flex-direction` en `.message-box`: se corrigió de `column` a `row !important` en `chat.html`, `dark.css` y `light.css`.
   - Se reubicó `<link id="theme-style">` al final del `<head>` en `chat.html` (después del bloque `<style>`) para que las reglas específicas del tema prevalezcan correctamente, situando el avatar a la izquierda del encabezado y mensaje.

2. **Resolución de Fotos de Perfil en Tiempo Real**:
   - Corrección del fallo donde Kick y Twitch no incluían URLs de avatar en los eventos de chat en tiempo real.
   - Implementación de pre-sembrado en backend para el broadcaster y resolución asíncrona sin bloqueos en `chat.js`, sustituyendo de forma suave la inicial temporal por la foto de perfil en cuanto se descarga.

3. **Desincronización de Controles en Panel de Configuración de Overlay**:
   - Corrección de selecciones inválidas en `combo_overlay_theme` al migrar desde perfiles guardados con temas deprecados.

---

### Verificación y Pruebas Realizadas
- `uv run pytest resources/tests/`: 50/50 pruebas superadas con 100% de éxito.
- `unused_parameter_manager.py`: 0 hallazgos detectados.
- `dead_code_manager.py`: 0 hallazgos detectados.
- `role_manager.py -v`: 0 discrepancias de roles y estados QSS.
- `window_audit_manager.py`: 0 ventanas fantasma / fugas de HWND.
- `i18n_manager.py`: 100% de paridad EN/ES.
