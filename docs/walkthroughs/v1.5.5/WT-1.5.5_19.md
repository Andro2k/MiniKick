# Walkthrough 1.5.5_19: Corrección de Estados y Mensajes en Diálogo de Actualización

## Descripción General
Se corrigió el comportamiento del diálogo de actualización ([update_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/update_dialog.py)), evitando que apareciera el botón de "Reiniciar ahora" durante la comprobación inicial ("Conectando al servidor...") y ajustando adecuadamente los mensajes de subtítulo entre el estado de versión disponible y el de descarga completada.

---

## Cambios Realizados

### 1. Diálogo de Actualización ([update_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/update_dialog.py))
- **Ocultamiento del Botón Primario en Inicialización**:
  - `self.btn_primary.hide()` se aplica en el constructor (`__init__`) para que durante el estado de comprobación/conexión únicamente se muestre el botón "Cerrar".
- **Corrección de Subtítulo en Versión Disponible (`show_update_available`)**:
  - Se sustituyó el texto prematuro de reinicio por `dialogs.update.subtitle_available` ("Una nueva versión está lista para descargar e instalar.").
  - El botón primario pasa a mostrar "Descargar ahora" (`dialogs.update.btn_download`).
- **Subtítulo de Reinicio en Descarga Completada (`show_complete`)**:
  - Se asignó `dialogs.update.subtitle_restart_req` ("Se requiere reiniciar para completar la instalación.") junto con el botón "Reiniciar ahora" (`dialogs.update.btn_restart`).

### 2. Internacionalización (i18n)
- **Archivos**: [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json), [default_en_locale.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/default_en_locale.py)
- Se añadió la clave:
  - `dialogs.update.subtitle_available`: `"Una nueva versión está lista para descargar e instalar."` / `"A new version is ready to download and install."`

---

## Verificación
- **Sintaxis**: Verificada con `python -m py_compile` (`Exit code 0`).
- **Comportamiento Visual**:
  1. *Comprobando*: Muestra "Actualización del Sistema", "Conectando al servidor..." y únicamente el botón "Cerrar".
  2. *Actualización encontrada*: Muestra "Versión {version} disponible", "Una nueva versión está lista para descargar e instalar." y los botones "Cerrar" + "Descargar ahora".
  3. *Descarga completada*: Muestra "Actualización completada", "Se requiere reiniciar para completar la instalación." y los botones "Cerrar" + "Reiniciar ahora".
  4. *Sin actualización*: Muestra "Sistema Actualizado", "Tu sistema ya cuenta con la versión más reciente." y el botón "Cerrar".
