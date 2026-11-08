# Walkthrough Técnico — MiniKick v1.6.7 (Paso 06)

Se amplió el diagnóstico de latencia de Kick sin alterar el procesamiento del chat ni intentar corregir los episodios reportados. Ahora se mide el RTT de Pusher durante tráfico activo y las advertencias de mensajes lentos incluyen contexto de socket, tópico e hilo. También se corrigió el resumen del máximo cuando todas las muestras son negativas.

---

## Novedades

- Nuevo monitor `Kick pong RTT`, alimentado por pongs correlacionados con sondas Pusher.
- El watchdog envía una sonda aproximadamente cada 20 segundos incluso cuando hay mensajes. Mantiene una sola sonda RTT pendiente; el timeout de heartbeat existente continúa activo.
- Las advertencias rate-limited de mensajes lentos incluyen ID, `created_at`, latencia cruda, tópico/canal, segundos desde el frame anterior, segundos desde el último pong y nombre del hilo.
- El parser conserva el campo `channel` del sobre Pusher para que el registro identifique el tópico que entregó el mensaje.

## Mejoras

- Las mediciones de RTT, tiempo entre frames y tiempo desde el último pong usan reloj monotónico.
- El registro de latencia de Kick deja al warning contextual del proveedor la responsabilidad de alertar sobre mensajes lentos, evitando duplicar warnings genéricos.
- La estimación opcional del desfase del reloj no se agregó: el cliente no expone el encabezado HTTP `Date` en los datos de inicio, y el diagnóstico solicitado no requiere añadir otra llamada de red.

## Correcciones

- El máximo por intervalo de `LatencyMonitor` ya no parte de cero; cuando todas las muestras son negativas, el resumen muestra el máximo real negativo.
- No se modificaron el backoff, los intervalos existentes de inactividad, el timeout `PONG_TIMEOUT_S`, las reconexiones ni el flujo de mensajes. Este cambio instrumenta la latencia; no afirma haber eliminado la demora ni determina todavía si ocurre en Kick, la red o el hilo del socket.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `$env:QT_QPA_PLATFORM='offscreen'; .\.venv\Scripts\python.exe -m pytest resources\tests\test_latency_monitor.py resources\tests\test_kick_ws_heartbeat.py resources\tests\test_kick_ws_key_rotation.py resources\tests\test_chat_controller.py resources\tests\test_message_path_performance.py --tb=short -q` | 57 aprobadas |
| `.\.venv\Scripts\python.exe -m pytest resources\tests\test_json_utils.py --tb=short -q` | 6 aprobadas |
| `.\.venv\Scripts\python.exe resources\tools\project_quality_suite.py --quick` | 11/12 aprobadas; falla únicamente Project Translation Keys por `music.youtube.com` en `backend/utils/youtube_url.py`, falso positivo conocido y ajeno a este cambio |
| `git diff --check` | Sin errores de whitespace |

> [!NOTE]
> El log adjunto estaba vacío. El contexto de latencia se basa en los resultados resumidos por el usuario; no se atribuye la demora a una causa no observada directamente.
