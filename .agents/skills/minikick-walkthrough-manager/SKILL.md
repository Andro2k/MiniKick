---
name: minikick-walkthrough-manager
description: >-
  Use this skill whenever generating technical walkthroughs (WT-X.Y.Z_NN.md)
  or compiling user-facing Release Notes (Release_Notes_vX.Y.Z.md) in MiniKick,
  enforcing strict structure, zero emojis, and zero code leaks.
---

# MiniKick Walkthrough & Release Notes Manager

Esta skill estandariza la creación de documentación técnica de implementación (Walkthroughs) y la consolidación de Notas de Versión públicas (Release Notes) en MiniKick, asegurando coherencia y cumplimiento estricto de las directrices del proyecto.

## 1. Convenciones de Nomenclatura y Rutas

Toda la documentación vive dentro de `docs/walkthroughs/v<VERSION>/`:

* **Walkthroughs Técnicos**:
  `docs/walkthroughs/v<VERSION>/WT-<VERSION>_<NUMERO>.md`  
  *Ejemplo:* `docs/walkthroughs/v1.6.5/WT-1.6.5_03.md` (número correlativo con padding de 2 dígitos).

* **Notas de Versión (Release Notes)**:
  `docs/walkthroughs/v<VERSION>/Release_Notes_v<VERSION>.md`  
  *Ejemplo:* `docs/walkthroughs/v1.6.5/Release_Notes_v1.6.5.md`.

---

## 2. Estructura Estándar para Walkthroughs (`WT-<VER>_<NUM>.md`)

Cada walkthrough documenta los cambios técnicos realizados y **debe contener obligatoriamente estas 3 secciones**:

```markdown
# Walkthrough Técnico — MiniKick vX.Y.Z (Paso NN)

Resumen técnico conciso de los cambios implementados y módulos afectados.

---

## Novedades
Nuevas características, componentes o endpoints agregados en esta iteración.

## Mejoras
Optimizaciones de rendimiento, reducciones Big-O, refactors arquitectónicos, ajustes de UI/UX y estandarización i18n.

## Correcciones
Bugs solventados, manejo de excepciones corregido, fallos de sincronización o reconexión resueltos.
```

---

## 3. Directrices Obligatorias para Release Notes (`Release_Notes_v<VER>.md`)

Al compilar o actualizar las notas de versión maestras a partir de los walkthroughs:

### Reglas Inquebrantables
1. **Estructura Canónica de 3 Secciones**:
   Organizar en:
   - Título de versión y fecha de publicación.
   - Párrafo de resumen introductorio orientado a streamers.
   - Separador `---`.
   - `## Novedades`
   - `## Mejoras`
   - `## Correcciones`
2. **Cero Emojis**: Estrictamente prohibido usar emojis o iconos tipográficos en títulos, tablas o listas.
3. **Prohibición de Etiquetas Técnicas**: No utilizar prefijos como `[FEATURE]`, `[BUGFIX]`, `[IMPROVEMENT]`, `[BACKEND]`.
4. **Cero Fuga de Código**: Queda prohibido citar nombres de archivos (`.py`), clases internas, métodos o variables técnicas. Explicar el cambio desde el impacto visible para el usuario.
5. **Tabla de 4 Columnas para Novedades**:
   En `## Novedades`, resumir las funciones clave con esta tabla:
   ```markdown
   | Sección | Característica | Descripción | Beneficio para el Usuario |
   |---|---|---|---|
   | [Pestaña] | [Nombre] | [Qué hace de forma comprensible] | [Por qué le sirve al streamer] |
   ```
   *Valores válidos para `Sección`:* `Chat`, `Widgets`, `Comandos`, `Timers`, `Music`, `Developer`, `Dashboard`, `Settings`.
6. **Veracidad Estricta**: No incluir características que no estén presentes o probadas en el código real de la versión.
7. **Alertas Markdown Permitidas**: Se pueden emplear bloques `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]` para destacar avisos relevantes.
