# Walkthrough - Diagnóstico de Log y Prevención de Crash en BugReportWorker (v1.5.8_42)

## 1. Análisis del Reporte de Error y Diagnóstico del Log

### A. La Causa del Crash
En el log reportado por el usuario (`minikick_TheAndro2K_v1.5.8 (1).log`), el fallo fatal se debió a:
```text
[2026-09-07 16:57:18] [CRITICAL] [Qt] QThread: Destroyed while thread 'Worker_Bug_Report' is still running
```
**¿Por qué ocurrió?**
1. A las `16:57:05`, tras probar música y notar un retraso al pedir canciones con `!sr`, el usuario abrió la pestaña `Developer` y abrió el modal de **Bug Report**.
2. Al pulsar *Enviar*, se inició el hilo en segundo plano `BugReportWorker` (`Worker_Bug_Report`) para empaquetar el log y enviarlo por Webhook a Discord con `timeout=15`.
3. Si el usuario cerraba o cancelaba el modal mientras la petición HTTP aún estaba en curso (o al cerrarse el diálogo tras la señal `finished` antes de que el runtime de C++ terminara de desalojar el hilo), Python recolectaba la instancia de `BugReportDialog` y `self.worker`.
4. En Qt, destruir el wrapper en Python de un `QThread` activo detiene inmediatamente la aplicación mediante `std::terminate` / `abort()`.

### B. El "Retraso" en los Mensajes de Kick
En el registro entre `16:55:40` y `16:56:50`:
```text
 16:56:25 Streamer TheAndro2K !sr i have become animal
 16:56:32 Bot @MiniKick 🔍 Buscando 'i have become animal' en YouTube...
 16:56:34 Bot @MiniKick 🎵 Añadida a la cola: Three Days Grace - Animal I Have Become...
 16:56:37 Streamer TheAndro2K xd
 16:56:50 Streamer TheAndro2K que paso aqui xd
```
1. **Búsqueda de YouTube (`yt-dlp`)**: El comando `!sr` realiza la búsqueda y resolución de metadata en YouTube, lo cual tomó 7 segundos en completarse y responder al chat.
2. **Descarga en paralelo de Audio**: Paralelamente, `YouTubeResolveWorker` estaba descargando a disco el audio de 10 MB a 15 MB/s, lo que satura temporalmente la concurrencia de red en Linux.
3. **Recepción de mensajes**: Los mensajes como `xd` (16:56:37) y `que paso aqui xd` (16:56:50) fueron recibidos y reproducidos por el sintetizador TTS casi de inmediato (pre-descarga de TTS en 0.87s - 0.99s).

---

## 2. Solución Implementada para el Crash

Se implementó el patrón de **Retiro Seguro de Workers** tanto en [bug_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/bug_report_dialog.py) como en [crash_report_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/crash_report_dialog.py):

1. **Registro Global de Workers Activos (`_ACTIVE_BUG_WORKERS` / `_ACTIVE_CRASH_WORKERS`)**:
   - Mantiene una referencia fuerte en Python de los hilos de reporte activos hasta que completan su ejecución y emiten `finished`.
   - Evita que el Garbage Collector destruya prematuramente el objeto de C++ mientras el thread de sistema operativo sigue ejecutándose.

2. **Desconexión Segura en `closeEvent` y `reject`**:
   - Si el usuario cancela o cierra el modal a mitad de envío, se desconectan las señales que interactúan con la interfaz visual (`_on_worker_finished`) y el hilo concluye de forma segura en segundo plano sin congelar la interfaz ni tumbar la aplicación.

3. **Espera de Finalización (`wait`)**:
   - En `_on_worker_finished`, antes de ejecutar `self.accept()`, se invoca `self.worker.wait(1000)` para garantizar que el bucle de ejecución del hilo finalice limpiamente antes del cierre del modal.

---

## 3. Verificación Automatizada

Se añadió la prueba `test_bug_report_dialog_worker_lifecycle_safety` en [test_dialogs.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_dialogs.py):
```powershell
uv run pytest resources/tests/unit/ui/test_dialogs.py
```
Resultado: **14 passed in 0.38s**.
