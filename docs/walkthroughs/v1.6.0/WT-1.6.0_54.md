# Walkthrough WT-1.6.0_54: Corrección de Fondo Transparente en Popups de Búsqueda (CategorySearch & SearchableCombo)

## Resumen Ejecutivo
Se diagnosticó y corrigió el defecto de renderizado visual reportado en la vista de Horarios (`ScheduleView`), donde al escribir en el buscador de categorías (`CategorySearchComboBox`), el menú emergente de sugerencias (`CategorySuggestionsPopup`) se desplegaba con fondo 100% transparente, traslapándose con los botones y etiquetas del formulario ubicados debajo. Se implementó el despacho de la primitiva `PE_Widget` en el `paintEvent` de los popups derivados de `QFrame`, restaurando el fondo oscuro sólido del tema (`#111215` / `#18191e`, $\text{Alpha} = 255$) sin perder el redondeo de esquinas anti-aliased.

---

## 1. Novedades

- **Fondo Sólido y Elevación Visual en Menús Emergentes**:
  - Los menús desplegables de búsqueda de categorías y selectores enriquecidos ahora presentan una superficie completamente opaca y protegida, evitando que los controles de la ventana subyacente se transparenten durante la interacción del usuario.

---

## 2. Mejoras

- **Integración con el Motor de Estilos QSS en Popups con `WA_TranslucentBackground`**:
  - [`frontend/widgets/category_search.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/category_search.py): En `CategorySuggestionsPopup`, se implementó `paintEvent` inicializando `QStyleOptionFrame` y dibujando `QStyle.PrimitiveElement.PE_Widget`. Esto asegura que el `background-color: #111215` y `border: 1px solid #202227` de `QFrame[role="category_dropdown"]` sean pintados con opacidad completa.
  - [`frontend/widgets/searchable_combo_box.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/searchable_combo_box.py): Se implementó el mismo `paintEvent` en `SearchableComboPopup`, garantizando que todos los selectores buscables de la aplicación compartan el mismo comportamiento visual consistente.
- **Registro en Historial Maestro de Errores**:
  - Documentado como incidente **`INC-013`** en [`docs/historial_crashes_y_errores.md`](file:///c:/Users/TheAn/Desktop/python/Kick/docs/historial_crashes_y_errores.md).

---

## 3. Correcciones

- **Eliminación de la Transparencia Involuntaria en Popups Frameless (INC-013)**:
  - Se corrigió el comportamiento por defecto de Qt donde un `QFrame` de nivel superior omite el relleno de fondo del stylesheet cuando `WA_TranslucentBackground = True` está activo.
  - Se verificó que el interior del popup ahora posee $\text{Alpha} = 255$ (100% opaco), mientras que los 4 píxeles extremos de las esquinas exteriores mantienen $\text{Alpha} = 0$ (transparente), eliminando simultáneamente los marcos rectangulares blancos y el problema de transparencia.

---

## Verificación y Calidad

1. **Test Automatizado de Pixel Rendering**:
   - `CategoryPopup`: Centro $(20, 20) \to \text{Alpha} = 255$ (`0xff111215`), Esquina $(0, 0) \to \text{Alpha} = 0$.
   - `SearchableComboPopup`: Centro $(20, 20) \to \text{Alpha} = 255$ (`0xff18191e`), Esquina $(0, 0) \to \text{Alpha} = 0$.
2. **Suite de Pruebas Unitarias (`pytest resources/tests`)**:
   - **82 passed in 3.28s** (100% PASS).
3. **Suite Maestra de Control de Calidad (`system_health_audit.py --all`)**:
   - **11/11 herramientas aprobadas (100% PASS)** en 17.61 segundos.
