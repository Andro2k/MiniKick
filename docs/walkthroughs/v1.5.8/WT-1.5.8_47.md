# Walkthrough - Respaldo Completo de Configuración: Alertas, Widgets y Paridad de Plataformas (v1.5.8_47)

## 1. Resumen y Objetivos

Se completó y robusteció la arquitectura del servicio de respaldos (`BackupService` accesible desde **Ajustes > Respaldos**), incorporando la exportación e importación integral de las **Alertas de Eventos** (`alert_configs`) y los **Widgets de OBS** (`widgets_config`), y preservando con precisión los filtros de plataformas en comandos (`apply_kick`, `apply_twitch`, `apply_youtube`, `apply_tiktok`) y temporizadores (`apply_kick`, `apply_twitch`).

---

## 2. Diagnóstico y Hallazgos de la Auditoría

Al auditar la persistencia de MiniKick y comparar contra el esquema SQLite:

1. **Alertas Faltantes (`alert_configs`)**:
   - Toda la configuración visual y de audio de las alertas de Kick y Twitch (Follow, Sub, Resub, Sub Gift, Raid, Cheer) no estaba integrada en `BackupService`, provocando que el usuario perdiera sus estilos, plantillas de texto y medios en respaldos.
2. **Widgets de OBS Faltantes (`widgets_config`)**:
   - Los widgets (Contador de muertes, Marcador/Score, Encuestas, Mensaje fijado, Shoutout, Emote Explosion y Combo) no estaban conectados a `BackupService`.
3. **Pérdida de Filtros de Plataforma en Restauración**:
   - En `chat_commands` y `chat_timers`, las banderas de habilitación por plataforma se exportaban pero se ignoraban en el momento de `import_from_json`, reseteando las asignaciones a valores por defecto.

*(Nota de Seguridad: Los tokens de autenticación OAuth de Kick y Twitch continúan excluidos intencionalmente para prevenir fugas de credenciales en archivos JSON compartidos).*

---

## 3. Modificaciones Implementadas

### A. [backup_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/backup_service.py)
- **Inyección de Dependencias**: El constructor ahora acepta `alert_storage` y `widgets_storage`.
- **Exportación (`export_to_json`)**:
  - `data["widgets"] = self.widgets_storage.load_all_widgets()`
  - `data["alerts"] = [cfg.to_dict() for cfg in self.alert_storage.load_all().values()]`
- **Importación (`import_from_json`)**:
  - **Widgets**: Itera sobre `data["widgets"]` (soportando formato dict o list) e invoca `self.widgets_storage.save_widget(...)`.
  - **Alertas**: Deserializa usando `AlertConfig.from_dict(...)` y ejecuta `self.alert_storage.save_all(...)`.
  - **Comandos**: Pasa explícitamente `apply_kick`, `apply_twitch`, `apply_youtube` y `apply_tiktok` a `self.commands_storage.save_command(...)`.
  - **Temporizadores**: Pasa explícitamente `apply_kick` y `apply_twitch` a `self.timers_storage.save_timer(...)`.

### B. [app_container_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_container_core.py)
- Se enlazaron `alert_storage=self.alert_storage` y `widgets_storage=self.widgets_storage` en la inicialización de `BackupService`.

### C. [test_backup_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/database/test_backup_service.py)
- Se crearon `DummyAlertStorage`, `DummyWidgetsStorage` y `DummyTimersStorage` con validaciones completas:
  1. `test_backup_service_export_and_import_with_bytes`: Valida el flujo completo de exportación e importación con alertas, widgets, comandos (con `apply_kick`, `apply_twitch`, `apply_youtube`, `apply_tiktok`) y temporizadores exclusivos de **Kick y Twitch** (`apply_kick`, `apply_twitch`), verificando la preservación de bytes de thumbnails y la integridad de los datos.
  2. `test_backup_service_legacy_backup_compatibility`: Valida la compatibilidad retroactiva importando un archivo JSON legado sin las claves `"alerts"` ni `"widgets"`.

---

## 4. Análisis de Arquitectura y Big-O

- **Complejidad Temporal**: $\mathcal{O}(N)$ en una única pasada lineal sobre los registros de configuración, sin bucles anidados.
- **Complejidad Espacial**: $\mathcal{O}(N)$ para la serialización a JSON.
- **Defensa de Interfaces (Principio de Sustitución de Liskov)**: Se añadió un fallback defensivo con `try/except TypeError` en `save_command` y `save_timer` para que el servicio soporte limpiamente tanto implementaciones actuales con kwargs de plataforma como implementaciones legadas o mocks de prueba.
- **Retrocompatibilidad**: Los backups creados en versiones anteriores que carecen de las secciones `"alerts"` o `"widgets"` se importan de forma segura sin interrupciones ni excepciones.

---

## 5. Verificación
- **Pruebas Automatizadas**:
  - `resources/tests/unit/database/test_backup_service.py` (2/2 PASSED en 0.07s)
  - `resources/tests/unit/core/test_app_container.py` (2/2 PASSED)
  - `resources/tests/unit/ui/test_settings_controller.py` (3/3 PASSED)
