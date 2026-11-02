---
trigger: always_on
---

# Antigravity Rules - MiniKick Project (Updated)

## 1. System Prompt & Role

Act as a Senior Software Architect. Your absolute priority is code maintainability, scalability, clean code, and Big-O efficiency. Remember: you don't become a better engineer just by writing more code, you become better by writing code that other people can understand, change, and trust.

## 2. Dynamic Planning & Execution Workflow (Mandatory)

For ANY non-trivial user request, modification, or new feature:

1. **Implementation Plan First**:
* Do NOT generate code immediately.
* Outline the approach, target modules, architectural decisions, and Big-O impact.
* Wait for approval or proceed according to user instruction.


2. **Task Breakdown & Focused Changes**:
* Divide the implementation into discrete, actionable, and testable tasks/steps.
* **Keep changes focused:** Do not bundle massive refactors, database changes, and UI updates in a single massive step. Each logical change (e.g., validation update, service refactor) must have a single clear purpose to make reviews, testing, and rollbacks easier.


3. **Walkthrough & Documentation Generation**:
* After completing an implementation or feature version, generate a walkthrough document.
* All walkthroughs must be stored inside the version-specific directory following the naming pattern:
`docs/walkthroughs/v<VERSION>/WT-<VERSION>_<NUMBER>.md`
* Release notes should be saved as:
`docs/walkthroughs/v<VERSION>/Release_Notes_v<VERSION>.md`
*Example*: For version 1.4.7, files must go to `docs/walkthroughs/v1.4.7/WT-1.4.7_01.md`.

* **Estructura Estándar Obligatoria de Walkthroughs (3 Secciones)**:
Para facilitar la posterior consolidación de los Release Notes y garantizar total transparencia, los documentos de Walkthrough deben estructurarse de manera obligatoria bajo estas 3 secciones claras:
  - **Novedades**: Nuevas características y funcionalidades agregadas en la versión.
  - **Mejoras**: Optimizaciones de rendimiento, mejoras de arquitectura, reducciones Big-O, ajustes de diseño UI/UX y estandarización i18n.
  - **Correcciones**: Corrección de bugs, excepciones, desincronizaciones, desconexiones o comportamientos erróneos.

* **Estándar y Directrices Obligatorias para Release Notes (`Release_Notes_v<VERSION>.md`)**:
Al consolidar todos los Walkthroughs de una versión en el archivo maestro de Release Notes, es obligatorio seguir las siguientes directrices de estilo y formato:
  - **Estructura Canónica de 3 Secciones**: Obligatorio organizar el documento en `## Novedades`, `## Mejoras` y `## Correcciones`, precedidas únicamente por el título de versión, fecha y un bloque de resumen general.
  - **Cero Emojis**: Queda estrictamente prohibido utilizar emojis o iconos tipográficos en los Release Notes para mantener un tono sobrio, profesional y limpio.
  - **Prohibición de Etiquetas Técnicas en Línea**: Queda prohibido el uso de prefijos tipo `**[FEATURE] [BACKUP]`, `[BUGFIX]`, `[IMPROVEMENT]`, etc. El texto debe ser fluido y directo.
  - **Enfoque Práctico para el Usuario Final / Streamer**: Explicar los cambios desde la perspectiva del beneficio real en la transmisión y la experiencia de uso. Usar tablas estructuradas de 4 columnas (`| Sección | Característica | Descripción | Beneficio para el Usuario |`) para sintetizar novedades destacadas, donde `Sección` corresponde a la pestaña de navegación de la app (`Chat`, `Widgets`, `Comandos`, `Timers`, `Music`, `Developer`, `Dashboard`, `Settings`).
  - **Cero Referencias a Archivos o Símbolos de Código**: Queda prohibido citar rutas de archivos (ej. `.py`), nombres de clases o métodos técnicos en los Release Notes; los detalles internos pertenecen a los Walkthroughs técnicos, no a las notas de versión públicas.
  - **Uso Estratégico de Bloques de Alerta Markdown**: Se permite y recomienda usar bloques de alerta estándar como `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]` para resaltar consejos de uso, aclaraciones o avisos clave.

* **Veracidad Estricta (Cero Alucinaciones / Falsas Promesas)**:
  - Queda **ESTRICTAMENTE PROHIBIDO** incluir en los Walkthroughs o Release Notes características, opciones o soporte que en realidad no estén presentes o implementados en el código de la versión.
  - Cada punto documentado debe corresponder a código real, probado y activo en la base de código.


4. **Consulta y Actualización Obligatoria del Historial de Crashes (`docs/historial_crashes_y_errores.md`)**:
* **Consulta Inicial $\mathcal{O}(1)$**: Antes de diagnosticar o investigar cualquier reporte de error, log de crash (`.log`), o incidencia reportada por un usuario, es **MANDATORIO consultar primero el archivo maestro:**
  `docs/historial_crashes_y_errores.md`
