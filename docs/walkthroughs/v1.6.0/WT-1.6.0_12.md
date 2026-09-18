# Walkthrough v1.6.0 - WT-1.6.0_12: Resiliencia de Red KickAPI y Optimización SQLite para ScheduleWorker

En esta iteración se abordaron las anomalías de conectividad y concurrencia identificadas en el reporte crítico de usuario (`minikick_crash_DeyDeyLove_v1.5.9.log`), eliminando la pérdida de mensajes del bot por desconexión de sockets TCP (error 10054) y suprimiendo las excepciones por bloqueo de base de datos (`database is locked`) mediante caché en memoria y ajuste de timeouts.

---

## 1. Novedades
- **Suite de Pruebas Automatizadas de Resiliencia de Red y Base de Datos (`resources/tests/test_network_and_db_resiliency.py`)**:
  - Se incorporó la prueba `test_kick_api_client_reconnects_on_connection_reset_10054` para validar la renovación transparente de la sesión HTTP ante sockets caídos.
  - Se incorporó la prueba `test_kick_api_client_handles_persistent_network_error` para verificar el manejo seguro de fallos persistentes de red sin causar interrupciones no controladas.
  - Se implementó `test_schedule_service_in_memory_caching_and_invalidation` para garantizar la lectura $\mathcal{O}(1)$ desde memoria RAM y la invalidación reactiva ante mutaciones.
  - Se implementó `test_database_manager_busy_timeout_setting` para asegurar que el `busy_timeout` de SQLite permanezca configurado en 30,000 ms.

---

## 2. Mejoras
- **Caché en Memoria $\mathcal{O}(1)$ en `ScheduleService` (`backend/services/schedule/schedule_service.py`)**:
  - Se añadió almacenamiento en caché en memoria (`self._schedules_cache`) protegido por exclusión mutua (`threading.Lock`).
  - Se optimizó `get_all_schedules(force_reload=False)`: retorna una copia de la lista en memoria en $\mathcal{O}(1)$, eliminando 3,600 operaciones de I/O de disco por hora en segundo plano.
  - Se implementó la invalidación atómica del caché (`invalidate_schedules_cache()`) en `save_schedule()`, `delete_schedule()`, `toggle_schedule()` y `mark_schedule_executed()`.
- **Desacoplamiento y Cohesión en `ScheduleWorker` (`backend/workers/schedule_worker.py`)**:
  - Se encapsuló la persistencia del estado ejecutado delegando a `self.service.mark_schedule_executed(sched["id"], today_date_str)`, respetando el principio de Separación de Responsabilidades (SoR) y evitando llamadas directas del worker a la capa de almacenamiento.
- **Tolerancia a Contención en SQLite (`backend/database/database_manager.py`)**:
  - Se incrementó el `busy_timeout` de SQLite a 30,000 ms (30 segundos) y el timeout de conexión a 30.0 segundos, permitiendo a los hilos concurrentes absorber ráfagas intensivas de escritura de logs y configuración sin disparar `sqlite3.OperationalError: database is locked`.

---

## 3. Correcciones
- **Recuperación y Reconexión Transparente ante `ConnectionResetError 10054` en `KickAPIClient` (`backend/providers/chat/kick_provider.py`)**:
  - Se subsanó el descarte silencioso de mensajes del bot (timers, comandos) cuando Cloudflare o Kick cerraban sockets TCP inactivos tras periodos de silencio.
  - El método `_request` ahora captura excepciones `(requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError, ConnectionResetError)`. Ante un fallo de conexión aborted/reset, cierra la sesión existente, genera una sesión limpia mediante `ScraperFactory.create()` y reintenta la petición de manera inmediata y transparente.

---

## Verificación de Calidad

| Suite de Pruebas | Comando | Resultado |
| :--- | :--- | :--- |
| **Resiliencia de Red y Base de Datos** | `uv run pytest resources/tests/test_network_and_db_resiliency.py` | 4 pasadas (100% éxito) |
| **Suite Completa de Pruebas** | `uv run pytest resources/tests/` | 17 pasadas (100% éxito) |
