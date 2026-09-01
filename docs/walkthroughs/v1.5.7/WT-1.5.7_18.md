# Walkthrough: Optimización de Notificaciones Toast y Eliminación de Latencia

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_18.md`  
**Módulos Modificados:**
- [`frontend/navigation/toast_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py)

---

## 1. Resumen de Cambios

### A. Eliminación de Subventanas Nativas de Windows
- En [`toast_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py#L12), se eliminó la bandera `setWindowFlags(Qt.WindowType.SubWindow)`.
- Los toasts ahora se renderizan directamente en el canvas acelerado de `MainWindow` como widgets hijos livianos, eliminando el overhead de 50-100ms que causaba la creación de handles Win32/DWM en Windows.

### B. Animaciones Rápidas y Deduplicación
- Se redujo la duración de la animación a `180ms` con curva `OutCubic` para una respuesta visual instantánea y fluida (60 FPS).
- Se implementó deduplicación inteligente en `ToastManager.show_toast()`: si se recibe una notificación idéntica en ráfaga (como al alternar un switch varias veces), se refresca el temporizador del toast visible en lugar de reconstruir y reanimar la pila completa.

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/ui/ -q --tb=short
```
- **30/30 pruebas unitarias de UI aprobadas al 100%**.
