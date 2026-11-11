# Walkthrough Técnico — MiniKick v1.6.8 (Paso 01)

Se añadió la entrega saliente de webhooks: MiniKick envía los eventos del stream (suscripciones, follows, raids, canjes, comandos, chat y cambios de canción) a Discord o a cualquier servicio HTTP propio, como Home Assistant, Node-RED o un servidor personalizado. El envío corre en un hilo de Python puro, sin Qt, con cola acotada, reintentos con backoff y aislamiento por destino, de modo que un endpoint lento o caído no frena el chat, las alertas ni los overlays. Las URLs y los secretos de firma se guardan cifrados con `SecretCipher`, y los tokens de Discord se enmascaran en los logs. La gestión se hace desde una nueva vista **Webhooks** en la barra lateral, con diálogo de configuración y ping de prueba.

---

## Novedades

- Nueva vista **Webhooks** con tabla de destinos (nombre, formato, eventos, plataformas), buscador, interruptor de activación y menú de edición y borrado.
- Diálogo de configuración con presets **Discord** (embeds con color por tipo de evento) y **JSON genérico**, selección de eventos y plataformas, URL enmascarada con opción de mostrarla, y botón **Enviar ping de prueba** que informa estado HTTP y latencia.
- Eventos entregables: suscripción, resuscripción, subs regaladas, cheers, follow, raid, canje de recompensa, comando ejecutado, cambio de canción y mensajes de chat (estos últimos solo si se marcan).
- Firma HMAC-SHA256 opcional para el preset genérico, con las cabeceras `X-MiniKick-Signature-256`, `X-MiniKick-Timestamp` y `X-MiniKick-Event-Id`. La firma se calcula en cada intento y el identificador del evento se mantiene estable para que el receptor pueda deduplicar.
- Aviso en el diálogo al usar `http://` en un destino que no es Discord, y bloqueo de `http://` para dominios de Discord, que exigen `https://`.
- Documento de diseño `docs/designs/webhook_delivery_service.md` alineado con la implementación y registrado en `SITEMAP.md`.

## Mejoras

- **Arquitectura por capas:** contratos en `backend/interfaces/i_webhooks.py`; formatters, firma, transporte, sender, dispatcher, adaptador de eventos y servicio de gestión en `backend/services/webhooks/`; worker en `backend/workers/webhook_delivery_worker.py`; almacén de destinos en `backend/config/webhook_endpoint_store.py`; controlador y vista siguiendo el patrón existente de Timers.
- **Entrega resiliente:** una sola cola con límite de 1000 trabajos pendientes. Los eventos efímeros (chat, comandos, música) se descartan al llegar al 80 % de capacidad y los críticos solo al 100 %. Los reintentos usan backoff exponencial con jitter completo (hasta 4 intentos) programados en un heap, sin dormir el hilo.
- **Aislamiento por destino:** un 429, un timeout o un error 5xx aplica un enfriamiento solo a ese endpoint; `Retry-After` se respeta con un tope de 30 s. Los destinos sanos siguen recibiendo eventos.
- **Seguridad del transporte:** `httpx` sin seguimiento de redirecciones, timeouts de 3 s de conexión y 5 s de lectura, y errores de red que nunca incluyen la URL.
- **Secretos en reposo:** los destinos se guardan como una lista JSON en la clave única `webhook_endpoints` de `config.toml` (`IConfigProvider` solo maneja claves planas), con `target_url` y `hmac_secret` cifrados con prefijo `enc:v1:`, igual que el almacén de tokens.
- **Logs sin tokens:** `redact_secrets()` y `SecretRedactingFilter` se aplican a los handlers de consola y archivo (mensajes, argumentos y tracebacks) y al registro de fallos del arranque. Cubre `discord.com`, `discordapp.com`, subdominios `canary`/`ptb` y rutas `/api/vN/webhooks`.
- **Discord sin menciones masivas:** los embeds incluyen `allowed_mentions` vacío y truncan descripciones largas, para que un `@everyone` escrito en el chat no genere avisos.
- **Cierre ordenado:** `AppContainerCore.shutdown()` detiene el worker (`join` de 1,5 s en hilo daemon) y después cierra el transporte.
- **Integración:** `WebhookEventAdapter` traduce alertas de Twitch, mensajes del chat (como `chat` o `command`), canjes de Kick y Twitch, y cambios de canción (sin repetir la misma canción) hacia `IEventSink.post_event`. El cableado ocupa pocas líneas en `frontend/window/wiring.py`.
- **Separación de datos en la vista:** la tabla recibe `WebhookSummary` (sin URL ni secreto); la URL y el secreto solo llegan al diálogo del destino que se edita.
- **Fuente única:** `EVENT_TYPES` en `i_webhooks.py` y `FORMATTER_REGISTRY` en los formatters son usados por el servicio y el contenedor. El servicio recibe `send` como callable y no una clase concreta.
- **Textos:** claves `webhooks.*` y pestaña `main.sidebar.tabs.webhooks` en `es.json`, `en.json` y `locale_defaults.py`.

## Correcciones

- El diseño original guardaba los destinos en SQLite y usaba `worker_shutdown.py` (coordinador de `QThread`) y `log_format.py` (parser del visor) como puntos de integración. Se corrigió a TOML cifrado, registro en `AppContainerCore.shutdown()` y filtro de logging en `app_logger_core.py`.
- El diseño reencolaba reintentos en la misma cola acotada que consume el worker, con riesgo de bloqueo cuando está llena. Se sustituyó por un heap de reintentos programados.
- Se retiraron datos inventados del documento (dominio del avatar, cifra de cobertura), enlaces absolutos y la versión objetivo errónea, y se eliminó el `design_draft.md` de la raíz.
- Guardar desde otro perfil de Windows ya no borra los destinos que no pueden descifrarse: se conservan tal cual hasta que se puedan abrir de nuevo.
- Reaplicar la búsqueda tras activar, guardar o borrar un destino evita que la tabla vuelva a mostrar la lista completa con el filtro aún escrito.
- El ping de prueba de Discord muestra el título «Test ping» en lugar del título genérico.
- El servicio rechaza guardar destinos sin eventos o sin plataformas; antes esa regla solo existía en la interfaz.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| Suite de pruebas completa | 263 aprobadas |
| Pruebas nuevas de webhooks | Formatters, firma, sender, transporte, worker, dispatcher, adaptador, almacén cifrado, servicio de gestión, filtro de logs y UI (vista, diálogo, controlador) |
| Suite rápida de auditorías de calidad | 14 de 14 aprobadas, incluidas fronteras de arquitectura, ubicación de archivos, código muerto, claves de traducción y textos hardcodeados |
| Ruff sobre los archivos modificados | Sin hallazgos |
| Prueba de extremo a extremo con servidor HTTP local | Entrega firmada del evento suscrito y omisión del no suscrito |
| Auditorías runtime (Layout Matrix, Qt Windows) | Pendientes de ejecutar en el equipo de desarrollo; no pudieron correr en el entorno de pruebas sin pantalla |
| Prueba manual con Discord o Home Assistant reales | Pendiente |

## Limitaciones conocidas

- Kick no genera alertas de suscripción, follow ni raid en la aplicación (solo Twitch crea `AlertEvent`), por lo que esos eventos no se envían desde Kick. Para Kick funcionan chat, comandos y canjes.
- Los destinos que no se pueden descifrar no aparecen en la tabla y por tanto no se pueden borrar desde la interfaz.
- La regex de enmascarado cubre tokens de Discord; las URLs de otros servicios (por ejemplo, el identificador de Home Assistant) no se enmascaran y por eso nunca se escriben en los logs.
