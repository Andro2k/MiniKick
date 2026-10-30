# Walkthrough Técnico — MiniKick v1.6.6 (Paso 09)

Eliminación de dos costes residuales en el hilo de interfaz detectados en `minikick_9ee8ce.log` sobre el HEAD `202f2c3` de `release/v1.6.6`, que ya incluye los pasos 05 a 07 (con la caché de descifrado de tokens revertida). El log contiene tres sesiones; solo la última (07:03:13) incluye el parche del paso 07, porque es la única cuyo planificador de creación anticipada arranca 300 ms después de la hidratación. Tras ese parche, el refresco de integraciones de Settings bajó de ~300 ms a ~140 ms en lugar de a ~15 ms, y las revisitas conservan un coste fijo de 9–27 ms (con picos de hasta 530 ms) en una fase de la navegación que solo contiene una línea de log. Este paso corrige ambos: el estado de plataformas de `RewardsView` deja de compararse por claves que la vista no usa, y la persistencia de los registros de log en SQLite pasa a un hilo en segundo plano con escritura por lotes. Módulos afectados: `frontend/views/rewards_view.py`, `backend/database/logs_storage.py`, `backend/services/system/logs_service.py`, `backend/services/system/log_writer.py` (nuevo), `frontend/main_window.py` y las pruebas `test_connected_platforms_idempotence.py`, `test_log_writer.py` (nuevo) y `test_log_service_async.py` (nuevo).

Validado con 13 pruebas nuevas (7 del escritor de logs, 5 del servicio y 1 de `RewardsView`), la batería de pruebas relevante (136 pasan) y los auditores del proyecto (fronteras de arquitectura, DRY, código muerto, ubicación de archivos, parámetros sin uso, tokens de diseño, textos hardcodeados y señales Qt), todos en verde. Los cambios se entregan como `0011-perf-rewards-effective-platform-state.patch` y `0012-perf-async-log-persistence.patch`; ambos aplican sobre `202f2c3`, de forma independiente y en conjunto.

---

## Diagnóstico a partir del log

| Medida (sesión 07:03:13, con el paso 07) | Valor |
| --- | --- |
| Primera visita a Chat / Stream Info (ya anticipadas) | 39.78 / 33.32 ms (antes 574–595 / 239 ms) |
| Refresco de integraciones, `views` | 142.01 / 142.06 / 136.95 / 134.81 ms (sesiones previas: 280–330 ms) |
| Settings, revisita, `hooks` | 174.90 / 180.24 / 165.63 ms y, una sola vez, 13.45 ms |
| `create` en revisitas | 9–27 ms habitual; picos de 61.60, 95.52, 282.16 y 530.26 ms |
| `switch` en revisitas | 1.7–19.7 ms |

**Coste residual de Settings (`views` ≈ 140 ms).** El único `hooks` de Settings que costó 13.45 ms fue una visita inmediatamente posterior a otra visita a Settings, sin pasar por Triggers entre ambas. En todas las demás había una visita a Triggers antes. Cada visita a Triggers lanza `_fetch_api_rewards()`, y al llegar los datos `RewardsController` llama a `populate_table(..., connected_platforms=self._get_connected_platforms())`. Ese diccionario tiene solo dos claves (`kick`, `twitch`), mientras que `MainWindowCore.get_connected_platforms()` entrega cuatro (`kick`, `twitch`, `youtube`, `tiktok`). La vista guarda el de dos claves, y en la siguiente visita a Settings el de cuatro claves no es igual, aunque `RewardsView` solo consulta `kick` y `twitch`, así que la guarda del paso 07 no actúa y `_apply_filters()` reconstruye la tabla de recompensas (~135–142 ms).

**Coste fijo de `create` en revisitas.** La fase `create` del log abarca desde el inicio de `_handle_navigation` hasta justo antes de `setCurrentWidget`. Para una vista ya creada, esa fase solo contiene la línea `[User Action] Navigated to view` y una búsqueda en un diccionario. Por tanto, esos 9–27 ms (con picos de hasta 530 ms) corresponden a una llamada a `logger.info` en el hilo de interfaz (conclusión por lectura del código, no medida directa en Windows).

Esa llamada pasa por `QLogHandler`, cuya señal se conecta a `LogsController.process_incoming_log`. Ese manejador se ejecuta siempre en el hilo de interfaz, incluso para registros emitidos desde otros hilos. Para cada registro llama a `LogService.append_record`, que invocaba `SQLiteSystemLogStorage.append_log`: una conexión nueva, cuatro `PRAGMA`, un `INSERT` y un `commit`, de forma síncrona. En consecuencia, cada línea de log de la aplicación, incluidas las de los hilos de chat y los workers, escribía en SQLite en el hilo de interfaz.

## Novedades

