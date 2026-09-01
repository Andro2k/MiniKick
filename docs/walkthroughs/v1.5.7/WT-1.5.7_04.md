# Walkthrough: Motor de Notificaciones Toast de Alto Rendimiento sin Latencia y Corrección libpyside

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_04.md`  
**Módulos Involucrados:**
- `frontend/navigation/toast_component.py`
- `frontend/views/chat_view.py`
- `frontend/components/chat/tts_settings.py`

---

## 1. Resumen de Objetivos y Cambios

### A. Eliminación de Latencia en Notificaciones Toast
- **Problema:** Al activar y desactivar switches rápidamente (como en los ajustes de TTS en `ChatView`), la aparición de notificaciones Toast generaba congelamientos perceptibles de 50 a 100 ms en la interfaz.
- **Causa Raíz:** Cada notificación utilizaba `self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)`, lo que forzaba al Desktop Window Manager (DWM) de Windows a crear y registrar una ventana nativa de sistema operativo en cada invocación.
- **Solución:**
  - Se transformó `ModernToast` en un widget hijo ligero renderizado directamente sobre la jerarquía visual de `MainWindow`.
  - Se optimizó la animación de entrada/salida a una duración de 180 ms con aceleración cúbica (`QEasingCurve.Type.OutCubic`).
  - Se implementó deduplicación por ráfaga en `ToastManager.show_toast()`, actualizando el toast activo en lugar de recrear la pila de animación.

### B. Corrección de `RuntimeWarning: libpyside` en Desconexión de Señales
- **Problema:** El log registraba advertencias `RuntimeWarning: libpyside: Failed to disconnect (None) from signal 'finished()' on 'QPropertyAnimation'`.
- **Causa Raíz:** Desconexión dinámica de callbacks anónimos o ya ejecutados en la animación.
- **Solución:**
  - Se reemplazó el patrón dinámico por una conexión fija permanente `self.anim.finished.connect(self._on_anim_finished)` y un flag de estado booleano atómico `self._is_dismissing`.

---

## 2. Verificación
- Pruebas unitarias de toasts y componentes de interfaz en `resources/tests/unit/ui/` aprobadas.
- Respuesta instantánea al interactuar continuamente con switches y controles visuales.
