# Walkthrough - WT-1.5.0_08: Rediseño Estilo Arc de Diálogos de Reporte de Bugs y Fallos (Crash)

## Resumen de Cambios

1. **Cumplimiento Estricto del Sistema de Temas (QSS & Roles)**:
   - Se eliminaron el **100% de llamadas a `setStyleSheet(...)` con CSS inline** en [`bug_report_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/bug_report_dialog.py) y [`crash_report_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/crash_report_dialog.py).
   - Todos los estilos y contenedores visuales ahora utilizan únicamente propiedades nativas de Qt (`setProperty("role", ...)` y `setProperty("state", ...)`), reutilizando las reglas globales centralizadas de [`theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) (`role="card"`, `role="banner_danger"`, `role="action_outlined"`, `role="action_accent"`, `role="action_danger_border"`).

2. **Rediseño Completo de `BugReportDialog`**:
   - Tarjetas superiores de severidad (*Baja*, *Media*, *Urgente*) con selector dinámico.
   - Área **Dropzone** para arrastrar y soltar imágenes con vista previa mini (thumbnail) y eliminación rápida `[X]`.
   - Disposición estructurada en 2 columnas y botón de envío dinámico según prioridad.

3. **Rediseño de `CrashReportDialog`**:
   - Tarjeta de advertencia superior utilizando `role="banner_danger"`.
   - Visor de traceback monospaciado con botón dinámico (`clipboard-text.svg`) para copiar el traceback completo al portapapeles.

4. **Internacionalización (i18n)**:
   - Sincronización completa de claves en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) y [`backend/config/default_en_locale.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/default_en_locale.py).

---

## Verificación

- **Pruebas Automatizadas (`pytest`)**: 35/35 pruebas pasadas.
- **Estilos Limpios**: Eliminado cualquier `setStyleSheet` inline en ambos diálogos.
