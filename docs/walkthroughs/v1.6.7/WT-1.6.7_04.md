# Walkthrough Técnico — MiniKick v1.6.7 (Paso 04)

Los usuarios reportaron que el TTS leía cualquier emoji escrito en el chat. Se comprobó con el fonemizador de Piper (espeak-ng en español) que cada emoji se pronuncia con su nombre, por ejemplo "cara llorando de risa" o "manos en oración", y que un emoji pegado a un nombre de usuario provocaba además que el nombre se deletreara letra por letra. Se añadió una utilidad que elimina emojis y se aplicó en el filtro del chat y en la entrada del gestor de TTS. Módulos afectados: utilidades de texto, filtro de chat y gestor de TTS.

---

## Novedades

- Nueva utilidad `strip_emojis` en `backend/utils/text_utils.py`, exportada desde `backend.utils`. Elimina pictogramas, emoticonos, banderas (incluidas las de subdivisión), tonos de piel, secuencias unidas con ZWJ, teclas numéricas con marco, selectores de variación y símbolos emoji de los bloques de símbolos varios y dingbats.
- Un mensaje compuesto solo por emojis queda vacío y no se envía a la voz.

## Mejoras

- `ChatFilterHandler.clean_message_for_tts` elimina los emojis antes del resto de la limpieza, de modo que el recorte de longitud máxima solo cuenta texto hablable.
- `TTSManager.say` aplica la misma limpieza como red de seguridad para cualquier texto que llegue al TTS (nombres de usuario, alertas u otros avisos) y descarta los textos que solo contienen emojis, con un log DEBUG.
- El emoji se sustituye por un espacio y los espacios sobrantes se colapsan, por lo que "hola😂mundo" se lee como dos palabras.
- No se tocan acentos, signos de apertura, símbolos de texto como `%`, `@`, `#`, `&`, `$`, `€` o `©`, ni escrituras que usan ZWJ para dar forma a las letras.

## Correcciones

- El TTS ya no pronuncia el nombre de los emojis, tanto con Piper como con los demás proveedores, porque la limpieza ocurre antes de elegir proveedor.
- Los nombres de usuario con un emoji pegado (por ejemplo "Juan" seguido de un emoji de fuego) ya no se deletrean letra por letra.

> [!NOTE]
> No se eliminan los emoticonos escritos con caracteres ASCII (por ejemplo `:)` o `:D`) ni las letras con estilos Unicode decorativos (por ejemplo alfabetos matemáticos en negrita o cursiva) usadas en algunos nombres de usuario.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `resources/tests/test_tts_emoji_stripping.py` (nuevas) | 26 aprobadas |
| Comparación con el fonemizador de Piper (espeak-ng, español) antes y después de la limpieza | Los nombres de emojis desaparecen de la salida fonética; "Juan" más emoji pasa de deletrearse a pronunciarse "juan" |
| Pruebas de filtro TTS, controlador de chat, workers, anti-spam, arquitectura, parámetros sin usar e imports perezosos | 82 aprobadas, 4 fallidas |
| Pruebas fallidas | Tres de `test_giphy_and_tts_filter.py` (requieren API key de Giphy y red) y `test_chat_and_reward_workers_stop_sets_interruption_and_quit` (intermitente); fallan igual sin estos cambios |
| Suite rápida de auditorías de calidad | 11 de 12 aprobadas; falla Project Translation Keys por la clave `music.youtube.com` en `backend/utils/youtube_url.py`, ajena a este paso |
| Entorno | Python 3.12 en la verificación; el proyecto declara 3.14. Piper se probó solo a nivel de fonemización, no se reprodujo audio |
