# Walkthrough Técnico - v1.6.4 / WT-1.6.4_04

**Versión**: v1.6.4  
**Fecha**: 2026-10-15  
**Origen**: Diagnóstico Pyrefly `unknown-name` en la resolución de rutas de iconos.

---

## Novedades

No se agregan funciones nuevas.

## Mejoras

El módulo de rutas ahora declara un logger con el patrón de nombres usado por el resto de `frontend/common`,
permitiendo registrar advertencias con contexto cuando no se encuentra un icono.

## Correcciones

Se corrigió el nombre `logger` no definido en `resolve_icon_path`. Pyrefly reportaba `unknown-name` y la ruta
de icono faltante podía provocar `NameError` al intentar emitir el warning. El módulo ahora importa `logging`
y crea `logger = logging.getLogger("minikick.paths")`.

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| `frontend/common/paths.py` | Importación de `logging` y declaración del logger del módulo |
| `docs/historial_crashes_y_errores.md` | Registro del incidente INC-024 y referencia al walkthrough |

---

## Verificación

- Se revisó que la referencia de `resolve_icon_path` tenga ahora una declaración de logger en el mismo módulo.
- No se ejecutaron pruebas automatizadas.
