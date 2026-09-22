# Walkthrough WT-1.6.0_35: Corrección de Tareas Asíncronas Huérfanas y Teardown Limpio del Loop de TikTokLive (INC-012)

> **Versión**: `v1.6.0`  
> **ID de Incidente**: `INC-012`  
> **Fecha**: 2026-09-22  
> **Área**: `backend/providers/chat/tiktok_provider.py`  

---

## 1. Novedades

* **Suite de Pruebas Unitarias para TikTokChatProvider**:
  - Se añadió la suite [`resources/tests/test_tiktok_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_tiktok_provider.py) con 6 pruebas automatizadas que validan:
    1. Drenado seguro ante clientes nulos o loops inexistentes.
    2. Invocación limpia de `_clean_tasks` cuando esté presente.
    3. Drenado de rescate (fallback) cancelando tareas y ejecutando `asyncio.gather(*pending, return_exceptions=True)`, garantizando 0 tareas pendientes.
    4. Cierre seguro en `stop_chat()` tanto si el bucle está en ejecución como si ya se encuentra detenido.
    5. Deduplicación de mensajes $\mathcal{O}(1)$ (`_mark_seen`).
    6. Extracción jerárquica de URLs de avatares de usuario (`_extract_avatar_url`).

---

## 2. Mejoras

* **Manejo Determinista del Event Loop Asíncrono de TikTok**:
  - Se introdujo el método estático [`TikTokChatProvider._drain_client_loop`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/tiktok_provider.py) para inspeccionar de manera exhaustiva el bucle de eventos interno (`_asyncio_loop`) del cliente `TikTokLive`.
  - Si el bucle no está corriendo, cancela de inmediato todas las tareas pendientes creadas por `websockets` (`transfer_data`, `close_connection`, ping loops) y las drena mediante `gather`, asegurando que no queden corrutinas suspendidas en memoria.
* **Eliminación de Warnings por Deprecación**:
  - Se retiró la importación directa y obsoleta de `websockets.exceptions.InvalidStatusCode` (marcada como deprecada en websockets 14+), sustituyéndola por inspección de propiedades dinámicas (`status_code`) y tipo de excepción sin dependencias directas de módulos internos.

---

## 3. Correcciones

* **Solución a `Task was destroyed but it is pending!` y `RuntimeError: no running event loop` (INC-012)**:
  - **Causa Raíz**: En la biblioteca `TikTokLiveClient`, el método de drenado y desconexión `_clean_tasks()` estaba condicionado exclusivamente al bloque `except KeyboardInterrupt:`. Ante desconexiones programadas o cierre de la aplicación, `client.run()` retornaba dejando corrutinas de `WebSocketCommonProtocol` activas. Al destruirse estas corrutinas durante la recolección de basura en Python 3.14, el cierre de generadores asíncronos invocaba `events.get_running_loop()`, lo que desataba excepciones `RuntimeError` y warnings críticos en los logs.
  - **Solución**: En [`backend/providers/chat/tiktok_provider.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/tiktok_provider.py), la llamada a `self._client.run(fetch_live_check=True)` fue protegida con una cláusula `try ... finally: self._drain_client_loop(self._client)`. Esto garantiza que, sin importar si el cliente termina por error, cierre manual o desconexión del stream, todas las tareas del bucle sean canceladas y drenadas de forma limpia en el hilo de trabajo antes de liberar el loop.
* **Registro en Historial Maestro**:
  - Se catalogó y documentó formalmente el incidente `INC-012` en [`docs/historial_crashes_y_errores.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/historial_crashes_y_errores.md).

---

## 4. Verificación y Resultados

* **Pytest Suite**:
  ```bash
  .venv\Scripts\pytest.exe resources/tests/test_tiktok_provider.py -v
  # 6 passed in 0.87s (0 warnings)

  .venv\Scripts\pytest.exe resources/tests
  # 58 passed in 2.10s
  ```
* **Herramientas de Salud de Código**:
  ```bash
  .venv\Scripts\python.exe resources\tools\dead_code_manager.py
  # 0 huérfanos, 0 código muerto

  .venv\Scripts\python.exe resources\tools\unused_parameter_manager.py
  # 0 parámetros huérfanos
  ```
