# Walkthrough - WT-1.5.8_03: Fase 2: Frontend e Interfaz de Configuración de Alertas Multiplataforma

**Versión:** `v1.5.8`  
**Documento:** `WT-1.5.8_03.md`  
**Fecha:** 02 de Septiembre, 2026  

---

## Resumen Ejecutivo

Se completó con éxito la **Fase 2 (Frontend y Navegación)** del sistema de alertas en vivo de MiniKick para Kick y Twitch. La interfaz permite a los usuarios configurar y personalizar cada tipo de alerta (Follow, Suscripción, Resub, Regalo de Subs, Raid y Bits/Cheers), asociar sonidos e imágenes/videos, ajustar volumen y duración, activar la lectura por voz (TTS), copiar el enlace de OBS Browser Source con un solo clic y probar las alertas en tiempo real contra el overlay local.

---

## Componentes y Cambios Implementados

### 1. Vista de Alertas (`frontend/views/alerts_view.py`)
- **`AlertEventCard`**:
  - Componente modular heredero de `ModernCard`.
  - **Adherencia Estricta al Sistema de Diseño (`theme.py`)**: Sin `setStyleSheet` inline, utilizando roles semánticos del tema.
  - **Colores de Plataforma en Botones de Acción**:
    - Para eventos de Kick: botón *"Probar Alerta"* estilizado con `role="action_kick"` (verde brillante Kick).
    - Para eventos de Twitch: botón *"Probar Alerta"* estilizado con `role="action_twitch"` (púrpura Twitch).
  - **Cabecera**: Icono distintivo con acento de plataforma (verde Kick `#53FC18`, púrpura Twitch `#9146FF`), título y descripción de la alerta, y `ModernSwitch` para activación/desactivación.
- **`AlertsView`**:
  - **Layout de 2 Columnas Responsivas (estilo `spam_view.py`)**:
    - Disposición en 2 columnas balanceadas mediante `QBoxLayout(LeftToRight)` que distribuye de forma simétrica los eventos tanto en Kick como en Twitch.
    - Soporte responsive nativo con `resizeEvent`: conmuta fluidamente a 1 sola columna vertical (`TopToBottom`) en ventanas de ancho menor a 920px.
  - **Pestañas de Selector de Plataforma Temáticas (estilo `dashboard_view.py`)**:
    - Botones `ModernButton` interactivos con iconos de marca (`brand-kick.svg` y `brand-twitch.svg`).
    - Al seleccionar Kick: el botón Kick adopta `role="action_kick"` y Twitch `role="action_outlined"`.
    - Al seleccionar Twitch: el botón Twitch adopta `role="action_twitch"` y Kick `role="action_outlined"`.
  - **Distribución Flexible Interna por Tarjeta (Anti-Cramping)**:
    - **Filas de Archivos de Sonido y Multimedia**: Se desacoplaron en filas independientes de ancho completo. Cada `QLineEdit` cuenta con espacio amplio para mostrar rutas completas sin truncamiento, junto a botones *"Examinar..."* de ancho uniforme (110px).
    - **Fila de Parámetros**: Control de Duración (`NoWheelSpinBox` de 100px) y Slider de Volumen dinámico (`NoWheelSlider` expandible) situados en una fila dedicada con proporción balanceada.
    - **Fila de Acciones Inferior**: Switch horizontal de lectura por voz TTS a la izquierda y botón *"Probar Alerta"* temático anclado a la derecha, evitando solapamientos o desbordes fuera de la tarjeta.
  - **Controles Inferiores**:
    - Duración: `NoWheelSpinBox` (1 a 60 segundos con sufijo "s").
    - Volumen: `NoWheelSlider` (0% a 100% con etiqueta porcentual dinámica).
    - Lectura por voz: `ModernSwitch` para TTS.
    - Botón de Prueba: `ModernButton` (*"Probar Alerta"*) con icono `player-play.svg`.
- **`AlertsView`**:
  - Hereda de `BaseView` con scroll nativo y cabecera (`alerts.header.title`).
  - **Tarjeta Superior de Overlay**: Contiene la URL del navegador OBS (`http://localhost:8090/alerts?token=...`) y botón rápido de copiado al portapapeles.
  - **Selector de Plataforma**: Botones de filtro `filter_chip` para alternar fluidamente entre las alertas de **Kick** y **Twitch** mediante un `QStackedWidget`.

### 2. Controlador de Alertas (`backend/controllers/alerts_controller.py`)
- **`AlertsController`**:
  - Conexión reactiva de señales (`config_changed`, `test_alert_requested`, `copy_url_requested`, `view_shown`).
  - `load_initial_data`: Carga diferida en $\mathcal{O}(1)$ desde `SQLiteAlertStorage` y poblado automático de los campos de la interfaz.
  - `_handle_config_changed`: Persistencia atómica de `AlertConfig` y emisión de Toast de confirmación con tag semántico `tag="alert_<platform>_<type>"`.
  - `_handle_test_alert`: Disparo de prueba inmediato a OBS vía `AlertService.trigger_test_alert` y notificación Toast.
  - `_handle_copy_url`: Copiado seguro al portapapeles del sistema (`QGuiApplication.clipboard().setText`) con feedback visual.

### 3. Navegación Principal y Shell (`backend/core/main_window_core.py`)
- Agregada la pestaña **"Alertas"** en `_NAV_CONFIG` con el icono `alert-circle.svg` en la sección superior (`top`).
- Instanciación de `AlertsController` en `_setup_ui`.
- Carga perezosa (*lazy instantiation*) en `_get_or_create_view` para optimizar el tiempo de arranque de la aplicación.
- Proveedor de URL `get_alerts_overlay_url()` en `OverlayServerManager`.

### 4. Internacionalización Estricta (i18n)
- **`locales/es.json` y `locales/en.json`**:
  - Incorporada la clave `main.sidebar.tabs.alerts` ("Alertas" / "Alerts").
  - Incorporada la sección completa `"alerts"` con traducciones idénticas en español e inglés: títulos, descripciones de eventos, placeholders, tooltips y mensajes de toast.
  - Cumplimiento de la regla **Zero Hardcoded UI Text**.

---

## Verificación y Pruebas Automatizadas

Se añadieron pruebas completas para la interfaz y controlador:
- `resources/tests/unit/ui/test_alerts_ui.py`:
  - `test_alert_event_card_interactions`: Prueba carga de datos, emisión de señal ante cambios de texto/volumen y clic en botón de prueba.
  - `test_alerts_view_instantiation_and_platform_switch`: Prueba alternancia entre páginas Kick y Twitch.
  - `test_alerts_controller_lifecycle`: Prueba carga inicial, persistencia ante cambios, disparo de alerta de prueba y copiado de URL al portapapeles.
- Verificación de paridad i18n (`test_i18n_integrity.py`): **Aprobada**.
- Verificación de roles QSS del tema (`test_roles_integrity.py`): **Aprobada**.

**Resultado de la Suite Completa del Proyecto**:
```text
============================ 190 passed in 12.25s =============================
```
190 pruebas pasando al 100% sin advertencias ni regresiones.
