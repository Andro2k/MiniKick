# Walkthrough - WT-1.5.8_23: Corrección de Escalado y Transición al Paso 2 en Diálogos Asistentes (Wizards)

## Resumen de Cambios

Se resolvió de forma integral y definitiva la anomalía en el asistente de temporizadores ([`TimerConfigWizard`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/timer_dialog.py)) y demás modales derivados de [`ModernWizardPanel`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py), donde al tener configurado en Ajustes un tamaño de fuente mayor a 13px (14px Grande o 16px Extra Grande), el Paso 2 no se renderizaba o quedaba bloqueado.

El origen del problema residía en que a mayor tamaño de fuente, la altura agregada de controles, tarjetas y textos superaba la altura vertical física útil de la pantalla (especialmente con factores de escala de Windows de 125%/150%), provocando colisiones en `setGeometry` / `MINMAXINFO` de Windows y congelando el layout del `QStackedWidget`.

## Archivos Modificados

1. **[`frontend/dialogs/base_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py)**:
   - **Envoltorio Responsivo `QScrollArea` (`scroll_content`)**: Se envolvió el `QStackedWidget` central de `ModernWizardPanel` en un `QScrollArea` sin bordes con `setWidgetResizable(True)`. Si el contenido excede el espacio vertical por fuentes grandes (14px/16px), se habilita un scroll suave manteniendo el encabezado (`Paso X/Y`, barra de progreso y título) y los botones inferiores de acción siempre visibles y anclados.
   - **Restricción de Pantalla (`_apply_screen_constraints`)**: Se implementó el cálculo dinámico de la altura máxima permisible respecto a `screen.availableGeometry()` (máximo 90% de la pantalla útil, respetando la barra de tareas de Windows).
   - **Centrado Seguro**: En `ModernFramelessShell.showEvent()`, se asegura que las coordenadas de posición del diálogo nunca tomen valores negativos ni se salgan del área visible.
   - **Manejo Defensivo y Logging**: Captura y registro de excepciones con `logger.exception()` en `_go_next()`, `_go_back()` y `_update_step_ui()`.

2. **[`frontend/dialogs/timer_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/timer_dialog.py)**:
   - **Desacoplamiento de jerarquía en `CategorySearchComboBox`**: Se asignó `parent=None` para evitar que el buscador reclame como padre directo el diálogo modal superior cuando se encuentra dentro del layout de la tarjeta de filtros.
   - **Política de tamaño en `tab_filters`**: Se configuró `QSizePolicy.Expanding` en ambas dimensiones.
   - **Habilitación Segura de Botones**: `_update_btn_next_state()` valida los requisitos de respuesta en el Paso 0 y mantiene habilitado el botón "Guardar" en el Paso 2.

3. **[`resources/tests/unit/ui/test_dialog_font_scaling.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_dialog_font_scaling.py)** *(Nuevo)*:
   - Suite completa de 16 pruebas parametrizadas para validar navegación, renderizado y estados en los 4 tamaños de fuente soportados (**11px, 13px, 14px y 16px**) en `TimerConfigWizard`, `CommandConfigWizard` y `RewardsConfigWizard`.

4. **[`resources/tests/unit/ui/test_dialogs.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_dialogs.py)**:
   - Añadida prueba unitaria `test_timer_config_wizard_step_transition` para verificar el flujo paso 1 -> paso 2 -> paso 1.

## Verificación

- **Pruebas Automatizadas**:
  ```powershell
  uv run pytest resources/tests/unit/ui/test_dialogs.py resources/tests/unit/ui/test_dialog_font_scaling.py
  ```
  **Resultado**: 24 pruebas aprobadas (100% de éxito en 7.88s).
