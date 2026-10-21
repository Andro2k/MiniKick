# Walkthrough Tecnico - MiniKick v1.6.5 (Paso 17)

Se corrigio la incompatibilidad entre el nombre tipografico esperado por el codigo y el token definido por la refactorizacion del tema.

## Novedades

- Se conserva el nombre `Typography.FAMILY` como alias compatible del token `Typography.FONT_FAMILY`.

## Mejoras

- Ambos nombres comparten un unico valor, evitando duplicar configuracion tipografica.

## Correcciones

- Se evita el `AttributeError` durante la importacion del tema.
- Se elimina texto accidental que contaminaba el bloque QSS de accion primaria.

## Archivos Modificados

- `frontend/common/theme.py`
- `docs/historial_crashes_y_errores.md`

## Verificacion

- `python -m py_compile frontend/common/theme.py`.
- Comprobacion de los alias y del texto QSS.
- No se ejecuto la suite de pruebas automatizadas.
