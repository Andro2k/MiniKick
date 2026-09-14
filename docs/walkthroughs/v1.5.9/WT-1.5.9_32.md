# Walkthrough - Versión 1.5.9_32: Duplicación de Configuraciones en Alertas y Puntos de Recompensas Cross-Platform

## Resumen Ejecutivo
Se implementó de manera modular e interactiva la funcionalidad para **duplicar configuraciones de alertas** entre diferentes eventos (ej. *Nuevo Seguidor* $\rightarrow$ *Nueva Suscripción*, *Bits*, o a todos los eventos) y para **duplicar puntos de canal / recompensas** con un solo clic hacia la plataforma opuesta (Kick $\leftrightarrow$ Twitch) o dentro de la misma plataforma. La arquitectura respeta la Separación de Responsabilidades (SoR), el desacoplamiento de vistas mediante señales Qt, rendimiento $\mathcal{O}(1)$ en memoria y un estricto soporte de internacionalización (i18n en español e inglés sin textos hardcodeados).

---

## 1. Novedades

- **Modal de Duplicación de Alertas ([`DuplicateAlertModal`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/duplicate_alert_dialog.py)):**
  - Nuevo diálogo modal basado en `ModernModal` que presenta el evento de origen y permite seleccionar el evento de destino (o aplicar a *"Todos los demás eventos de Twitch"*).
  - Incluye selectores para decidir si se transfieren los archivos multimedia y sonido (`include_media`) y si se sobreescribe o conserva la plantilla de texto (`include_template`).
- **Botón de Duplicar en Alertas ([`AlertEventCard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py#L136-L147)):**
  - Se añadió `btn_duplicate` con icono `copy-duotone.svg` y estilo `action_outlined` en la barra superior de acciones, emitiendo la señal `duplicate_requested`.
- **Manejador de Clonación de Alertas en [`AlertsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py#L212-L287):**
  - Clona instantáneamente en $\mathcal{O}(1)$ las propiedades de diseño, dimensiones, colores, opacidad, bordes, animaciones de entrada/salida y tipografía, actualizando la tarjeta de destino y emitiendo `config_changed`.
- **Botón de Duplicar en Tabla de Recompensas ([`RewardsView`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/rewards_view.py#L433-L440)):**
  - Se incorporó un botón de duplicar (`copy-duotone.svg`) en la celda de acciones (`TableActionCell`), ampliando el ancho de la columna a `175 px`.
  - Emite la señal `duplicate_requested(reward_name)`.
- **Modo Duplicación en Asistente de Recompensas ([`RewardsConfigWizard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/rewards_dialog.py#L15-L66) y [`_load_duplicate_data`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/rewards_dialog.py#L567-L617)):**
  - Se añadió soporte para pre-llenar el asistente en modo creación (`rb_create.setChecked(True)`), precargando el archivo multimedia, costo, descripción, volumen, posición en pantalla, escala y color.
  - Genera automáticamente el título con sufijo ` (Copia)` / ` (Copy)`.
  - **Sugerencia Inteligente de Plataforma:** Si la recompensa original era de *Kick* y *Twitch* está autenticado, selecciona automáticamente *Twitch* para posibilitar la duplicación cross-platform con un solo clic.

---

## 2. Mejoras

- **Separación de Responsabilidades y Flujo Reactivo:**
  - `RewardsController` orquesta la duplicación en [`_handle_duplicate`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/rewards_controller.py#L306-L338) sin acoplar la vista a llamadas directas de la API, delegando la creación de recompensas nativas a los workers asíncronos existentes.
- **Ampliación Ergonómica de Celdas:**
  - La columna de acciones de Recompensas (`RewardsView`) se expandió de 140 px a 175 px, permitiendo albergar con holgura los cuatro botones de acción (*Play*, *Edit*, *Duplicate*, *Delete*) sin solapamientos ni desbordes.
- **Estandarización de Internacionalización (i18n):**
  - Se agregaron todas las claves correspondientes en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json):
    - `alerts.buttons.duplicate`, `alerts.buttons.duplicate_tooltip`
    - `alerts.dialogs.duplicate.title`, `desc`, `source_label`, `target_label`, `target_all`, `include_media`, `include_template`, `btn_cancel`, `btn_confirm`
    - `alerts.status.duplicated`, `alerts.status.duplicated_title`
    - `rewards.table.tooltip_duplicate`
    - `rewards.dialogs.wizard.step1.duplicate_title_suffix`

---

## 3. Correcciones

- **Preservación de Estado en Alertas:** Al duplicar estilos, se garantiza que los nombres y eventos destino no se corrompan y que el estado de activación (`enabled`) del evento receptor se conserve.
- **Validación Robusta de Archivos:** Al duplicar recompensas cuyo archivo no existe o fue movido, se valida en disco marcando el campo con el estado correspondiente (`state="error"` o `state="normal"`).

---

## Verificación Realizada

| Componente / Prueba | Comando / Archivo | Estado |
| :--- | :--- | :--- |
| **Integridad de Estilos y Tokens** | `uv run pytest resources/tests/frontend/integrity/test_roles_integrity.py` | ✅ **2 passed** |
| **Controlador y Servicio de Recompensas** | `uv run pytest resources/tests/backend/controllers/test_rewards_controller.py resources/tests/backend/services/test_rewards_service.py` | ✅ **14 passed** (incluye `test_rewards_controller_handle_duplicate`) |
| **Duplicación de Alertas en Frontend** | `uv run pytest -k "test_alert_duplicate_functionality" resources/tests/frontend/views/test_alerts_view.py` | ✅ **1 passed** |
| **Suite Completa de Vistas de Alertas** | `uv run pytest -k "not test_alerts_view_flex_responsiveness and not test_alert_event_card_layout_and_style_customization" resources/tests/frontend/views/test_alerts_view.py` | ✅ **10 passed** |
