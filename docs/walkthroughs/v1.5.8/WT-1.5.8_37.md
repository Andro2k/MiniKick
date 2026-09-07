# Walkthrough v1.5.8_37: Menú Desplegable con Búsqueda Integrada para Selección de Voces (TTS)

## Resumen del Cambio
Se implementó y pulió el nuevo componente `SearchableComboBox` (`SearchableComboPopup`) para alcanzar una apariencia moderna, limpia y fiel al diseño de referencia:
1. **Eliminación de Doble Flecha en ComboBox**: Se resolvió la anomalía donde aparecía una segunda flecha en el centro del combobox. En Qt QSS, el uso de selectores con comas en subcontroles (`A::down-arrow, B::down-arrow`) provoca que Qt posicione el subcontrol secundario por defecto en el centro (`x ~ 50%`). Al simplificar a una regla única `QComboBox[state="active"]::down-arrow`, ahora se dibuja exclusivamente una única flecha en el extremo derecho que invierte su orientación (`^`) correctamente.
2. **Eliminación del Borde / Margen Transparente del Popup**: Se retiró el contenedor anidado con márgenes translúcidos externos de 8px que causaba recortes y un "borde transparente" visible sobre los controles de fondo. El popup ahora es directamente un contenedor limpio y sin bordes residuales con sus esquinas redondeadas (`8px`) y fondo sólido `#121115`.
3. **Estandarización de Altura y Diseño del Buscador (`QLineEdit`)**: El contenedor de búsqueda interior se ajustó a una altura exacta de 30px con `BORDER_DEFAULT` (`1.2px solid #27262D`, `border-top: 1.2px solid #38363E`), radio de 8px e icono centrado verticalmente, igualando exactamente el alto y estilo de los demás campos de entrada de la aplicación.
4. **Items de Lista Pulidos y Scrollbar Inteligente**: Items con hover suave redondeado (`border: none; outline: none; border-radius: 6px;`), scrollbar oculto cuando hay pocos elementos (<= 6) y barra delgada de 5px si la lista sobrepasa la altura máxima.

---

## Archivos Modificados y Creados

### 1. [searchable_combo_box.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/searchable_combo_box.py)
- **`SearchableComboPopup`**:
  - `WA_TranslucentBackground` desactivado para evitar márgenes fantasma en Windows.
  - Layout directo sin márgenes externos artificiales.
  - `search_container` fijado a 30px de alto con padding horizontal ergonómico (`(8, 0, 8, 0)`).
  - Altura uniforme de filas de 32px (`setUniformItemSizes(True)`).
  - Mensaje de búsqueda vacía (`common.no_results`).
- **`SearchableComboBox`**:
  - Subclase de `NoWheelComboBox` con repintado instantáneo `update()` en transiciones `active` $\leftrightarrow$ `normal`.

### 2. [theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)
- `QComboBox[state="active"]::down-arrow`: Regla de subcontrol única sin comas, eliminando la flecha central duplicada.
- `QFrame[role="searchable_combo_search_bar"]`: Borde estándar `BORDER_DEFAULT`, resaltado superior `1.2px solid #38363E` y radio `RADIUS_MD` (8px).
- `QLineEdit[role="searchable_combo_input"]`: Padding compacto `0px 4px` y fondo transparente.
- Items de lista limpios sin contornos toscos.

### 3. [tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py)
- Configurados los 5 combos de voces con `SearchableComboBox`, placeholder traducido y mensaje de lista vacía.

### 4. [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) & [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)
- Claves agregadas: `"common.search_placeholder"`, `"common.no_results"`, `"chat.settings.search_voice_placeholder"`.

---

## Verificación

| Prueba | Comando | Resultado |
| :--- | :--- | :--- |
| Pruebas de `SearchableComboBox` | `uv run pytest resources/tests/unit/ui/test_searchable_combo_box.py` | **4 PASSED** (0.09s) |
| Integridad de i18n (en/es) | `uv run pytest resources/tests/unit/ui/test_i18n_integrity.py` | **3 PASSED** (0.96s) |
| Ventanas top-level no deseadas | `uv run python resources/tests/unit/ui/test_toplevels.py` | **SUCCESS** (0 ventanas) |
