# Walkthrough WT-1.4.7_02 - Vinculación de Sub-widgets Internos a Parent

## Resumen

En esta fase se resolvió el parpadeo remanente de ventanas nativas secundarias al iniciar la aplicación, vinculando todos los contenedores internos (`QStackedWidget`, `ModernTable`, `QFrame`, y `QLabel`) a su objeto `parent` correspondiente.

## Cambios Aplicados

1. **[frontend/widgets/table.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/table.py)**:
   - Se asignó `parent=self` en `ModernTableCard` (`lbl_title`, `txt_search`, `btn_add`, `stack`, `table`).
   - Se asignó `parent=self` en `TableActionCell` y `setup_empty_state`.

2. **[frontend/core/main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/core/main_window_core.py)**:
   - `self.content_stack = QStackedWidget(self.central_widget)`.

3. **[frontend/views/log_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/log_view.py)**:
   - `self.content_stack = QStackedWidget(self)`.

4. **[frontend/dialogs/base_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py)**:
   - `self.container = QFrame(self)` y `self.main_content = QStackedWidget(self)`.

5. **[frontend/widgets/controls.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls.py)**:
   - `NoWheelSlider` y `QLabel` dentro de `CompactSlider` vinculados a `parent=self`.

6. **[frontend/widgets/blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py)**:
   - `ViewHeader`, `SettingRow`, `SliderRow` y `StatCard` actualizados con `parent=self` en las etiquetas e iconos.

## Verificación

- Verificación sintáctica limpia mediante `py_compile` en todos los archivos del frontend.
