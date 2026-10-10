# Walkthrough WT-1.6.2_04: Corrección de Crash en Linux (INC-018), Lanzador Resiliente de Navegador y Adaptación Dinámica de Toasts

## Resumen de la Versión
* **Versión:** `v1.6.2`
* **Tipo:** Corrección de Crash Crítico, Soporte Multi-Plataforma Linux/Wayland, UI Dinámica
* **Módulos Afectados:**
  * [`frontend/views/dashboard_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py)
  * [`backend/controllers/dashboard_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/dashboard_controller.py)
  * [`backend/services/system/browser_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/browser_service.py)
  * [`backend/services/auth/auth_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/auth_service.py)
  * [`frontend/navigation/toast_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py)
  * [`docs/historial_crashes_y_errores.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/historial_crashes_y_errores.md)
  * [`resources/tests/test_linux_auth_and_toast.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_linux_auth_and_toast.py)

---

## Novedades

* **Lanzador Resiliente Multi-Nivel de Navegador Web (`BrowserService._open_default`)**:
  Se implementó una arquitectura en cascada de 5 niveles para la apertura de hipervínculos y flujos de autenticación OAuth, eliminando los fallos silenciosos en distribuciones Linux modernas con Wayland, XDG Desktop Portals o invocaciones desde hilos de trabajo secundarios:
  1. *Nivel 1 (Qt Native Portal)*: Despacho mediante `QDesktopServices.openUrl(QUrl(url))`, comunicándose de forma nativa con el portal D-Bus de FreeDesktop (`org.freedesktop.portal.OpenURI`) en Linux y con la sesión gráfica activa.
  2. *Nivel 2 (Linux / BSD Native Detached)*: Búsqueda con `shutil.which` de `xdg-open` o `gio open`, despachando el proceso con `start_new_session=True` y redirección a `DEVNULL` para evitar que el navegador muera al cerrarse el hilo o subshell de origen.
  3. *Nivel 3 (Windows Native ShellExecute)*: En Windows, ejecución directa a bajo nivel con `os.startfile(url)`.
  4. *Nivel 4 (macOS Native)*: Despacho desacoplado con `open`.
  5. *Nivel 5 (Fallback Estándar)*: Delegación en el módulo estándar `webbrowser.open(url)`.
* **Auto-Ajuste Geométrico Dinámico en Notificaciones Toast ([`ModernToast`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py))**:
  Se diseñó el método `_adjust_geometry(self)` que calcula en tiempo constante $\mathcal{O}(1)$ la altura exacta requerida para cualquier combinación de título y mensaje mediante `QFontMetrics.boundingRect` con `Qt.TextFlag.TextWordWrap`. El contenedor adapta automáticamente su altura desde 58 px (solo título) hasta 108 px o más según la cantidad de líneas, garantizando que nunca más se recorte el texto en el borde inferior.

---

## Mejoras

* **Posicionamiento Reactivo en [`ToastManager`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/toast_component.py)**:
  Se actualizó el cálculo de coordenadas en `_calculate_positions` para evaluar dinámicamente `target_x = self.main_window.width() - toast.width() - margin_x` en lugar de utilizar un ancho cableado estático de 330 px, permitiendo que los toasts utilicen un ancho óptimo de 340 px con mayor legibilidad.
* **Integración Defensiva en [`OAuthCallbackServer`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/auth_service.py)**:
  En `capture_auth_code`, si el servicio de navegador no fue inyectado o falla, la aplicación recurre de inmediato al lanzador resiliente `BrowserService._open_default(url)` en lugar de invocar `webbrowser.open(url)` sin protección.
* **Suite de Pruebas Unitarias Especializadas**:
  Creación de [`resources/tests/test_linux_auth_and_toast.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_linux_auth_and_toast.py) cubriendo compatibilidad de argumentos por palabra clave, manejo de estados de error en el controlador, escalado dinámico de altura en toasts y ejecución desacoplada del lanzador de navegador en Linux.

---

## Correcciones

* **Eliminación del Crash Fatal por `TypeError` en `DashboardView.update_connection_status` (INC-018)**:
  Se subsanó el fallo crítico reportado en `minikick_crash_anonymous_v1.6.1.log`:
  ```text
  TypeError: DashboardView.update_connection_status() got an unexpected keyword argument 'error_msg'. Did you mean '_error_msg'?
  ```
  Se restauró la firma canónica `def update_connection_status(self, is_connecting: bool, has_error: bool = False, error_msg: str = ""):` en [`frontend/views/dashboard_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/dashboard_view.py), registrando el mensaje de error si está presente.
* **Corrección de Recorte Visual de Texto en Alertas Toast**:
  Se resolvió el defecto donde la alerta *"Autenticación en curso"* mostraba su tercera línea de texto cortada por la mitad en el borde inferior, asegurando que todo el mensaje se lea con holgura y márgenes equilibrados.
