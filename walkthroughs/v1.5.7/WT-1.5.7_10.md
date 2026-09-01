# Walkthrough: Rediseño Moderno y Formato de Lista para Alerta de Permisos en Dashboard

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_10.md`  
**Módulos Modificados:**
- [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)
- [`frontend/views/dashboard_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py)
- [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
- [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)

---

## 1. Resumen de Cambios

### A. Estilo de Tarjeta Satinada Elegante
- Se reemplazó el estilo rojo neón saturado (`role="banner_danger"`) por una tarjeta moderna y limpia (`role="banner_scope_card"`) con fondo neutro `#121115`, bordes sutiles adaptados con acento de plataforma (`state="kick"` o `state="twitch"`) y espaciado interno amplio.
- Se integraron botones temáticos de plataforma (`action_kick` y `action_twitch`) para una estética cohesionada y premium.

### B. Formato de Lista Estructurada en Viñetas
- Se eliminó el párrafo corrido con comas.
- Ahora los permisos se despliegan en una lista con viñetas (`•`) con tipografía Google Sans, título destacado, subtítulo explicativo y espaciado vertical cómodo (`margin-bottom: 3px`, `line-height: 135%`).

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/ui/ resources/tests/unit/core/ -q --tb=short
```
- **40/40 tests aprobados (100% PASSED)**.
- 100% de paridad en claves i18n y validación de roles/estados en `theme.py`.
