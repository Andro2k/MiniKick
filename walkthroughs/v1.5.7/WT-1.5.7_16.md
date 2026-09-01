# Walkthrough: Ajuste de Geometría y Eliminación de Advertencias en Diálogos Modales

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_16.md`  
**Módulos Modificados:**
- [`frontend/dialogs/base_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py)

---

## 1. Resumen de Cambios

### A. Sincronización de Geometría Previa al Centrado en `showEvent`
- En [`base_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py#L56), se añadió `self.adjustSize()` antes de calcular las coordenadas globales de centrado en `ModernFramelessShell.showEvent`.
- Esto garantiza que `self.height()` y `self.width()` reflejen con exactitud la altura real requerida por los widgets del layout antes de enviar las coordenadas de posición a Windows.

### B. Ajuste Dinámico en Asistentes
- Se añadió `self.adjustSize()` en `ModernWizardPanel._update_step_ui()` al cambiar de página en los wizards de configuración (`RewardsConfigWizard`, `TimerConfigWizard`).
- Se configuró `setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)` en el contenedor principal de los modales para una adaptación fluida.

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/ui/test_dialogs.py -v
```
- **4/4 pruebas unitarias de diálogos aprobadas al 100%**.
