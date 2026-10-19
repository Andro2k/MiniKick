# Walkthrough Técnico — MiniKick v1.6.5 (Paso 12)

Se normalizaron los nombres de las herramientas de auditoría según el alcance y la responsabilidad, se conservaron los comandos antiguos y se documentó qué analiza cada herramienta.

---

## Novedades

- Se añadieron nombres canónicos con prefijos `frontend_` y `project_` y un índice de cobertura por auditoría.
- Los nombres anteriores siguen disponibles como puntos de compatibilidad para comandos e importaciones existentes.

## Mejoras

- La suite de calidad invoca los nombres canónicos y resuelve primero la ruta directa para evitar seleccionar por accidente otra herramienta homónima.
- El índice explica el alcance de backend/frontend y documenta las opciones que eliminan archivos.
- Los detectores de código muerto y parámetros no usados se mantienen separados: analizan estructuras distintas y producen diagnósticos diferentes. La suite maestra sigue ofreciendo una ejecución consolidada.

## Correcciones

- Se actualizaron las referencias activas de la suite, la skill de calidad, README y pruebas a los nombres canónicos.
- Los análisis de traducciones e iconos excluyen ahora el archivo canónico de la propia herramienta, igual que el alias anterior.
