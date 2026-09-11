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
- **Calibración y Auditoría de Iconos en `icon_manager.py` ([WT-1.5.9_03](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.5.9/WT-1.5.9_03.md))**:
  - Corrección de la detección de iconos huérfanos (como `message.svg`) aislando el escaneo al código fuente de producción (`frontend/`, `backend/`, `main.py`) para evitar contaminación por tests unitarios.
  - Extractor AST (`IconASTVisitor`) que descarta docstrings de módulos/funciones y fragmentos constantes de f-strings dinámicas (`JoinedStr`), eliminando falsos positivos.
  - Incorporación de opciones CLI completas (`--audit`, `--unused`, `--missing`, `--report`, `--clean`, `--force`, `--json`, `--strict`, `--include-tests`).
  - Limpieza segura de iconos sin uso con reporte de peso recuperable y confirmación interactiva.

---

### Configuración del Sistema y Autenticación (`frontend/views/` & `backend/services/`)
- **Selector de Navegador Web para OAuth y Enlaces ([WT-1.5.9_02](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.5.9/WT-1.5.9_02.md))**:
  - Nueva opción en [`SettingsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py) para elegir el navegador utilizado en inicios de sesión OAuth (Kick y Twitch), previsualización de overlays y enlaces externos.
  - Detección automática en Windows mediante el registro (`winreg`) y escaneo de rutas de navegadores estándar (Google Chrome, Microsoft Edge, Mozilla Firefox, Brave, Opera, Opera GX, Vivaldi).
  - Selector manual con botón de exploración rápida para elegir cualquier ejecutable personalizado (`.exe`).
  - Servicio desacoplado [`BrowserService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/browser_service.py) con memoización $\mathcal{O}(1)$ y mecanismo tolerante a fallos que recurre automáticamente al navegador del sistema ante cualquier error o ruta faltante.

---

### Integraciones de Streaming & Chat (`backend/providers/` & `backend/config/`)
- **Estabilización de TikTok Live Chat vía EulerStream ([WT-1.5.9_05](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.5.9/WT-1.5.9_05.md))**:
  - Corrección definitiva del error `InvalidStatusCode: server rejected WebSocket connection: HTTP 400` reportado al intentar conectar salas de TikTok Live.
  - Integración de firma autenticada y dedicada mediante `SIGN_API_KEY` en [`backend/config/api_keys.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/api_keys.py) y [`TikTokChatProvider`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/tiktok_chat_provider.py).
  - Soporte de sobrescritura de clave vía variable de entorno o archivo `.env` (`python-dotenv` cargado en [`main.py`](file:///c:/Users/TheAn/Desktop/python/Kick/main.py)).
  - Recepción fluida en tiempo real de eventos de chat estructurados (con usuario, avatar, comentario y roles) sin navegadores embebidos ni captchas visuales.
---

### Arquitectura y Estandarización de Código (`backend/interfaces/` & `docs/`)
- **Estandarización de Nombres de Archivos y Capa de Interfaces ([WT-1.5.9_06](file:///c:/Users/TheAn/Desktop/python/Kick/docs/walkthroughs/v1.5.9/WT-1.5.9_06.md))**:
  - Auditoría integral de los 179 archivos `.py` del proyecto documentada en [`docs/Correcciones.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/Correcciones.md) con tablero de control y justificación técnica para cada archivo.
  - Ejecución de la Fase 2 del plan de migración: estandarización completa de los 10 archivos de `backend/interfaces/` bajo la convención unificada `i_{dominio}.py` (`i_alerts.py`, `i_auth.py`, `i_browser.py`, `i_chat_provider.py`, `i_chat_service.py`, `i_instance.py`, `i_music_provider.py`, `i_settings.py`, `i_tts.py`, `i_updater.py`).
  - Actualización del punto de entrada [`backend/interfaces/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/interfaces/__init__.py) y suites de tests unitarios, garantizando 100% de compatibilidad sin romper dependencias.
