# Walkthrough Técnico — MiniKick v1.6.8 (Paso 16)

Ajustes posteriores al cambio de iconos de marca por iconos de bloque (`block-*`): se deja en verde la cuadrícula de iconos y la prueba de resolución por packs.

---

## Mejoras

- **`dots-horizontal-outline.svg`:** el icono nuevo llegaba con `width`/`height` `1em` y `project_icon_grid_tool.py --check` lo marcaba como `LIENZO`. Se normalizó con `--fix` a `24×24`; el render no cambia (ya estaba centrado y dentro del área útil de 22u).
- **`test_icon_pack_resolution.py`:** la prueba con assets reales busca `block-kick.svg` en `common/` (antes `brand-kick.svg`, renombrado).
- **Verificación:** `project_icon_grid_tool.py --check` en 0 y `resources/tests` da 413 aprobadas y 1 fallida (ver Limitaciones).

## Limitaciones conocidas

- `test_sidebar_and_icon_only_buttons_use_explicit_icon_sizes` falla desde el commit de los iconos de bloque: ese commit eliminó `setIconSize` en `Sidebar` (logo y botones de navegación), en `configure_icon_only_button` y en `ModernButton` (`__init__` y `setIcon`). Con ello los botones quedan con el tamaño por defecto de Qt (16 en lugar de `ICON_NAV`=18 / `ICON_FEATURE`) y el parámetro `icon_size` de `ModernButton` ya no se aplica. Pendiente de decidir si se restauran esas líneas o se actualiza la prueba; no se modificó aquí.
- `Frontend Qt Windows` sigue fallando como antes de estos cambios.
