# Walkthrough WT-1.5.8_28: Creación de `ClearableLineEdit` e Integración en Diálogos de Plataformas

## 1. Resumen Ejecutivo
Se implementó el nuevo componente reutilizable [`ClearableLineEdit`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/clearable_line_edit.py), inspirado en [`UnifiedSearchBar`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/search_bar.py). Este widget integra un botón de limpieza con el icono `x.svg` dentro de la propia caja de texto (estilizada homogéneamente mediante `role="search_bar"`).
A continuación, se refactorizaron los diálogos de integración de plataformas ([`PlatformConnectDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/platform_connect_dialog.py), [`TikTokConnectDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/tiktok_connect_dialog.py) y [`YouTubeConnectDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/youtube_connect_dialog.py)), eliminando el botón secundario externo ("Limpiar" / "Desconectar") para ofrecer una interfaz más limpia, moderna y directa.

---

## 2. Componentes y Modificaciones

### A. Widget Reutilizable: `ClearableLineEdit`
- **Archivo**: [`frontend/widgets/clearable_line_edit.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/clearable_line_edit.py)
- **Estructura**:
  - Hereda de `QFrame` con `role="search_bar"`, heredando automáticamente la estética oscura, bordes, estados `:hover` y `:focus-within`, y el separador vertical del botón definidos en `theme.py`.
  - Contiene un `QLineEdit` sin marco (`setFrame(False)`) y un `QPushButton` (`btn_clear`) con icono `x.svg`.
  - **Comportamiento Reactivo**:
    - El botón 'X' se oculta automáticamente cuando el campo no tiene texto (`btn_clear.setVisible(bool(text.strip()))`).
    - Al pulsar 'X', limpia el campo, recupera el foco inmediatamente y emite `textCleared` y `textChanged("")`.
  - **API de compatibilidad**:
    - Expone métodos de `QLineEdit` (`text()`, `setText()`, `clear()`, `setPlaceholderText()`, `placeholderText()`, `setFocus()`, `setEnabled()`, `setReadOnly()`, `isReadOnly()`).
    - Expone señales estándar: `textChanged = Signal(str)`, `returnPressed = Signal()`, `textCleared = Signal()`.

### B. Diálogos de Conexión de Plataformas
- **[`PlatformConnectDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/platform_connect_dialog.py)**:
  - Se eliminó el botón secundario `self.btn_clear` (`ModernButton`) y el layout dividido horizontal `input_container`.
  - `self.txt_target` ahora es una instancia de `ClearableLineEdit` a ancho completo.
  - Conexión a `returnPressed`: permite confirmar y conectar directamente al pulsar Enter.
  - Al hacer clic en 'X', marca `_is_cleared = True` y valida el estado del botón principal de conexión.
  - Se mantienen los métodos de consulta `is_cleared() -> bool` y `get_target() -> str` consumidos por `main_window_core.py`.
- **[`TikTokConnectDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/tiktok_connect_dialog.py)** y **[`YouTubeConnectDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/youtube_connect_dialog.py)**:
  - Se removió el paso del parámetro obsoleto `btn_clear_key`.

---

## 3. Verificación y Pruebas

### A. Pruebas Unitarias
Se añadió la prueba `test_clearable_line_edit` en [`test_frontend_common.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_frontend_common.py):
- Verifica el estado inicial con botón 'X' oculto.
- Verifica la aparición dinámica del botón al asignar texto con `setText()`.
- Verifica la limpieza, recuperación de foco y emisión de la señal `textCleared`.

### B. Suite Completa
```powershell
uv run pytest
```
**Resultado:**
- **286 passed in 52.59s** (100% de aprobación, 0 fallos, 0 regresiones).
