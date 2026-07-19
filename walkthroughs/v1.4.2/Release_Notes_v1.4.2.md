# Historial de Cambios y Mejoras - Versión v1.4.2

Este documento detalla todas las refactorizaciones, optimizaciones de rendimiento y correcciones de errores aplicadas al sistema para mejorar su modularidad, disminuir la complejidad temporal y evitar fugas de memoria.

---

## 1. Refactorización y Desacoplamiento de Controladores ( backend/controllers )

Se aplicaron principios de **Inversión de Dependencias (Pillar 1)** y **Separación de Responsabilidades (Pillar 2)** en la capa de controladores para aislar la lógica del backend de la interfaz gráfica (PySide6).

* **LogController (`log_controller.py`):**
  * Se eliminó la importación y creación directa de `BugReportDialog` en el controlador.
  * Se delegó la acción a un nuevo método unificado en la vista (`self.view.show_bug_report_dialog()`).
* **UpdateController (`update_controller.py`):**
  * Se rediseñó por completo para ser un controlador **100% no-visual**.
  * Se removieron las dependencias de `MainWindow` y las clases de diálogo del frontend.
  * Ahora expone señales asíncronas para reportar estados (`update_found`, `download_progress`, etc.).
* **MainWindowCore (`main_window_core.py`):**
  * Se implementó el método `handle_update_check()` en la ventana principal (capa de presentación) para gestionar interactivamente el ciclo de vida y eventos del `UpdateDialog`.
* **ChatController (`chat_controller.py`):**
  * Se eliminó el acceso directo a los widgets internos (`self.view.chk_command`, `self.view.txt_command`) y a la manipulación directa de señales de la vista en `_sync_tts_command_from_db`.
  * Se encapsuló esta funcionalidad mediante la introducción del método `set_tts_command_configuration` en `ChatView`.
* **MusicController (`music_controller.py`):**
  * Se introdujo inyección de dependencias a través de un diccionario `provider_factory` en el constructor, desacoplando la clase de la instanciación e importación directa de `SpotifyMusicProvider` y `YouTubeMusicProvider`.

---

## 2. Optimización de Rendimiento en Capa de Datos ( backend/database y backend/services )

Se reemplazaron las búsquedas secuenciales $O(N)$ en memoria por consultas indexadas en base de datos $O(1)$ para optimizar el rendimiento y disminuir la carga de procesamiento y uso de disco.

* **timers_storage.py & timer_service.py:**
  * Se creó y expuso la consulta individual `get_timer_by_id(timer_id)`.
  * Se actualizó `TimerController` para utilizar esta llamada rápida en edición, eliminación y cambio de estado, evitando cargar toda la colección de base de datos a memoria principal de Python.
* **commands_storage.py & command_service.py:**
  * Se creó y expuso la consulta directa `get_command_by_trigger(trigger)`.
  * Se actualizó `CommandController` para usar este método directo para verificar la existencia de un comando en $O(1)$.
* **Toast DRY Helper:**
  * Se centralizó el código redundante de creación y formateo de alertas emergentes en un único método `_show_toast(...)` reutilizable.

---

## 3. Corrección de Fugas de Memoria y Optimización de Hilos ( backend/services y backend/workers )

Se resolvieron problemas críticos de acumulación infinita de datos en memoria (RAM) y bloqueos innecesarios en subprocesos asíncronos.

* **SpamService (`spam_service.py`):**
  * Se implementó la inserción y descarte ordenado por orden de llegada (FIFO) usando un límite preestablecido de `max_history_size` (1000 usuarios).
  * Esto previene que la variable `self.user_history` crezca linealmente $O(U)$ indefinidamente durante transmisiones prolongadas con miles de espectadores activos.
* **RewardWorker (`rewards_worker.py`):**
  * Se reemplazó la llamada bloqueante de sistema operativo `time.sleep(0.5)` por el método de subprocesamiento de Qt `self.msleep(500)`. Esto permite suspender de forma segura el hilo asíncrono y responder de inmediato al método `stop()`.
  * Se implementó un buffer ordenado FIFO (`self._processed_order`) limitando el tamaño del conjunto `self._processed_ids` a un máximo de 2000 registros, liberando de forma constante los IDs de canjes más antiguos y protegiendo el consumo de memoria en ejecuciones a largo plazo.

---

## 4. Corrección de Errores Visuales ( frontend/dialogs )

* **UpdateDialog (`update_dialog.py`):**
  * Se corrigió la invisibilidad del ícono de checkmark de descarga completada en `show_complete()`. El ícono se pintaba usando `COLOR_GREEN` (`#2ECD70`) sobre el círculo de fondo del mismo tono `COLOR_GREEN`, haciéndolo imperceptible. Se cambió la coloración del ícono a `COLOR_NEUTRAL_950` para proveer un contraste óptimo.
