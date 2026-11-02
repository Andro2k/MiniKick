---
name: minikick-crash-investigator
description: >-
  Use this skill whenever investigating, diagnosing, or fixing a bug, crash log (.log),
  fatal exception, unhandled error, or reported issue in MiniKick, adhering strictly
  to the mandatory crash history protocol in docs/historial_crashes_y_errores.md.
---

# MiniKick Crash & Incident Investigator

Esta skill define el procedimiento obligatorio para el diagnóstico, resolución y registro de incidencias, excepciones y archivos de crash (`.log`) en MiniKick, garantizando trazabilidad y eliminando retrabajos innecesarios.

## 1. Visión General del Flujo

```mermaid
flowchart TD
    A[Reporte de Error / Crash Log / Excepción] --> B[Paso 1: Consulta O(1) en docs/historial_crashes_y_errores.md]
    B --> C{¿El error ya está catalogado como Solventado?}
    C -->|Sí| D[Notificar de inmediato al usuario citando INC-XXX, archivos, líneas y versión/WT]
    C -->|No| E[Paso 2: Diagnóstico de Causa Raíz sin modificaciones a ciegas]
    E --> F[Paso 3: Implementación de la solución arquitectónica limpia]
    F --> G[Paso 4: Validación con pruebas automatizadas]
    G --> H[Paso 5: Registro obligatorio de nuevo INC-XXX en docs/historial_crashes_y_errores.md]
```

---

## 2. Paso 1: Consulta Inicial $\mathcal{O}(1)$ en el Historial Maestro

Antes de tocar código o investigar la base de código a ciegas, **ES MANDATORIO** consultar el archivo maestro:
`docs/historial_crashes_y_errores.md`

1. Buscar por la firma de la excepción (ej. `TypeError: ToastManager.show_toast()`), el módulo implicado o el mensaje de error.
2. Si el fallo ya está catalogado como `✅ Solventado`:
   - Detener la investigación inmediatamente.
   - Informar al usuario citando el identificador del incidente (ej. `INC-018`), los archivos y líneas modificadas, y la versión/walkthrough donde fue resuelto.

---

## 3. Paso 2: Diagnóstico de Nueva Incidencia

Si el error no está en el historial o es una anomalía pendiente:
1. **Analizar el Stacktrace y Contexto**: Identificar el hilo de origen (GUI thread vs QThread/Worker), la excepción exacta y los parámetros involucrados.
2. **Consultar logs**: Revisar `resources/logs/` o el archivo `.log` proporcionado por el usuario sin alterar el sistema de telemetría.
3. **Reproducción o Verificación**: Localizar la línea exacta del fallo sin aplicar supuestos.

---

## 4. Paso 3: Implementación de la Corrección

Aplicar la solución respetando los principios del proyecto:
* **Separación de Responsabilidades (SoR)**: No colocar lógica de negocio en handlers de UI ni viceversa.
* **Make Errors Useful**: Capturar excepciones específicas (`KeyError`, `Timeout`, `ConnectionResetError`) en lugar de `except Exception: pass` genéricos. Registrar contexto útil sin exponer credenciales.
* **Manejo de Concurrencia**: Asegurar que hilos en segundo plano (`QThread`) no se destruyan prematuramente y que las señales desconectadas no emitan estados obsoletos.
* **Validación**: Ejecutar o crear una prueba en `resources/tests/` que reproduzca el caso y prevenga regresiones futuras.

---

## 5. Paso 4: Registro Obligatorio del Incidente (`INC-XXX`)

Una vez validada la solución, es **ESTRICTAMENTE OBLIGATORIO** actualizar `docs/historial_crashes_y_errores.md`:

1. **Determinar el siguiente ID:** Localizar el último `INC-XXX` en la tabla de índice (ej. `INC-027`).
2. **Actualizar el Índice Rápido:** Añadir una fila a la tabla `## 📋 Índice Rápido de Incidentes`:
   ```markdown
   | **INC-XXX** | Resumen conciso del error | Archivo log o reporte origen | Versión afectada | `✅ Solventado` | Archivos modificados | Versión / WT Fix |
   ```
3. **Añadir el Detalle Técnico:** Al final de la sección `## 🔍 Detalle Técnico por Incidente`, agregar la ficha completa:
   ```markdown
   ---

   ### INC-XXX: [Título Descriptivo del Error]

   * **Estado**: `✅ Solventado`
   * **Severidad**: **CRÍTICA** / **ALTA** / **MEDIA**
   * **Reportes Asociados**: Archivo .log o descripción del reporte
   * **Fecha y Versión del Fallo**: YYYY-MM-DD en MiniKick `vX.Y.Z`
   * **Traza de la Excepción**:
     ```text
     [Traceback relevante aquí]
     ```
   * **Causa Raíz**: Explicación técnica de por qué ocurrió el fallo.
   * **Archivos y Módulos Modificados**: Lista de rutas relativas y líneas modificadas.
   * **Solución Implementada**: Explicación de la refactorización arquitectónica aplicada.
   * **Pruebas y Verificación**: Pruebas automáticas asociadas (`resources/tests/...`).
   ```
