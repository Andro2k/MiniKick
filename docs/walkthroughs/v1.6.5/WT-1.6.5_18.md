# Walkthrough Técnico — MiniKick v1.6.5 (Paso 18)

Se acotó la aplicación dinámica del tamaño de texto al árbol de widgets de la ventana principal. El cambio evita reemplazar la hoja de estilos de toda la aplicación cuando se cambia la preferencia en Ajustes.

---

## Novedades

- No se agregaron funciones nuevas.

## Mejoras

- El QSS dinámico se aplica a la ventana principal y sus widgets descendientes, reduciendo el ámbito de actualización de estilos.
- La hoja dinámica ya estaba memoizada; la mejora se enfoca en evitar reinstalarla en `QApplication`.

## Correcciones

- Se elimina la reinstalación global del QSS al cambiar el tamaño de texto desde Ajustes.

## Archivos Modificados

- `frontend/main_window.py`
- `docs/historial_crashes_y_errores.md`

## Verificación

- `python -m py_compile frontend/main_window.py`: correcto.
- `git diff --check`: correcto.
- Suite de calidad rápida: 11 de 12 controles aprobados; el control QSS reportó el rol sin uso `action_danger_outlined` en `frontend/common/theme.py`.
- No se ejecutaron pruebas automatizadas ni validación visual o medición de rendimiento en ejecución.
