# Walkthrough: Modernización Visual, Geometría de Diálogos y Corrección de Fuentes en ComboBoxes

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_01.md`  
**Módulos Involucrados:**
- `frontend/views/dashboard_view.py`
- `frontend/dialogs/base_dialog.py`
- `frontend/dialogs/modern_modal.py`
- `frontend/views/spam_view.py`
- `frontend/views/widgets_view.py`
- `frontend/common/theme.py`
- `main.py`

---

## 1. Resumen de Objetivos y Cambios

### A. Modernización del Dashboard y Switches Táctiles
- Se integraron switches interactivos `ModernSwitch` con retroalimentación háptica/visual inmediata para la activación de bots de Kick y Twitch.
- Formateo moderno para la visualización de permisos requeridos en Kick/Twitch en formato de lista estructurada con insignias de estado.

### B. Corrección de Sincronización de Geometría en Diálogos Modales
- **Problema:** En Windows, la apertura de diálogos (`ModernFramelessShell`, `ModernConfirmDialog`, `ModernWizardPanel`) emitía advertencias `QWindowsWindow::setGeometry` y desalineación al calcular el centro de la pantalla antes de computar el layout de Qt.
- **Solución:**
  - Invocación explícita de `self.adjustSize()` previa a la ecuación de centrado `(parent.width() - self.width()) // 2`.
  - Configuración de políticas de tamaño restrictivas (`QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred`) en el contenedor interno del diálogo.
  - Eliminación total de advertencias de geometría nativa de Windows.

### C. Unificación de Alturas y Proporciones en Tarjetas (`SpamView` y `WidgetsView`)
- Estandarización de `minimumHeight` y layouts de `ModernCard` en los paneles de filtros de spam y configuración de widgets para evitar deformaciones visuales en resoluciones altas o escaladas por DPI.

### D. Eliminación de Advertencias `QFont::setPointSize` en ComboBoxes
- **Problema:** Los menús desplegables (`QComboBox`) generaban la advertencia `QFont::setPointSize: Point size <= 0 (-1), must be greater than 0` al abrirse en Windows.
- **Solución:**
  - Inicialización de la tipografía global con tamaño explícito en puntos (`app_font.setPointSize(10)`) en `main.py`.
  - Declaración explícita de `font-size: {text1}px;` en los selectores QSS `QComboBox`, `QComboBox QAbstractItemView` y `QComboBox QAbstractItemView::item` en `frontend/common/theme.py`.

---

## 2. Verificación
- Diálogos y ComboBoxes probados en ejecuciones con resolución 1080p y 1440p (escala 100% y 125%).
- Registro de log completamente limpio de advertencias `QWindowsWindow::setGeometry` y `QFont::setPointSize`.
