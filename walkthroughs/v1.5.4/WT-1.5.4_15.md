# Walkthrough: Reorganización de Configuración General en 3 Secciones & Unificación de Kick

## 1. Resumen de Cambios

Se reestructuró por completo la vista de Configuración General ([frontend/views/settings_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py)) para agrupar los ajustes en **3 secciones visuales cohesivas** (`ModernCard`), unificando además la cuenta de **Kick** dentro de la sección de plataformas integradas y reemplazando la tarjeta roja aislada y genérica de desvinculación.

---

## 2. Estructura de las 3 Secciones

### **Sección 1: Ajustes de la Aplicación** (`app_card`)
- **Idioma de la Aplicación** (`world.svg`): Selector de idioma con soporte para reinicio.
- **Tamaño de Fuente Global** (`file-text.svg`): Selector dinámico de escala visual.
- **Ejecución en Segundo Plano** (`minimize.svg`): Switch para minimizar a la bandeja del sistema.
- **Salida de Música (YouTube)** (`music.svg`): Selector de dispositivo de audio para música.
- **Salida de Voz (TTS)** (`volume.svg`): Selector de dispositivo de audio para síntesis de voz.
- **Respaldo de Configuración** (`restore.svg`): Botones de exportación e importación segura.

### **Sección 2: Conexiones de Plataformas** (`integrations_card`)
- **Canal de Kick** (`kick.svg`):
  - Estado dinámico: *"Conectado exitosamente a la cuenta de @{channel}"* o *"No hay una cuenta de Kick conectada actualmente"*.
  - Botón interactivo: `Desconectar @{channel}` (en estilo `action_danger_border` si está conectado) o `Conectar Kick` (`action_accent` si está desconectado).
- **Canal de Twitch** (`twitch.svg`):
  - Estado dinámico y botón de conexión/desconexión con confirmación.
- **Canal de YouTube Live** (`brand-youtube.svg`):
  - Estado dinámico y diálogo modal para captura de chat en vivo.

### **Sección 3: Actualizaciones y Soporte** (`support_card`)
- **Actualizaciones de Software** (`cloud-download.svg`): Botón para comprobar nuevas versiones.
- **Novedades de la Versión** (`file-text.svg`): Visor modal de Release Notes.
- **Soporte y Reporte de Bugs** (`bug.svg`): Formulario integrado para reporte de incidencias y sugerencias.

---

## 3. Archivos Modificados

| Archivo | Cambios Principales |
|---|---|
| [frontend/views/settings_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py) | Reorganización en 3 `ModernCard`s, integración de `row_kick_integration` y actualización dinámica de Kick en `set_integrations_status`. |
| [backend/core/main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py) | Soporte en `_handle_unlink_account` para conectar Kick si está desconectado o solicitar confirmación si está conectado. |
| [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) | Inclusión de claves i18n (`kick_title`, `kick_desc_connected`, `kick_desc_disconnected`, `btn_connect_kick`, `btn_disconnect_kick`). |
| [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) | Paridad en inglés para todas las claves de integración de Kick. |

---

## 4. Validación y Pruebas

- **Suite de Pruebas Unitarias (`pytest`)**: 96/96 pruebas pasadas con éxito (`96 passed in 12.53s`).
- **Verificación de i18n**: Paridad total entre `es.json` y `en.json` confirmada por `test_i18n_key_parity`.
