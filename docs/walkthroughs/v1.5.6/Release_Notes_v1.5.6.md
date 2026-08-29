# Release Notes - MiniKick Version 1.5.6

**28 de Agosto, 2026**

## Detección Proactiva de Archivos Multimedia Faltantes en Puntos y Recompensas

> [!NOTE]
> MiniKick v1.5.6 introduce un sistema de validación proactiva y alerta visual para el módulo de recompensas de canal y triggers interactivos, eliminando fallos silenciosos en OBS Studio y notificando al streamer en tiempo real ante archivos movidos o eliminados.

---

### Novedades (1)

- **[FEATURE] [REWARDS] Detección y Marcado Visual de Archivos Multimedia Faltantes:** Identificación en tiempo real de archivos inexistentes o movidos en la tabla de recompensas vinculadas, con iconos de alerta (`alert-triangle.svg`), texto en color rojo (`COLOR_RED`), tooltips descriptivos, indicador de advertencia en el encabezado de la tarjeta y notificaciones Toast explicativas al streamer tanto en previsualizaciones manuales como en canjes de espectadores en vivo (`WT-1.5.6_01`).

---

### Mejoras (3)

- **[IMPROVEMENT] [REWARDS] Validación Temprana en Capa de Negocio:** Incorporación de `RewardsService.is_file_valid` para comprobar en tiempo constante $\mathcal{O}(1)$ la existencia física del archivo antes de enviar órdenes de renderizado al servidor overlay (`WT-1.5.6_01`).
- **[IMPROVEMENT] [UI/UX] Validación Estricta en el Asistente de Recompensas:** Marcado automático con estilo de error en el campo de archivo al editar recompensas huérfanas y bloqueo preventivo del botón de guardado si el archivo no existe en disco (`WT-1.5.6_01`).
- **[IMPROVEMENT] [I18N] Cobertura de Cero Texto Hardcodeado:** Incorporación de todas las etiquetas de advertencia, textos de estado y mensajes de log en los diccionarios `locales/es.json` y `locales/en.json` (`WT-1.5.6_01`).

---

### Correcciones (1)

- **[FIX] [OVERLAYS] Eliminación de Fallos Silenciosos en OBS:** Corrección de eventos de canje y previsualizaciones que fallaban silenciosamente con errores HTTP 404 en el overlay sin notificar la causa (`WT-1.5.6_01`).

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.6 preserva íntegramente la base de datos, configuraciones personalizadas y modelos de voz instalados en versiones previas.
