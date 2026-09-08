# Notas de la Versión - MiniKick v1.5.9

## Resumen de Cambios
Esta versión introduce mejoras y correcciones críticas en las herramientas de desarrollo y auditoría del sistema de diseño QSS, asegurando la sincronización estricta entre los selectores de estilo y el código frontend.

---

### Herramientas de Auditoría y Calidad (`resources/tools/`)
- **Calibración de `role_manager.py` ([WT-1.5.9_01](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.5.9/WT-1.5.9_01.md))**:
  - Detección precisa de roles y estados QSS huérfanos/sin uso definidos en [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py).
  - Trazabilidad y reporte exacto del número de línea donde se encuentra definido cada selector no utilizado (por ejemplo, `QFrame[role="searchable_combo_divider"]` en línea 314).
  - Motor de inspección AST mejorado para capturar ternarios condicionales, argumentos específicos (`btn_role`, `icon_role`, `button_role`) y llamadas a helpers de estado sin falsos positivos.
  - Nuevas opciones CLI: `--unused`, `--missing` y `--strict` (retorno de código de salida 1 ante selectores huérfanos).

---

### Configuración del Sistema y Autenticación (`frontend/views/` & `backend/services/`)
- **Selector de Navegador Web para OAuth y Enlaces ([WT-1.5.9_02](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.5.9/WT-1.5.9_02.md))**:
  - Nueva opción en [`SettingsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py) para elegir el navegador utilizado en inicios de sesión OAuth (Kick y Twitch), previsualización de overlays y enlaces externos.
  - Detección automática en Windows mediante el registro (`winreg`) y escaneo de rutas de navegadores estándar (Google Chrome, Microsoft Edge, Mozilla Firefox, Brave, Opera, Opera GX, Vivaldi).
  - Selector manual con botón de exploración rápida para elegir cualquier ejecutable personalizado (`.exe`).
  - Servicio desacoplado [`BrowserService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/browser_service.py) con memoización $\mathcal{O}(1)$ y mecanismo tolerante a fallos que recurre automáticamente al navegador del sistema ante cualquier error o ruta faltante.

