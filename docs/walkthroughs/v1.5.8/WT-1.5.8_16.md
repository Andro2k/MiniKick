# Walkthrough: WT-1.5.8_16 - ScrollArea con Difuminado Vertical Dinámico y Sistema de Avisos Reactivos por Desvinculación de Plataformas

## Resumen Ejecutivo

En este walkthrough se implementaron dos mejoras clave de arquitectura y diseño solicitadas por el usuario:
1. **ScrollArea con Gradiente de Difuminado Dinámico (`FadingScrollArea`) y Scrollbars Modernos**:
   - Se rediseñó visualmente la barra de desplazamiento vertical en [theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) con un estilo flotante estilizado de 8px, bordes redondeados tipo cápsula y transparencias armoniosas (`rgba(255, 255, 255, 0.16)`).
   - Se diseñó e integró [FadingScrollArea](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py), que intercepta el evento de pintado del viewport (`QEvent.Type.Paint`) para proyectar un degradado difuso sutil (28px de altura) en el borde superior cuando el usuario se desplaza hacia abajo, y en el borde inferior cuando existe contenido desplazable adicional.
   - Se integró globalmente en [BaseView](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/base_view.py) y [ModernScrollArea](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py), dotando de este efecto visual a todas las vistas de la aplicación de manera uniforme.
2. **Sistema de Avisos Reactivos y Gating No Destructivo para Alertas al Desvincular Cuentas**:
   - Cuando el usuario desvincula Kick o Twitch, las configuraciones de alertas permanecen guardadas de forma segura en la base de datos (sin alteraciones destructivas).
   - Se introdujo un banner de aviso prominente ([ModernCard](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)) en [AlertsView](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py) con icono de advertencia, explicación contextual clara y botón de acción directa ("Conectar Kick" / "Conectar Twitch").
   - Las tarjetas de alerta ([AlertEventCard](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py)) muestran un badge de advertencia `(Desconectado)` indicando que la alerta permanecerá inactiva hasta reconectar.
   - En [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py) se conectó la sincronización de estado de plataformas (`set_connected_platforms`) y el slot de reconexión directa (`_handle_alert_platform_connect`), permitiendo re-autenticar la cuenta sin abandonar la vista de alertas.
3. **Internacionalización Completa (i18n)**:
   - Cumplimiento estricto de la Regla #7 de MiniKick: cero textos quemados y paridad 100% entre `locales/es.json` y `locales/en.json`.

---

## 1. Arquitectura y Principios de Diseño

### A. Difuminado en Scroll sin Overhead ($O(1)$)
En lugar de crear árboles complejos de widgets transparentes flotantes superpuestos (que interfieren con eventos del ratón, redimensionamientos o focus), `FadingScrollArea` aprovecha `viewportEvent`:
- Solo durante `QEvent.Type.Paint`, si `v_bar.value() > 0` o `v_bar.value() < v_bar.maximum()`, se dibuja un `QLinearGradient` con `QPainter` directamente en el viewport.
- **Complejidad Big-O**:
  - Tiempo de renderizado: $\mathcal{O}(1)$ (dos pasadas de gradiente 2D primitivas aceleradas por GPU/software).
  - Espacio de memoria: $\mathcal{O}(1)$ (reutilización del buffer de color sin instanciar sub-widgets).

### B. Separación de Responsabilidades y Gating No Destructivo
- **Conservación de Configuración**: Las alertas nunca se desactivan en la base de datos al cerrar sesión o expirar el token de la plataforma. La intención del usuario (mensajes, duraciones, TTS) queda preservada.
- **Transparencia Visual**: El usuario comprende de inmediato por qué no suenan las alertas mediante el banner superior y los badges en las tarjetas individuales.
- **Acción Inmediata**: Al hacer clic en "Conectar [Plataforma]", se despacha la señal `connect_platform_requested` hacia el orquestador principal (`main_window_core.py`), iniciando el flujo de autenticación OAuth sin navegación manual a la pantalla de Ajustes.

---

## 2. Modificaciones Detalladas

### A. Barra de Desplazamiento y Fading ([theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) y [blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py))
- **Estilo QSS en `theme.py`**:
  - Anchura vertical fijada en 8px, fondo transparente, márgenes de 2px, borde redondeado en 4px.
  - Handle translúcido con realce interactivo (`hover` y `pressed`).
