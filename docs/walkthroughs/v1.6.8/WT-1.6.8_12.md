# Walkthrough Técnico — MiniKick v1.6.8 (Paso 12)

Los archivos de traducción pasan de `locales/` a `assets/locales/`, de modo que todos los recursos estáticos viven bajo `assets/` (referencia de organización: `assets/` de sonora).

---

## Novedades

- **`assets/locales/`:** `en.json` y `es.json` se mueven con `git mv`, por lo que el historial de cada archivo se conserva. `locales/` desaparece de la raíz.

## Mejoras

- **`TranslationService`:** el valor por defecto de `locales_dir` pasa a `os.path.join("assets", "locales")`. Se resuelve igual en desarrollo y en el ejecutable (`sys._MEIPASS`).
- **`MiniKick.spec`:** se elimina la entrada `datas` de `locales`; el bundle ya incluye `assets/` completo y, con él, `assets/locales`.
- **Herramientas y pruebas:** `project_translation_integrity_auditor.py` (raíz del proyecto y rutas de `en.json` / `es.json`), el mensaje de `frontend_hardcoded_text_auditor.py` y `test_commands_help_and_backup.py` usan la nueva ruta.
- **Documentación vigente:** `README.md` (tabla de paquetes), `.agents/rules/minikick.md`, `.agents/skills/minikick-quality-auditor/SKILL.md`, `docs/designs/webhook_delivery_service.md` y los traspasos 2 y 3 citan `assets/locales/*.json`.
- **Verificación:** `resources/tests` da 346 aprobadas; `TranslationService` carga `en` y `es` desde la nueva ruta; `project_quality_suite.py --quick` pasa 13 de 14 auditores.

## Limitaciones conocidas

- `Frontend Qt Windows` (`frontend_qt_window_lifecycle_auditor.py`) falla también sin estos cambios, así que no se relaciona con el movimiento.
- Los `IGNORED_DIRS` de los auditores conservan `"locales"`: sigue excluyendo la carpeta por nombre en su nueva ubicación, por lo que no se modificaron.
- Los walkthroughs anteriores y `docs/historial_crashes_y_errores.md` conservan la ruta antigua por ser registro histórico.
- No se probó un build de PyInstaller ni el instalador en Windows; conviene generar uno para confirmar que `assets/locales` queda en `_internal`.
- Sonora separa los idiomas en subcarpetas (`assets/i18n/<idioma>/`) y agrupa iconos por plataforma; aquí solo se movió `locales`, sin cambiar el formato de los archivos.
