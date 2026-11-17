# Walkthrough Técnico — MiniKick v1.6.8 (Paso 19)

Repintado del diálogo de actualización y tarjeta de actualización del sidebar más minimalista.

---

## Contexto

- Tras el paso 17, el diálogo seguía mostrando el estado anterior (`99%`, "Descargando..." y "Reiniciar ahora" superpuestos) hasta pasar el cursor por encima.
- El `QGraphicsDropShadowEffect` aplicado al contenedor de `ModernFramelessShell` deja a los hijos sin repintar tras cambios posteriores a mostrar el diálogo (Windows, ventana sin marco y translúcida).
- Se pidió quitar el icono verde de nube de la tarjeta de actualización del sidebar.

## Cambios por capa

### Frontend

- **`frontend/dialogs/base_dialog.py`:** `set_dialog_state()` ya no crea un `QGraphicsDropShadowEffect`; guarda el color y `paintEvent()` dibuja el resplandor con trazos redondeados dentro del margen de la ventana. Afecta a todos los diálogos que usan `set_dialog_state` con color.
- **`frontend/dialogs/updater_dialog.py`:** `_refresh_presentation()` invalida el contenedor al cambiar de estado.
- **`frontend/navigation/sidebar_component.py`:** la tarjeta de actualización pierde la caja con el icono verde; el título y el botón de cerrar comparten fila. Se quita el import `BrandColors`, que ya no se usa.

### Pruebas

- **`test_update_dialog_layout.py`:** nueva prueba que verifica que el contenedor no tiene `graphicsEffect` tras llegar al estado completo.

## Archivos afectados

- `frontend/dialogs/base_dialog.py`
- `frontend/dialogs/updater_dialog.py`
- `frontend/navigation/sidebar_component.py`
- `resources/tests/test_update_dialog_layout.py`

## Verificación

- Render offscreen del diálogo en estado "descargando": resplandor verde visible y sin solapamientos.
- Auditores y pruebas de sidebar y diálogo en verde (31 aprobadas).
- Se rebasó sobre la migración a iconos de Lucide (paso 18); el icono del botón "Actualizar ahora" usa ahora `cloud-download.svg`.

## Limitaciones conocidas

- El defecto de repintado solo ocurre en Windows y no se pudo reproducir en el entorno de pruebas (Linux, offscreen); la causa es una hipótesis razonada. Verificar con una actualización real.
- Si la tarjeta del sidebar también aparece solo al pasar el cursor, el origen sería otro (no tiene efectos gráficos) y habría que investigarlo aparte.
- El icono del botón "Actualizar ahora" y el del botón colapsado se mantienen.