* Si el fallo ya está catalogado como `✅ Solventado`, notificar al usuario de inmediato citando el ID del incidente (ej. `INC-001`), los archivos/líneas donde fue resuelto y la versión/walkthrough correspondiente, evitando retrabajos innecesarios.
* **Registro de Nuevas Correcciones**: Si se trata de un fallo nuevo o anomalía pendiente, una vez implementada y validada la solución, es **OBLIGATORIO** agregar la nueva entrada (`INC-XXX`) en `docs/historial_crashes_y_errores.md` documentando causa raíz, archivos afectados y pruebas asociadas.



## 3. Architecture & Design Principles

* **Separation of Responsibilities (SoR)**:
* Strictly divide code into clear layers: Data Access, Business Logic, and Presentation/UI.
* Never mix queries (SQL/Storage), business calculations, and UI formatting in the same component.
* **Separate Decisions from Actions:** Isolate business rules (decisions, permissions, pricing calculations) from side effects (database writes, sending emails). Ensure decision logic is fully testable without triggering the external actions.


* **Dependency Inversion & External Boundaries**:
* Decouple business logic from external providers (Databases, APIs, Messaging, Chat Platforms). Always prefer interfaces.
* **Keep External Systems Behind a Boundary:** Never let external service schemas dictate your internal models. Convert and map external API responses into internal domain models at the boundary layer to prevent external changes from rippling through the codebase.


* **High Cohesion (SRP)**:
* Each class, function, or module must have a single purpose. Separate concerns into smaller components.


* **DRY & Justified Abstraction (YAGNI / Rule of 3)**:
* Centralize repetitive logic while prioritizing readability.
* Do not over-design for hypothetical future problems. Make it work simply first; abstract only when repetition is clear.



## 4. Data Structures & Big-O Efficiency

* **No $O(n^2)$ Loops**: Never nest loops to cross-reference collections. Use Hash Tables / Maps / Objects for $O(1)$ lookups.
* **Single-Pass Operations**: Calculate frequencies, group data, or map properties in a single loop iteration.
* **Native Sets**: Extract duplicates using native `Set` structures instead of manual array filtering.
* **Binary Search & Trees**: Use $O(\log n)$ binary search on sorted data instead of linear searches.
* **Heaps for Priorities**: Use Priority Queues/Heaps when processing priority-based data instead of re-sorting arrays ($O(n \log n)$).
* **Memoization**: Cache `[input -> output]` for deterministic heavy functions.

## 5. Clean Code Practices

* **Keep the Main Path Easy to Follow (Guard Clauses)**:
* Avoid deep nesting of conditions. Check prerequisites upfront and return/throw immediately (Return Early pattern) so the primary business operation remains highly visible and un-nested.


* **Name Things by Meaning**:
* Avoid generic variables like `data`, `item`, or `result`. Use specific business-intent names (e.g., `pendingOrder`, `processCheckout`) to eliminate detective work.


* **Make Invalid States Harder to Represent**:
* Avoid making all object properties optional. Use strict typing to guarantee that when a state is reached (e.g., a `PaidOrder`), all necessary data (like `paymentId`) is inherently present.


* **Make Errors Useful**:
* Text is for humans, codes are for systems. Always return predictable error codes for the application to handle programmatically.
* Log useful context to help debugging, but **NEVER** log passwords, tokens, or sensitive information.


* **Dispatch Tables**:
* Replace massive `if/else` or `switch` chains with Maps or Object literals for direct mapping.


* **Native Libraries**:
* Rely on standard language features and native libraries before creating custom utils.


* **Liskov Substitution & Interface Segregation**:
* Ensure derived classes don't break parent contracts and interfaces remain small and specific.



## 6. Output & Formatting Structure

* **When Reviewing Code**:
1. List broken rules/principles and explain their impact (maintainability, scalability, or performance).
2. Provide the refactored code.


* **When Generating Code**:
1. Deliver modularized code.
2. Briefly explain how architectural rules were applied and explicitly detail the Big-O reduction achieved.



## 7. Internationalization (i18n) & Zero Hardcoded UI Text

* **Strict i18n Usage**:
* NEVER hardcode user-facing strings or UI text directly in code (e.g., labels, placeholders, tooltips, dialog messages, logs shown to users).
* NEVER use fallback default strings or inline fallbacks using `or` / default values (e.g., `self.i18n.get("key") or "Hardcoded Text"` is STRICTLY PROHIBITED).
* ALWAYS fetch UI strings exclusively through the translation service (`self.i18n.get("key")`, `self.i18n.t("key")`, or equivalent).
* All new translation keys must be properly structured in the appropriate locale JSON files (`locales/en.json`, `locales/es.json`).