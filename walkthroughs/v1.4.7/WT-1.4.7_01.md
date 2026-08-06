# Walkthrough WT-1.4.7_01 - Corrección de Ventana Fantasma en Arranque

## Resumen

En esta versión se resolvió el parpadeo / destello de una pequeña ventana nativa blanca (`_ [ ] X`) que ocurría en Windows al iniciar la aplicación (`uv run main.py`).

## Origen del Problema
En PySide6, cuando un componente derivado de `QWidget` o `QMenu` es instanciado sin asignarle un objeto `parent`, Qt lo clasifica temporalmente como una ventana de nivel superior (Top-Level Window). En Windows, esto provocaba que el sistema operativo renderizara brevemente un marco de ventana estándar antes de que las banderas de la interfaz de usuario surtieran efecto.

## Cambios Aplicados

1. **[frontend/widgets/controls.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls.py#L141)**:
   - `VariableTextEdit`: Se pasó `self` como padre al instanciar `self.popup = QListWidget(self)`.

2. **[frontend/navigation/tray_menu_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/tray_menu_component.py#L27)**:
   - `SystemTrayManager`: Se asignó `self.parent()` al instanciar `self.menu = QMenu(self.parent())`.

3. **[frontend/navigation/sidebar_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py#L14-L15)**:
   - `Sidebar`: Se ajustó el constructor para recibir `parent=None` y ejecutar `super().__init__(parent)`.

4. **[frontend/core/main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/core/main_window_core.py#L104)**:
   - `MainWindowCore`: Se pasó `parent=self` al instanciar `self.sidebar`.

5. **[frontend/widgets/blocks.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks.py#L169-L170)**:
   - `ExpandableSettingCard`: Se actualizó el constructor para recibir y propagar `parent`.

## Verificación Realizada

- Verificación sintáctica con `py_compile` en todos los archivos modificados.
