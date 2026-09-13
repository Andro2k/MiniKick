# Walkthrough WT-1.5.9_34: Diálogo Interactivo de Restauración Selectiva de Respaldos de Configuración

## Novedades
- **Diálogo Modal Moderno de Restauración (`ImportBackupModal`)**:
  - Implementado el nuevo componente modal interactivo `ImportBackupModal(ModernModal)` en `frontend/dialogs/import_backup_dialog.py`.
  - Al presionar el botón "Importar Configuración" en los Ajustes (`SettingsView`), el sistema ya no sobreescribe ciegamente todas las configuraciones. En su lugar, analiza la estructura del archivo y presenta un cuadro de diálogo donde el usuario puede elegir exactamente qué secciones desea restaurar.
  - El modal visualiza:
    - Ficha de metadatos con la versión de la copia (`_metadata.version`) y la fecha de exportación (`_metadata.exported_at` / `export_date`).
    - Barra de acciones rápidas con botones "Seleccionar Todo" y "Deseleccionar Todo".
    - Contenedor con scroll adaptativo para mostrar las secciones disponibles en el archivo de respaldo (`Ajustes Generales`, `Alertas de Eventos`, `Recompensas de Puntos`, `Comandos de Chat`, `Filtros Anti-Spam`, `Temporizadores`, `Programaciones de Transmisión` y `Widgets de OBS`).
    - Insignias tipo píldora (`role="badge"`) que indican el número exacto de elementos contenidos en cada sección del respaldo (ej. `4 elementos`, `1 elemento`).
    - Botón de confirmación reactivo que se deshabilita automáticamente si no hay ninguna sección seleccionada.
- **Inspección sin Efectos Secundarios (`inspect_backup`)**:
  - Añadido el método `inspect_backup(filepath: str) -> dict | None` en `BackupService` y expuesto a través de `SettingsService`. Permite inspeccionar el archivo `.json` de respaldo en tiempo constante $\mathcal{O}(1)$ respecto al árbol raíz, extrayendo metadatos y recuentos de elementos sin modificar el almacenamiento ni la base de datos de SQLite.
- **Importación Selectiva Parametrizada (`import_from_json(..., sections=...)`)**:
  - Actualizado `BackupService.import_from_json(filepath, sections=...)` y `SettingsService.import_settings(filepath, sections=...)` para admitir un parámetro opcional `sections: set[str] | list[str] | None`.
  - Cuando se define un conjunto de secciones (por ejemplo `{"alerts", "commands"}`), únicamente se importan e insertan los datos de esas secciones seleccionadas, preservando intactas las demás secciones y tablas de SQLite.
  - Mantiene retrocompatibilidad total: si `sections` es `None`, se importan todas las secciones detectadas tal como en versiones anteriores.

## Mejoras
- **Arquitectura Limpia y Separación de Responsabilidades (SoR)**:
  - `BackupService` permanece como servicio puro del dominio/datos sin dependencias de la interfaz gráfica (`PySide6`).
  - `SettingsController.handle_import()` actúa como orquestador desacoplado: solicita la ruta al usuario mediante `SettingsView.ask_open_path()`, delega la inspección en `SettingsService.inspect_backup()`, solicita la decisión al usuario a través de `SettingsView.show_import_backup_dialog()` y finalmente ejecuta la importación filtrada en `SettingsService.import_settings()`.
- **Eficiencia Big-O**:
  - **Inspección de Encabezados $\mathcal{O}(1)$**: `inspect_backup` solo consulta las claves de primer nivel del JSON cargado para medir su longitud (`len(dict)` o `len(list)`), sin iterar estructuras anidadas pesadas.
  - **Filtrado de Pasada Única $\mathcal{O}(k)$**: La importación selectiva comprueba la pertenencia en el conjunto de secciones seleccionadas (`set`) en tiempo constante $\mathcal{O}(1)$ por cada clave antes de procesar el bloque correspondiente.
- **Internacionalización Integral (i18n)**:
  - Cero cadenas de texto hardcodeadas. Se definieron todas las claves de localización en `locales/es.json` y `locales/en.json` bajo el namespace `settings.dialogs.import_modal` (títulos, descripciones detalladas por sección, sufijos singular/plural y botones).
  - Verificado mediante los tests de integridad automatizados `test_i18n_keys_used_in_code_exist` y `test_i18n_key_parity`.
- **Cumplimiento de Roles de Tema QSS**:
  - Integración exclusiva con los roles válidos del diseño de MiniKick (`h3`, `body`, `caption`, `badge`), verificado con el validador estricto `test_all_used_roles_exist_in_theme`.

## Correcciones
- **Cancelación Segura del Flujo de Importación**:
  - Corregido el flujo para que, si el usuario cancela el diálogo modal de selección de respaldo o cierra la ventana, la operación se descarte de forma limpia sin emitir señales de recarga (`backup_restored`) ni alterar la base de datos de SQLite.
- **Validación de Archivos Dañados o No Válidos**:
  - Si el archivo JSON seleccionado está corrupto, truncado o no contiene un objeto JSON en su raíz, `inspect_backup` captura la excepción, registra el error y el controlador muestra una notificación toast de tipo `danger` (`settings.status.import_error`) informando adecuadamente al usuario sin provocar excepciones no controladas.
