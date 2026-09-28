# Walkthrough 1.6.1_06: Persistencia Inteligente del Estado y Geometría de Ventana Principal

## Novedades

- **Apertura Maximizada por Defecto**:
  La aplicación ahora se inicia en modo maximizado en el primer arranque o instalación nueva, aprovechando la totalidad del espacio visual de la pantalla sin requerir interacción manual del usuario.

- **Persistencia Inteligente de Geometría y Estado (`restore_window_state`)**:
  Se implementó un motor de persistencia que recuerda el estado exacto de la ventana al cerrarla:
  - Si el usuario cerró la app en modo maximizado, se volverá a abrir maximizada.
  - Si el usuario colocó la ventana en una posición y tamaño específicos (modo flotante en monitores secundarios o configuraciones multi-pantalla), la aplicación restaura fielmente esas coordenadas mediante `restoreGeometry`.

---

## Mejoras

- **Preservación de Estado al Minimizar a la Bandeja del Sistema (Tray)**:
  Se optimizó el controlador `_restore_from_tray` y el evento `changeEvent`. Si la ventana se encontraba maximizada antes de minimizarse a la bandeja del sistema, al hacer clic en el icono de la bandeja se restaura de inmediato en modo maximizado (`showMaximized()`) en lugar de forzar el modo de ventana normal.

- **Persistencia Segura en Salida**:
  El método `_save_window_state` se ejecuta atómicamente antes de ocultar la ventana en `closeEvent` y `_force_quit`. Si la ventana está maximizada, no sobrescribe la geometría normal para preservar el tamaño de ventana flotante cuando el usuario decida desmaximizarla.

---

## Correcciones

- **Corrección de Tamaño Inicial en Bootstrap**:
  Se reemplazó la llamada fija `window.show()` en [main.py](file:///c:/Users/TheAn/Desktop/python/Kick/main.py) por `window.restore_window_state()`, eliminando el comportamiento donde la app siempre iniciaba con un tamaño forzado de 1200x800 píxeles ignorando las preferencias del usuario.
