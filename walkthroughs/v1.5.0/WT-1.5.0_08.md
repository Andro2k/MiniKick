# Walkthrough: Corrección del Sistema de Exportación e Importación de Configuración (Backup)

## Resumen del Problema y Solución

Al intentar exportar la configuración a un archivo JSON desde Ajustes, el proceso fallaba con el error:
`TypeError: Object of type bytes is not JSON serializable`
generando un archivo JSON incompleto o truncado en el campo `thumbnail_bytes` de las recompensas de OBS.

---

### 1. Causa Raíz
- Las miniaturas de recompensas de OBS (`thumbnail_bytes`) se almacenan como datos binarios (`BLOB` / `bytes`) en la base de datos SQLite.
- La función estándar `json.dump()` en Python no puede serializar objetos binarios tipo `bytes`, provocando una excepción no controlada en [`backup_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/backup_service.py).

---

### 2. Solución Implementada ([`backup_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/backup_service.py))
- **Sanitización y Codificación Base64 en Exportación**:
  - Se implementó el método estático `_sanitize_for_json()` que recorre recursivamente diccionarios y listas, convirtiendo cualquier objeto `bytes` en una cadena codificada en **Base64** (`ASCII`), permitiendo la serialización JSON 100% segura.
- **Decodificación y Reconstrucción en Importación**:
  - Durante `import_from_json()`, las cadenas Base64 en `thumbnail_bytes` se decodifican de vuelta a `bytes` reales antes de persistirse en la base de datos SQLite.
- **Soporte de Programaciones de Stream (`stream_schedules`)**:
  - Se integró `schedule_storage` al servicio de respaldo para exportar e importar las programaciones automáticas de stream junto con el resto de la configuración.
- **Registro en el Contenedor ([`app_container_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_container_core.py))**:
  - Se vinculó `self.schedule_storage` en la instanciación de `BackupService`.

---

## Verificación

- Suite completa de pruebas unitarias (`uv run pytest`):
  - **54 / 54 pruebas aprobadas** (100% éxito), incluyendo [`tests/unit/test_backup_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/tests/unit/test_backup_service.py).
