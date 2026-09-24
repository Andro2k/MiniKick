# Walkthrough WT-1.6.0_33 — Corrección de Incompatibilidades Visuales con Tema Claro de Windows

## Resumen de Cambios

Se corrigieron anomalías visuales reportadas en entornos donde el sistema operativo Windows tiene activo el **Tema Claro**. Se implementó una paleta oscura nativa global forzada (`create_dark_palette`), se habilitó la transparencia (`WA_TranslucentBackground`) en los popups sin marco para eliminar marcos blancos rectangulares, y se estilaron el widget de autocompletado de variables y el popup de calendario de `QDateEdit`.

---

## 1. Novedades

- **Paleta Oscura Nativa Global (`create_dark_palette`)**:
  - En [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) se introdujo la función `create_dark_palette() -> QPalette` que define los roles nativos de Qt (`Window`, `Base`, `Text`, `Button`, `Highlight`, `ToolTipBase`, etc.) anclados al sistema de diseño oscuro de MiniKick.
  - En [`main.py`](file:///c:/Users/TheAn/Desktop/python/Kick/main.py) se inyecta `app.setPalette(create_dark_palette())` en la inicialización de `QApplication` y en el diálogo de crash global.
  - Esto garantiza que cualquier componente nativo de Qt (menús, tooltips, vistas de tablas, calendarios y popups) adopte una base oscura consistente sin importar si el usuario tiene Windows configurado en modo claro.

---

## 2. Mejoras

- **Estilos Globales de Menús y Tooltips**:
  - Se agregaron reglas CSS en `GLOBAL_QSS` para `QMenu` y `QToolTip` garantizando fondos oscuros (`#141519` / `#18191E`), bordes sutiles y texto blanco de alto contraste en menús contextuales y descripciones emergentes.
- **Soporte para Popups Flotantes Transparentes**:
  - En [`frontend/widgets/category_search.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/category_search.py), `CategorySuggestionsPopup` ahora activa `WA_TranslucentBackground = True` para evitar artefactos en esquinas redondeadas.
- **Cobertura de Pruebas**:
  - Se incorporó la prueba unitaria `test_dark_palette_and_popup_translucency_standards` en [`resources/tests/test_antigravity_ui_theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_antigravity_ui_theme.py).

---

## 3. Correcciones

- **Marco Blanco en Selector de Voces (`SearchableComboBox`)**:
  - En [`frontend/widgets/searchable_combo_box.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/searchable_combo_box.py), se corrigió `SearchableComboPopup` cambiando `WA_TranslucentBackground` de `False` a `True`. Se elimina el recuadro blanco rectangular que Windows dibujaba alrededor del menú redondeado en modo claro.
- **Recuadro Blanco en Autocompletado de Variables (`VariableTextEdit`)**:
  - En [`frontend/widgets/controls_widget.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls_widget.py), se asignó el rol `variable_autocomplete_popup` y `WA_TranslucentBackground = True` a `self.popup`.
  - En [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py), se agregaron reglas QSS específicas para `QListWidget[role="variable_autocomplete_popup"]` con fondo `#18191E`, bordes `#38363E`, items con hover/selected y tamaño de popup optimizado.
- **Fondo Blanco y Texto Invisible en Calendario (`QDateEdit` / `NoWheelDateEdit`)**:
  - En [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py), se estiló el contenedor nativo `QWidget#qt_datetimedit_calendar` y la grilla `QCalendarWidget QTableView QWidget` con fondo `#141519`.
  - En [`frontend/widgets/no_wheel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/no_wheel.py), `_configure_calendar_widget` aplica la paleta oscura directamente a `cal`, a su ventana `popup` (`cal.parent()`) y a `table.viewport()`, evitando que el viewport pinte `QPalette.Base` blanco.
- **Registro en Historial de Errores**:
  - Se catalogó el incidente bajo el código `INC-011` en [`docs/historial_crashes_y_errores.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/historial_crashes_y_errores.md).

---

## Verificación Realizada

1. **Pytest Suite**: 51/51 pruebas pasadas exitosamente (100% de éxito).
2. **AST Dead Code & Orphan Manager**: 0 archivos huérfanos, 0 imports innecesarios, 0 símbolos muertos.
3. **AST Unused Parameter Manager**: 0 parámetros huérfanos detectados.
