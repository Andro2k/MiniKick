# WT-1.5.9_02: Selector de Navegador Web para OAuth y Enlaces Externos

- **Versión**: v1.5.9
- **Tipo**: Feature / Architecture Enhancement
- **Componentes**:
  - [`backend/interfaces/browser_interface.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/interfaces/browser_interface.py)
  - [`backend/services/system/browser_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/browser_service.py)
  - [`backend/services/system/settings_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/settings_service.py)
  - [`backend/services/auth/oauth_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py)
  - [`backend/controllers/settings_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/settings_controller.py)
  - [`backend/controllers/alerts_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/alerts_controller.py)
  - [`frontend/views/settings_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py)
  - [`frontend/views/dashboard_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py)
  - [`frontend/dialogs/release_notes_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/release_notes_dialog.py)
  - [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) / [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) / [`backend/config/default_en_locale.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/default_en_locale.py)

---

## 1. Descripción del Problema y Requerimiento

Los flujos de autenticación OAuth (Kick y Twitch), así como la visualización de overlays en el navegador y los hipervínculos externos (canales de streamer, notas de versión en GitHub), abrían exclusivamente el navegador configurado por defecto en el sistema operativo mediante llamadas a `webbrowser.open(url)` o `QDesktopServices.openUrl(url)`.

El usuario requería la capacidad de:
1. Elegir en qué navegador web se abren las solicitudes OAuth y demás enlaces de la aplicación desde [`SettingsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py).
2. Ver automáticamente una lista de los navegadores instalados en su equipo (ej. Google Chrome, Microsoft Edge, Brave, Firefox, Opera, etc.).
3. Tener la opción de examinar y seleccionar manualmente cualquier ejecutable personalizado (`.exe`) en caso de navegadores portables o no registrados en el sistema.

---

## 2. Solución Aplicada y Arquitectura

### A. Capa de Interfaces y Desacoplamiento (Dependency Inversion)
- Se definió el protocolo [`IBrowserService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/interfaces/browser_interface.py) en la capa de abstracción, asegurando que ninguna lógica de negocio o de presentación dependa directamente de la implementación concreta del sistema operativo.

### B. Servicio de Navegadores (`BrowserService`)
- Se implementó [`BrowserService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/browser_service.py) en la capa de servicios del sistema:
  - **Detección Automática**: En Windows, inspecciona `winreg` bajo `HKCU` y `HKLM` en `SOFTWARE\Clients\StartMenuInternet` (y `WOW6432Node`), complementado con escaneo de rutas estándar para Google Chrome, Microsoft Edge, Mozilla Firefox, Brave, Opera, Opera GX y Vivaldi. En sistemas Unix/macOS, resuelve binarios mediante `shutil.which`.
  - **Memoización y Eficiencia Big-O**: El resultado de la detección se almacena en caché en una sola pasada $\mathcal{O}(k)$ (donde $k$ es el número de claves/rutas conocidas), garantizando que las llamadas subsecuentes se resuelvan en tiempo $\mathcal{O}(1)$.
  - **Tolerancia a Fallos**: Si un ejecutable configurado por el usuario no existe en disco o falla al invocarse, el servicio registra la advertencia y recurre de manera transparente al navegador predeterminado del sistema (`webbrowser.open(url)`), impidiendo que el usuario quede atrapado sin poder autenticarse.
  - **Persistencia**: Se sincroniza a través de `settings_storage` con la clave `"app_browser_path"`, con valor por defecto `"default"`.

### C. Integración en el Contenedor y Flujos OAuth
- [`AppContainerCore`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_container_core.py) inicializa `BrowserService` y lo inyecta en:
  - [`KickAuthManager`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py) y [`TwitchAuthManager`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py), quienes a su vez lo transmiten al servidor de captura [`OAuthCallbackServer.capture_auth_code`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py).
  - [`SettingsController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/settings_controller.py) y [`AlertsController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/alerts_controller.py).
  - Vistas con enlaces externos: [`DashboardView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py) y [`ReleaseNotesDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/release_notes_dialog.py).

### D. Experiencia de Usuario en `SettingsView`
- Se agregó una nueva fila `SettingRow` con el icono `link.svg` en la tarjeta de sistema de [`SettingsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py):
  - **Selector desplegable (`NoWheelComboBox`)**:
    - `"Predeterminado del sistema"` (valor `default`).
    - Navegadores detectados en la máquina (con su nombre comercial y ruta completa).
    - Opción personalizada si la ruta guardada es externa (`"Personalizado (nombre.exe)"`).
    - Opción `"Examinar ejecutable..."` (`__browse__`).
  - **Botón de Exploración Rápida (`ModernButton`)**:
    - Botón lateral con icono `folder-open.svg` y rol `action_neutral_border`.
    - Abre un diálogo nativo [`QFileDialog.getOpenFileName`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py) filtrando archivos ejecutables (`*.exe`).
    - Si el usuario selecciona un ejecutable, se agrega dinámicamente al combo, se selecciona y se emite la señal `browser_changed(path)`.
    - Si el usuario cancela la selección, el combobox restaura de forma limpia la opción previamente seleccionada sin emitir cambios innecesarios.

