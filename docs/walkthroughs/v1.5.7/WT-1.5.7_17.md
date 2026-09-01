# Walkthrough: Corrección de Advertencia QFont::setPointSize en ComboBoxes

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_17.md`  
**Módulos Modificados:**
- [`main.py`](file:///c:/Users/TheAn/Desktop/python/Kick/main.py)
- [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)

---

## 1. Resumen de Cambios

### A. Inicialización Explícita de `pointSize` en `main.py`
- En [`main.py`](file:///c:/Users/TheAn/Desktop/python/Kick/main.py#L138), se inicializó la fuente global de la aplicación con `QFont(font_family, 10)` y `app_font.setPointSize(10)`.
- Esto previene que `font.pointSize()` devuelva el valor no inicializado `-1` cuando Qt o sus delegados inspeccionan las propiedades tipográficas.

### B. Especificación de `font-size` en `theme.py` para `QComboBox`
- En [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py#L265), se incluyó `font-size: {text1}px;` en `QComboBox`, `QComboBox QAbstractItemView` y `QComboBox QAbstractItemView::item`.
- Ahora los menús flotantes de los ComboBox conocen con exactitud su métrica de texto sin requerir interpolaciones internas de Qt.

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/ui/test_frontend_common.py resources/tests/unit/ui/test_roles_integrity.py resources/tests/unit/ui/test_i18n_integrity.py -v
```
- **10/10 pruebas unitarias aprobadas al 100%**.
