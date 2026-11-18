# Walkthrough Técnico — MiniKick v1.6.8 (Paso 28)

Se corrigió la comparación de versiones del actualizador. `UpdateManager.check_for_updates` comparaba las versiones como texto, y con ese método `"v1.6.10" > "v1.6.9"` es `False`, así que al llegar a una versión con un componente de dos dígitos MiniKick habría dejado de avisar de la actualización.

---

## Correcciones

- `updater_service.py`: nueva función `_version_key`, que extrae los números de la versión (`v1.6.10` → `(1, 6, 10, 0)`) y los rellena con ceros, de modo que `1.6` y `1.6.0` sean iguales.
- `check_for_updates` compara ahora con `_version_key`. Un tag sin números (por ejemplo `latest`) nunca se considera más nuevo.
- Los sufijos de pre-lanzamiento (`-beta`) no se interpretan: `v1.7.0-beta` cuenta como `1.7.0`.

## Archivos afectados

- `backend/services/updates/updater_service.py` (parche `0001`)
- `resources/tests/test_update_manager_version.py` (parche `0001`, nuevo)
- `docs/walkthroughs/v1.6.8/WT-1.6.8_28.md` (parche `0002`)

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `pytest test_update_manager_version.py test_windows_installer.py` | 10 aprobadas, 0 fallidas |
| `ruff check` sobre los archivos tocados | Sin errores |
| `project_quality_suite.py --quick` | 5 advertencias de `ModernButton` sin `parent`, las mismas que antes del cambio |
