# Walkthrough - WT-1.5.8_01: Optimización de Rendimiento en Widgets, Chat/TTS y Sistema de Toasts

**Versión:** `v1.5.8`  
**Documento:** `WT-1.5.8_01.md`  
**Fecha:** 02 de Septiembre, 2026  

---

## Contexto y Motivación
Durante el análisis de auditoría de rendimiento de la aplicación en sesiones activas de streaming, se identificaron varios cuellos de botella que afectaban la fluidez de la interfaz de usuario (UI Thread):
1. **Sincronización en Cascada en Widgets ($O(N)$)**: Al alternar o editar un solo widget (ej. `shoutout`), el controlador ejecutaba `sync_commands_with_db()`, iterando indiscriminadamente sobre todos los widgets y guardando 5 comandos en `CommandService`. Cada guardado disparaba `_rebuild_dispatch_table_from_cache()` y emitía la señal `commands_changed` repetidamente (5 veces consecutivas), obligando a múltiples controladores a re-evaluar la base de datos o re-renderizar tablas.
2. **Doble Suscripción de Señales en `MusicController`**: `commands_changed` estaba conectado dos veces (en `__init__` y en `_connect_signals()`), duplicando el trabajo a 10 llamadas innecesarias.
3. **Tormenta de Transacciones SQLite en Chat/TTS**: Al guardar la configuración de Chat/TTS, `ChatService.save_settings()` invocaba `save_bool` y `save_string` 19 veces por separado, realizando 19 transacciones `INSERT ... commit` independientes y síncronas en disco en el hilo principal. Asimismo, los sliders de volumen y velocidad invocaban `save_string` en cada micro-movimiento del mouse sin debouncing.
4. **Saturación y Colisión de Animaciones en Toasts**: Al encender y apagar switches rápidamente para probar las notificaciones, los textos cambiaban ("Activado" vs "Desactivado"), por lo que la deduplicación por texto exacto fallaba. Cada alternancia destruía el widget anterior, creaba un nuevo `ModernToast` y reiniciaba animaciones concurrentes `QPropertyAnimation(pos)` compitiendo con los bloqueos de E/S síncrona en disco, produciendo una notable sensación de tironeo ("lag").

---

## Cambios Implementados

### 1. Sincronización Diferencial $O(1)$ en Widgets (`WidgetController`)
- **Actualización Puntual (`_sync_single_widget_command`)**: Se desacopló la sincronización masiva `sync_commands_with_db()` del flujo de guardado diferido `_flush_saves()`. Ahora, únicamente los widgets que estuvieron en `_pending_saves` ejecutan la sincronización de su comando asociado.
- **Detección Previa de Cambios**: Antes de invocar `command_service.save_command()`, se comparan en memoria los atributos del comando existente (`trigger`, `response`, `is_active`, `cooldown`, `permission`, `aliases`). Si ningún parámetro cambió, se aborta la operación, previniendo escrituras a disco, recompilaciones de regex y la emisión innecesaria de `commands_changed`.
- **Complejidad Reducida**: Se redujo de $O(N)$ escrituras masivas y $N$ ráfagas de señales a $O(1)$ estrictamente acotado al widget modificado.

### 2. Higiene de Señales en `MusicController`
- **Eliminación de Suscripción Redundante**: Se eliminó la conexión duplicada de `self.command_service.commands_changed.connect(self._sync_switches_from_db)` en el constructor `__init__`.
- **Idempotencia**: Se protegió `_connect_signals()` con la bandera `_signals_connected` para garantizar que no se dupliquen slots ante llamadas repetidas de `attach_view()`.

### 3. Transacción Atómica Batch y Debouncing en Chat/TTS (`ChatService`)
- **Guardado Atómico con `save_all`**: Se refactorizó `ChatService.save_settings()` para empaquetar todas las configuraciones en un diccionario `batch` y guardarlas mediante una única transacción SQLite atómica (`storage.save_all`), reemplazando las 19 llamadas individuales a `save_bool`/`save_string` con un solo `executemany` y un único `conn.commit()`.
- **Persistencia Amortiguada de Audio (`set_volume` / `set_speed`)**:
  - Los cambios en el motor de audio (`self.tts.set_volume` y `self.tts.set_speed`) se aplican de forma inmediata en memoria ($O(1)$) para garantizar feedback sonoro en tiempo real.
  - La persistencia en disco se amortigua mediante un `QTimer` (`_audio_timer` con 300 ms de debounce) y el método `_flush_audio_params()`, evitando saturar el almacenamiento SQLite con decenas de commits por segundo al arrastrar sliders.

### 4. Actualización *In-Place* en Notificaciones Toast (`ModernToast`, `ToastManager`)
- **Actualización en Caliente (`ModernToast.update_content`)**: Se implementó el método `update_content()` para refrescar el título, mensaje, estado semántico (colores/borde), icono y duración sin destruir el widget ni recrear su jerarquía visual. Si el toast se encontraba en animación de salida (`_is_dismissing`), se cancela el cierre y vuelve a su estado visible.
- **Identificación Determinística por `tag`**: En lugar de heurísticas o análisis de cadenas de texto con palabras hardcodeadas (lo que rompería las reglas estrictas de i18n al cambiar de idioma), `ToastManager.show_toast()` ahora recibe un parámetro opcional `tag`. Si el toast más reciente posee el mismo `tag` (ej. `tag="minimize_tray"`, `tag="widget_shoutout"` o `tag="tts_enabled"`), se actualiza *in-place* sobre el mismo widget de forma instantánea ($O(1)$) y 100% agnóstica al idioma.
- **Resultado Visual**: Encender y apagar switches consecutivamente responde de forma instantánea (0 ms de overhead visual), sin colas acumuladas de toasts ni parpadeos o caídas de cuadros por segundo.

---

## Principios de Arquitectura Aplicados

| Principio | Aplicación en la Solución |
| :--- | :--- |
| **Big-O Efficiency** | Reducción de $O(N)$ a $O(1)$ en la sincronización de comandos de widgets, eliminando la cascada de señales innecesarias sobre el sistema. |
| **Atomic Transactions (Single-Pass)** | De 19 transacciones independientes `INSERT ... commit` a 1 transacción atómica batch con `executemany` en `SettingsStorage`. |
| **Separation of Responsibilities & UI Threading** | Separación del feedback interactivo inmediato en UI/audio del I/O de persistencia en disco mediante debouncing amortiguado. |
| **DRY & Signal Hygiene** | Centralización de la sincronización de comandos en `_sync_single_widget_command` y eliminación de conexiones duplicadas en `MusicController`. |

---

## Verificación y Pruebas Automatizadas

1. **Nueva Suite de Pruebas Unitarias**:
   - Se creó `resources/tests/unit/ui/test_toast_and_widget_sync.py` validando:
     - Actualización *in-place* de toasts ante toggles consecutivos sin incremento en la pila.
     - Detección diferencial de comandos en `WidgetController`, verificando que omita `save_command` cuando los atributos coinciden.
2. **Ejecución Completa de Pruebas**:
   - Se ejecutaron los 176 tests del repositorio (`pytest resources/tests/`), pasando el 100% de manera exitosa:
     ```text
     ============================ 176 passed in 10.84s =============================
     ```
