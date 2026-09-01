# Walkthrough: Corrección de RuntimeWarning libpyside en ModernToast

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_19.md`  
**Módulos Modificados:**
- [`frontend/navigation/toast_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py)

---

## 1. Resumen de Cambios

### A. Eliminación de `signal.disconnect()` Inválido
- En [`toast_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py#L70), se eliminó la llamada a `self.anim.finished.disconnect()`.
- Se configuró una conexión fija permanente en `__init__` con `self.anim.finished.connect(self._on_anim_finished)`.

### B. Control Seguro de Ciclo de Vida mediante Bandera
- Se introdujo `self._is_dismissing` para proteger contra dobles cierres o llamadas redundantes a `dismiss()`.
- Al culminar la animación de salida, `_on_anim_finished` verifica `_is_dismissing` y emite `self.expired.emit(self)`, erradicando el `RuntimeWarning: libpyside` en el log.

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/ui/ -q --tb=short
```
- **30/30 pruebas unitarias aprobadas al 100%**.