- **`FadingScrollArea` en `blocks.py`**:
  ```python
  class FadingScrollArea(QScrollArea):
      def __init__(self, widget: QWidget = None, parent=None, fade_height: int = 28, fade_color: str | QColor = COLOR_NEUTRAL_950):
          ...
      def viewportEvent(self, event):
          res = super().viewportEvent(event)
          if event.type() == QEvent.Type.Paint:
              self._paint_fade()
          return res
  ```
- **Adopción en `BaseView`**:
  - `self.scroll_area = FadingScrollArea(parent=self)` en [base_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/base_view.py).
- **Herencia en `ModernScrollArea`**:
  - Ahora hereda de `FadingScrollArea`, asegurando compatibilidad hacia atrás con cualquier scroll previo.

### B. Tarjeta de Alertas ([event_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py))
- Se integró el badge de desconexión en el encabezado de la tarjeta:
  ```python
  self.badge_offline = create_badge(
      self.i18n.get("alerts.status.disconnected"),
      state="warning",
      parent=self
  )
  self.badge_offline.setVisible(False)
  ```
- Se añadió el método `set_platform_connected(self, connected: bool)` para alternar la visibilidad del badge y actualizar el tooltip de advertencia de la tarjeta.

### C. Vista de Alertas ([alerts_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/alerts_view.py))
- Se creó `notice_banner`:
  - Icono de advertencia ámbar (`alert-triangle.svg`).
  - Título ("Cuenta desconectada") y descripción contextual formateada con la plataforma activa.
  - Botón de reconexión `ModernButton(role="action_outlined", icon_name="plug.svg")`.
  - Disposición responsiva que se adapta verticalmente si el ancho es reducido ($< 680\text{px}$).
- Se agregaron las señales y métodos de sincronización:
  - `connect_platform_requested = Signal(str)`
  - `set_connected_platforms(self, connected_platforms: Dict[str, bool])`
  - `_update_platform_connection_ui(self)`

### D. Coordinación en el Núcleo ([main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py))
- En `_get_or_create_view` ("Alerts"):
  - Conexión de `view_alerts.connect_platform_requested` con `self._handle_alert_platform_connect`.
  - Inyección inicial de plataformas conectadas mediante `get_connected_platforms()`.
- En `_update_integrations_status_ui`:
  - Notificación de cambios de conexión hacia `view_alerts.set_connected_platforms(conn_dict)` junto con las demás vistas del sistema.
- En `_handle_alert_platform_connect(platform)`:
  - Redirección a `_handle_auth_process()` para Kick o `_handle_twitch_auth_process(force=False)` para Twitch.

### E. Internacionalización ([locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) & [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json))
- Nuevas claves estructuradas en `alerts.notice.*` y `alerts.status.*`:
  - `alerts.notice.disconnected_title`
  - `alerts.notice.disconnected_msg`
  - `alerts.notice.connect_btn`
  - `alerts.status.connected`
  - `alerts.status.disconnected`
  - `alerts.status.platform_offline`

---

## 3. Verificación y Resultados

### Pruebas Unitarias Ejecutadas
1. **[test_alerts_ui.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_alerts_ui.py)**:
   - `test_alerts_view_disconnection_notice_and_reconnect_flow`: Valida la visualización del banner ante desvinculaciones de Kick o Twitch, la visibilidad del badge en las tarjetas y la emisión correcta de la señal al hacer clic en reconectar.
   - `test_alerts_view_flex_responsiveness`: Valida la adaptabilidad responsiva sin desbordamiento de `minimumSizeHint` en resoluciones angostas ($550\text{px}$ a $1400\text{px}$).
2. **[test_frontend_common.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_frontend_common.py)**:
   - `test_fading_scroll_area`: Valida instanciación, configuración de `fade_size` y herencia de `ModernScrollArea`.
3. **[test_roles_integrity.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_roles_integrity.py)**:
   - Valida que todos los roles de QSS (`action_outlined`, `action_kick`, `action_twitch`, etc.) existan en el sistema de diseño de `theme.py`.
4. **[test_i18n_integrity.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_i18n_integrity.py)**:
   - Valida paridad completa y validez de sintaxis entre `es.json` y `en.json`.
