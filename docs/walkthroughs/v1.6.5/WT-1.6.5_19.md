# Walkthrough Técnico — MiniKick v1.6.5 (Paso 19)

Se añadió una forma cacheable de extender el QSS base con reglas personalizadas y se retiraron selectores de un rol que no tenía consumidores en la interfaz.

---

## Novedades

- `get_global_qss()` admite una tupla ordenada de fragmentos QSS personalizados. Los fragmentos se aplican después de los estilos base, para que puedan ajustar selectores o roles existentes.

  ```python
  get_global_qss(13, ('QPushButton[role="custom"] { color: #fff; }',))
  ```

## Mejoras

- La tupla de reglas personalizadas forma parte de la clave de `lru_cache`, por lo que las variantes repetidas reutilizan el QSS generado.
- `get_swatch_qss()` guarda hasta 128 variantes recientes de color, borde y radio para reutilizar estilos de swatches repetidos.
- Se retiraron las reglas de `action_danger_outlined`, que no tenía asignaciones en el frontend, incluida su referencia dentro del selector global de controles deshabilitados.

## Correcciones

- La auditoría de roles QSS vuelve a tener paridad entre los roles declarados y los usados por la interfaz.

## Archivos Modificados

- `frontend/common/theme.py`
- `docs/historial_crashes_y_errores.md`

## Verificación

- `python -m py_compile frontend/common/theme.py`: correcto.
- `git diff --check`: correcto.
- Generación aislada del QSS base y personalizado, orden de reglas y reutilización de caché: correcto.
- Suite de calidad rápida: 12/12 controles aprobados.
- PySide6 no está instalado en este entorno; falta validar el renderizado real de la variante personalizada.
