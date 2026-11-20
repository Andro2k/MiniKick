# Walkthrough Técnico — MiniKick v1.6.9 (Paso 01)

Se añadieron logs de diagnóstico a los canjes de puntos de canal. Algunos usuarios reportan que los canjes no les funcionan y a otros sí, pero los logs de v1.6.8 (DeyDeyLove, Yunior64 y el propio) no contienen ningún canje fallido: los canjes de Kick se procesan y llegan al overlay en los tres, y no hay ningún canje de Twitch en ninguno. Los descartes ocurrían en DEBUG o sin log, por lo que un canje que no hacía nada no dejaba rastro.

---

## Causas candidatas que ahora quedan registradas

1. **Título sin configuración:** `RewardsService.get_reward_config` compara el título de forma exacta (mayúsculas y espacios incluidos) contra la clave `plataforma:título`. Si la recompensa se renombró en la plataforma, no se dispara nada.
2. **Evento de Kick incompleto:** `_handle_reward_redeemed` descartaba en silencio un evento sin `reward_title` o `username`.
3. **Suscripciones de Twitch:** el éxito, el 409 y las excepciones al suscribirse a EventSub se registraban en DEBUG.
4. **Antirrebote:** el mismo usuario y la misma recompensa dentro de una ventana de 8 s se ignoraban en DEBUG.

## Cambios por capa

**Backend**
- `providers/chat/kick_ws_provider.py`: WARNING con las claves del payload cuando falta título o usuario.
- `providers/chat/twitch_eventsub_provider.py`: INFO por suscripción creada (200/202) o ya activa (409); WARNING si la petición lanza una excepción.

**Frontend**
- `window/rewards_handler.py`: INFO cuando ningún mapeo coincide con el título (se muestra con `%r` para ver espacios) y cuando se ignora un duplicado.

**Pruebas**
- `resources/tests/test_rewards_diagnostic_logs.py`: reenvío de un evento válido, descarte con aviso y duplicado en INFO.

## Fuera de alcance

- No cambia el comportamiento: solo el nivel y el contenido de los logs.
- Una comparación de títulos tolerante (sin distinguir mayúsculas ni espacios en los bordes) queda pendiente hasta confirmar con los nuevos logs que esa es la causa.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `pytest test_rewards_diagnostic_logs.py test_kick_ws_heartbeat.py` | 24 aprobadas |
| `project_quality_suite.py --quick` | mismos 6 avisos que antes del cambio, ninguno en los archivos tocados |