### E. Internacionalización Estricta (i18n)
- 100% de los textos nuevos se estructuraron en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) y el diccionario fallback [`default_en_locale.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/default_en_locale.py):
  - Claves en `settings.system`: `browser_title`, `browser_desc`, `browser_default`, `browser_custom`, `browser_browse`, `browser_dialog_title`, `browser_dialog_filter`.
  - Claves en `settings.status`: `browser_changed`, `browser_changed_msg`.
  - Cero strings hardcodeados o cadenas de fallback inline con `or`.

---

## 3. Análisis de Eficiencia Big-O

| Operación | Complejidad Previa | Complejidad Nueva | Optimización Realizada |
|---|---|---|---|
| Detección de navegadores instalados | N/A | $\mathcal{O}(k) \to \mathcal{O}(1)$ | Escaneo único con memoización en memoria en `BrowserService._installed_cache`. |
| Deduplicación de rutas detectadas | N/A | $\mathcal{O}(1)$ por elemento | Uso de estructura nativa `set` con normalización `os.path.normpath().lower()`. |
| Población de combobox en UI | N/A | $\mathcal{O}(n)$ | Recorrido lineal único de navegadores ($n \le 10$) evitando recálculos redundantes. |
| Ejecución del navegador | $\mathcal{O}(1)$ | $\mathcal{O}(1)$ | Despacho directo mediante `subprocess.Popen([browser_path, url])` sin bloqueo de hilos. |

---

## 4. Verificación y Resultados

1. **Suite de Pruebas Unitarias**:
   ```bash
   uv run pytest resources/tests/unit/services/test_browser_service.py resources/tests/unit/ui/test_settings_controller.py resources/tests/unit/ui/test_i18n_integrity.py resources/tests/unit/ui/test_roles_integrity.py
   ```
   **Resultado**: `16 passed in 1.85s` ✅.
   - `test_browser_service_default_path`: Aprobado.
   - `test_browser_service_set_browser_path`: Aprobado.
   - `test_browser_service_memoization`: Aprobado.
   - `test_browser_service_open_default`: Aprobado.
   - `test_browser_service_open_custom_exists`: Aprobado.
   - `test_browser_service_open_custom_missing_fallback`: Aprobado.
   - `test_browser_service_open_custom_exception_fallback`: Aprobado.
   - `test_settings_controller_browser_handling`: Aprobado.
   - `test_i18n_files_exist_and_valid_json`: Aprobado.
   - `test_i18n_key_parity`: Aprobado.
   - `test_i18n_keys_used_in_code_exist`: Aprobado.
   - `test_roles_integrity`: Aprobado.

2. **Auditoría de Roles y Estados QSS**:
   ```bash
   uv run .\resources\tools\role_manager.py --json
   ```
   **Resultado**:
   - `missing_roles`: `{}`
   - `missing_states`: `{}`
   - `unused_roles`: `{}`
   - `unused_states`: `{}`
   - 100% de sincronización estética cumplida.
