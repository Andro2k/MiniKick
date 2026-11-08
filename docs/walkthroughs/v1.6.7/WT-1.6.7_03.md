# Walkthrough Técnico — MiniKick v1.6.7 (Paso 03)

Se auditó el WebSocket de Kick (chat y eventos) por reportes de mensajes y eventos que llegan tarde. Se añadió medición de latencia por tramos, se sacó la búsqueda de GIF del hilo de la interfaz, se corrigió el reinicio del backoff de reconexión, se aceleró la detección de conexiones muertas y se limitó el flush del log de archivo. Módulos afectados: proveedor y worker del chat de Kick, controlador de chat, servicio de Giphy, pipeline de mensajes, utilidades y logger de la aplicación.

---

## Novedades

- Nueva utilidad `LatencyMonitor` que registra un aviso (con enfriamiento de 30 s) cuando una muestra supera su umbral y un resumen por minuto con n, promedio, p95 y máximo.
- El chat de Kick se mide en tres tramos: red (de `created_at` de Kick a la recepción en el socket, umbral 2 s), cola de la interfaz (umbral 1 s) y ejecución del pipeline en el hilo principal (umbral 0.25 s). El mensaje lleva `received_at` para poder medir la cola.
- El tramo de red se calcula siempre, ya no solo con logging en DEBUG.

## Mejoras

- `!gif <texto>` resuelve la búsqueda de Giphy en un hilo secundario (máximo 4 simultáneos) y devuelve el resultado a la interfaz mediante una señal en cola. Las URLs directas siguen siendo síncronas. La caché de Giphy está protegida con un lock.
- Detección de conexión muerta: ping de protocolo cada 20 s con timeout de 10 s (antes 30 y 20); el watchdog envía un ping de Pusher tras un tiempo de inactividad entre 10 y 25 s (un cuarto del `activity_timeout`), espera el pong 10 s (antes 30) y revisa cada 2 s (antes 5). El peor caso estimado pasa de unos 95 s a unos 37 s.
- El backoff de reconexión se reinicia cuando el socket estuvo estable al menos 10 s, además de reiniciarse al recibir un mensaje.
- El handler del archivo de log hace flush inmediato desde WARNING y como máximo cada 0.5 s para el resto de niveles; el flush explícito (cierre y crash) se respeta siempre.
- Las pruebas del heartbeat usan los helpers reales del proveedor en lugar de reimplementar la fórmula.

## Correcciones

- Una búsqueda de GIF sin caché podía bloquear el hilo de la interfaz hasta 3 s y retrasar todos los mensajes en cola.
- En chats tranquilos el backoff quedaba en su máximo (30 s) tras varias caídas porque solo se reiniciaba al llegar un mensaje.
- Un socket medio muerto tardaba hasta unos 95 s en detectarse.
- El log de archivo escribía al disco en cada registro desde el hilo de la interfaz.

> [!NOTE]
> La latencia de red se calcula contra la hora de Kick y el reloj local; un reloj del equipo desfasado distorsiona esa métrica. Las métricas de cola y pipeline usan reloj monotónico y no se ven afectadas.

> [!IMPORTANT]
> Estos cambios añaden instrumentación y quitan causas probables de retraso, pero no se verificaron contra Kick en vivo. Los resúmenes de latencia en los logs permitirán confirmar si el retraso venía de la red o de la aplicación. No se incluyen aún los callbacks de borrado y ban, el deduplicado de eventos ni la corrección del doble despacho por `TypeError` en `_handle_chat_message`.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| Pruebas de latencia, throttle de flush, heartbeat y rotación de claves del WebSocket, controlador de chat y rendimiento de la ruta de mensajes | 54 aprobadas |
| Pruebas nuevas del GIF asíncrono (no bloquea el hilo, URL directa síncrona, aviso sin API key) | 3 aprobadas |
| `resources/tests/test_architecture_and_placement_auditors.py` | 9 aprobadas |
| Tres pruebas de `test_giphy_and_tts_filter.py` | Fallan en el entorno de verificación (requieren API key de Giphy y red); también fallan sin estos cambios |
| Suite rápida de auditorías de calidad | 11 de 12 aprobadas; falla Project Translation Keys por la clave `music.youtube.com` en `backend/utils/youtube_url.py`, ajena a este paso |
| Entorno | Python 3.12 en la verificación; el proyecto declara 3.14 |
