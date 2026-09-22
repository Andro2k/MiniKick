# Walkthrough v1.6.0_29: Supresión Inteligente de Enlaces GIF en Mensajes de Chat y TTS

## Novedades y Mejoras

1. **Supresión Automática del Enlace de Texto al Embeber GIFs**:
   - **Problema anterior**: Cuando un usuario enviaba un enlace de Giphy (ej. `https://giphy.com/gifs/autumn-fall-peanuts-Zb2lUCnGMXzjO` o con tokens de CDN `https://media.giphy.com/media/v1.Y2lk.../Zb2lUCnGMXzjO/giphy.gif`), el overlay mostraba el GIF correctamente pero también dejaba visible la URL larga en texto crudo sobre la imagen animada y estiraba las píldoras horizontales.
   - **Solución implementada**:
     - En `formatChatMessage` de `assets/overlays/chat/js/chat.js`, se implementó detección profunda de GIFs mediante extracción de ID canónico de Giphy (`giphyIdMatch`) y expresiones regulares de coincidencia de URL.
     - Si el mensaje contiene un enlace de Giphy o GIF directo (`.gif`, `.webp`) y `gif_url` está presente, el enlace se suprime del texto.
     - Si el mensaje contenía únicamente el enlace, el texto queda vacío y se renderiza **únicamente la imagen animada**, luciendo como un embed nativo limpio (estilo Discord o WhatsApp).
     - Si el usuario escribió texto junto al enlace (ej. `mira esto https://giphy.com/...`), el texto del comentario permanece visible y la URL se retira de forma transparente.

2. **Supresión en Síntesis de Voz (TTS)**:
   - En `backend/handlers/spam_handler.py` (`clean_message_for_tts`), se extendió la limpieza de URLs de Giphy cuando `gif_url` está resuelto.
   - Evita que la voz sintetizada lea "un enlace web" o cadenas largas cuando un espectador envía un GIF.

---

### Verificación y Pruebas Realizadas
- `uv run pytest resources/tests/`: 50/50 pruebas superadas con 100% de éxito, incluyendo nuevos casos para enlaces de página y CDN de Giphy.
- `resources/tools/unused_parameter_manager.py`: 0 hallazgos detectados.
- `resources/tools/dead_code_manager.py`: 0 hallazgos detectados.
- `resources/tools/role_manager.py -v`: 0 estilos o roles faltantes/huérfanos.
