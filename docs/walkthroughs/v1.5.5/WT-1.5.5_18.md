# Walkthrough 1.5.5_18: Tarjeta de Notificación de Actualización en Sidebar

## Descripción General
Se rediseñó por completo la notificación de nuevas versiones en la barra lateral (`Sidebar`), transformando el botón simple anterior en una tarjeta moderna e interactiva inspirada en la referencia visual solicitada, con icono en contenedor estilizado, botón de cierre rápido ('x'), título en negrita, versión detectada y botón de acción directa ("Actualizar ahora").

---

## Cambios Realizados

### 1. Internacionalización (i18n)
- **Archivos**: [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json), [default_en_locale.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/default_en_locale.py)
- Se añadieron las siguientes claves en `sidebar.update_card`:
  - `title`: `"¡Nueva versión disponible!"` / `"New Version Available!"`
  - `desc`: `"Versión {version} lista para instalar"` / `"Version {version} ready to install"`
  - `btn`: `"Actualizar ahora"` / `"Update Now"`
  - `tooltip_dismiss`: `"Descartar aviso"` / `"Dismiss notification"`
  - `tooltip_collapsed`: `"Actualización disponible: {version}"` / `"Update available: {version}"`

### 2. Estilos y Sistema Visual QSS
- **[theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)**:
  - Añadidos roles de estilo:
    - `QFrame[role="update_banner_card"]`: Fondo oscuro con borde sutil y esquinas redondeadas.
    - `QFrame[role="update_icon_box"]`: Contenedor cuadrado con brillo verde y borde acentuado.
    - `QPushButton[role="btn_dismiss"]`: Botón transparente de cierre con efecto hover.

### 3. Componente Sidebar
- **[sidebar_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py)**:
  - Implementado `_setup_update_card`:
    - Fila superior con caja de icono (`cloud-download.svg`) y botón 'x' para descartar la notificación en la sesión actual.
    - Textos informativos dinámicos (`lbl_update_title` y `lbl_update_desc`).
    - Botón de acción destacado (`btn_update_action`).
  - **Modo Colapsado**: Se añadió `btn_collapsed_update`, un botón flotante con icono acentuado y tooltip de versión que permite iniciar la actualización incluso con el sidebar comprimido.
  - Señal `update_requested`: Emitida al presionar el botón de actualizar en cualquiera de los modos.

### 4. Controladores y Ventana Principal
- **[update_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/update_controller.py)**:
  - `update_found_silent` ahora emite el diccionario `info` (con la versión y url de descarga).
- **[main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)**:
  - Método `_on_silent_update_found` que extrae la versión y llama a `self.sidebar.set_update_available(True, version=version)`.
  - Conexión de `self.sidebar.update_requested` con `self.handle_update_check()`, abriendo inmediatamente el diálogo interactivo de actualización (`UpdateDialog`).

---

## Verificación y Calidad
- **Sintaxis**: Verificada con `python -m py_compile` (`Exit code 0`).
- **Strict i18n**: Cero textos quemados en código; todas las etiquetas y tooltips utilizan `TranslationService`.
- **Experiencia de Usuario**: Máxima visibilidad de nuevas versiones sin resultar invasivo, con opción de descarte inmediato o actualización en 1 clic.
