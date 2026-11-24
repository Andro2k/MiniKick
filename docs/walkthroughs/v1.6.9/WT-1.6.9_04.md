# Walkthrough Técnico — MiniKick v1.6.9 (Paso 04)

Corrección de la inyección por `{touser}` en las respuestas de comandos del chat, pendiente del Paso 03.

---

## Contexto

`CommandService._try_execute` sustituía `{touser}` (primer argumento que escribe cualquier espectador) con `str.replace`. En Twitch, `TwitchWebSocketManager.send_privmsg` envía el texto por IRC sin modificar, así que una plantilla que empezara por `{touser}` permitía que el mensaje del bot comenzara por `/` o `!` (comandos de Twitch u otros bots). La sustitución encadenada tampoco evitaba que un valor como `{random}` se expandiera después. Kick y la Helix API de Twitch no interpretan `/`, pero el filtro es el mismo para todas las plataformas.

## Cambios por capa

**Backend**
- `services/chat/commands_service.py`:
  - `_safe_placeholder`: elimina caracteres no imprimibles, quita los prefijos `/`, `.` y `!` iniciales y limita a 40 caracteres.
  - `_render_response`: sustitución de una sola pasada con `re.sub`; si `touser` queda vacío (por ejemplo `!hug @`) usa el usuario que ejecuta el comando.
  - `_try_execute` usa `_render_response`; `random` pasa a importarse a nivel de módulo.

**Pruebas**
- `resources/tests/test_command_placeholders.py` (nuevo): argumentos `/ban`, `!otrocmd`, `.disconnect`, `@ana` y `@` hacia el worker de Twitch, no re-sustitución de `{random}` y límite de longitud.

## Archivos afectados

`backend/services/chat/commands_service.py`, `resources/tests/test_command_placeholders.py`.

## Verificación

- `pytest` sobre `test_command_placeholders.py`, `test_chat_controller.py` y `test_commands_help_and_backup.py`: 27 en verde.
- `resources/tools/project_quality_suite.py --quick`: 13 auditores en PASS; `Frontend QSS Roles` y `Frontend Qt Windows` fallan igual que en el commit base `1e851a4` (sin archivos frontend tocados).

## Notas

- Una plantilla que el propio streamer escriba empezando por `/` (por ejemplo `/announce ...`) sigue funcionando: solo se limpian los valores sustituidos, no la plantilla.