- **`BatchedLogWriter`** (`backend/services/system/log_writer.py`): hilo demonio `LogBatchWriter` con una cola; agrupa los registros que llegan durante 250 ms (hasta 200 por lote) y los entrega a una función de escritura. Ofrece `flush(timeout)`, que espera a que se vacíe la cola, y `close(timeout)`, que drena lo pendiente y detiene el hilo. Si la escritura falla, informa por `sys.__stderr__`, pierde solo ese lote y sigue vivo. Tras `close()` ignora nuevos envíos y, si nunca recibió registros, no llega a crear el hilo.
- **`SQLiteSystemLogStorage.append_logs(records)`**: inserta todo un lote con `executemany` en una única conexión y una única transacción.
- **`LogService`**: `append_record` guarda el registro en el historial en memoria y lo encola, sin tocar la base de datos. Nuevos `flush_pending()` y `close()`. `get_history`, `get_filtered_history` y `clear_history` vacían primero la cola, de modo que la vista de logs sigue viendo los registros más recientes. Sin almacenamiento configurado funciona solo en memoria, como antes.
- **Cierre ordenado**: `_finish_cleanup` de `MainWindowCore` llama a `log_service.close()` justo antes de `db_manager.cleanup()`.
- **`RewardsView`**: `set_connected_platforms` compara únicamente los estados de las plataformas que la vista usa (`kick` y `twitch`, mediante la función de módulo `_platform_flags`) y guarda su propia copia del diccionario recibido.

## Mejoras

- **Separación de responsabilidades**: la política de persistencia de logs sale de la ruta de presentación; `LogService` solo registra y consulta, y el escritor decide cuándo y cómo escribir.
- **Coste por registro en el hilo llamador**: de 1.586 ms a 0.0023 ms en el entorno de validación (Linux, 300 registros sobre una base temporal), unas 690 veces menos. Los 300 registros se drenaron después en 257 ms y se persistieron las 601 filas esperadas. En el log de Windows el coste observado por clic es de 9–27 ms, por lo que se espera un efecto proporcionalmente mayor.
- **Conexiones SQLite**: de una por registro a una por lote.
- **Efecto esperado en el log**: `create` de las revisitas cercano a 0–2 ms y `hooks` de Settings en ~13 ms de forma consistente. Son estimaciones; deben confirmarse con un log nuevo.
- **Alcance**: la ganancia aplica a todo el tráfico de logs, también al de los hilos de chat, que antes escribía en SQLite en el hilo de interfaz por cada línea registrada.

## Compromisos y riesgos a tener en cuenta

- **Retraso de persistencia**: los registros llegan a la base de datos hasta ~250 ms después. Las lecturas del servicio vacían la cola antes de consultar, por lo que la vista de logs no se ve afectada.
- **Cierre brusco o fallo del proceso**: pueden perderse los registros de los últimos ~250 ms **en la base de datos**. El archivo `minikick.log` y el log de fallos siguen escribiéndose de forma síncrona y no cambian.
- **Últimas líneas del cierre**: lo que se registre después de `log_service.close()` (por ejemplo «Shutdown sequence completed») queda en el archivo de log pero no en la base de datos.
- **Fallo de escritura de un lote**: se pierde ese lote y se avisa por `stderr`; antes se perdía el registro individual con el mismo aviso.
- **Sin cambios** en el formato de los registros, el historial en memoria, el filtrado ni la vista de logs.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `test_log_writer.py` | 7 pasan (lotes y orden, envío sin bloqueo con almacenamiento lento, escritura fuera del hilo llamador, `flush` con y sin tiempo suficiente, `close` drena y rechaza envíos tardíos, fallo de un lote, `close` sin registros) |
| `test_log_service_async.py` | 5 pasan (rendimiento y persistencia contra SQLite real, lecturas que incluyen registros sin escribir, `clear_history`, `close`, modo sin almacenamiento) |
| `test_connected_platforms_idempotence.py` | 17 pasan (16 previas + 1 nueva: la vista ignora plataformas que no usa) |
| Batería relevante (frontend, contratos, handlers, controladores, logging, ajustes, auditores) | 136 pasan |
| Auditores CLI (fronteras, DRY, código muerto, ubicación, parámetros sin uso, tokens de diseño, textos, señales Qt) | Sin hallazgos |

**Fallos y limitaciones preexistentes, sin relación con este paso:**

- `test_giphy_and_tts_filter.py` (3 pruebas): dependen de la API key y de red de Giphy.
- `test_worker_and_core_lifecycle.py::test_chat_and_reward_workers_stop_sets_interruption_and_quit`: intermitente (carrera entre `run()` y `stop()` con `channel_name=""`).
- La suite completa y las pruebas que instancian la ventana principal producen *segmentation fault* en el entorno de validación (Qt sin pantalla). El cambio en `_finish_cleanup` de `main_window.py` no tiene prueba automatizada por esa razón; se valida cerrando la aplicación y comprobando en el siguiente log que las últimas líneas del cierre aparecen y que el apagado no se alarga.

## Pendiente (no incluido en este paso)

- **Manejador de archivo de log**: `AutoFlushTimedRotatingFileHandler` sigue escribiendo y vaciando el búfer en el hilo que registra, para cada línea de nivel INFO o superior. Si tras este paso `create` en revisitas sigue por encima de unos 5 ms, el siguiente paso sería un `QueueHandler`/`QueueListener` para sacar también esa escritura del hilo de interfaz, con el cuidado de vaciar la cola en `flush_all_logs()`.
- **Triggers**: `_fetch_api_rewards()` crea un cliente y lanza un worker de red en cada visita (≈ 24–29 ms de `hooks`), y la reconstrucción de la tabla al llegar los datos ocurre en el hilo de interfaz y no está medida.
- **Settings, creación**: ~400 ms; conviene medir qué parte corresponde a la enumeración de dispositivos de audio.
- **Arranque y cierre**: el total de arranque varió entre 2.2 y 6.3 s según la sesión (los imports entre 1.5 y 2.8 s, probablemente por el estado de la caché de archivos); la hidratación `integrations and profile` tarda 115–150 ms y los workers tardan ~1.1 s en detenerse.
